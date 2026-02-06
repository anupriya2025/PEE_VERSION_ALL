import os
import cv2
import av
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from queue import Queue, PriorityQueue
import re
import shutil
from core.database import EventDatabase
from share_queue import pid_last_seen, inactive_ids_record


class TrackVideoManager:
    """
    Manages video creation for individual track IDs with continuous video updates.
    Features:
    - Minimum/maximum video duration enforcement
    - Continuous video updates for returning tracks
    - Graceful shutdown with video finalization
    - No video corruption during writes
    - Proper duration tracking to capture full track lifetime
    """

    def __init__(self, base_folder="", output_folder="track_videos",
                 fps=10, max_age_hours=24, cleanup_interval=3600,
                 scan_interval=2, min_frames_for_video=2,
                 frame_cleanup_interval=500, frame_retention_minutes=5,
                 min_video_duration=2, max_video_duration=120,
                 video_inactivity_timeout=5):
        """
        Initialize the TrackVideoManager.

        Args:
            base_folder (str): Root folder containing date/camera/images structure
            output_folder (str): Base folder to save generated videos
            fps (int): Frames per second for output videos
            max_age_hours (int): Maximum age of frames before cleanup (hours)
            cleanup_interval (int): Interval between cleanup runs (seconds)
            scan_interval (int): Interval to scan for new files (seconds)
            min_frames_for_video (int): Minimum frames required to create video (default: 20)
            frame_cleanup_interval (int): Interval to clean old frame files (seconds)
            frame_retention_minutes (int): Keep frames for this many minutes after processing
            min_video_duration (int): Minimum video duration in seconds (default: 2)
            max_video_duration (int): Maximum video duration in seconds (default: 120/2min)
            video_inactivity_timeout (int): Seconds of inactivity before finalizing video (default: 10)
        """
        self.base_folder = Path(base_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.obj_db = EventDatabase()
        self.fps = fps
        self.max_age_hours = max_age_hours
        self.cleanup_interval = cleanup_interval
        self.scan_interval = scan_interval
        self.min_frames_for_video = min_frames_for_video
        self.frame_cleanup_interval = frame_cleanup_interval
        self.frame_retention_minutes = frame_retention_minutes
        self.keep_video_ids_record = []

        # Video duration constraints
        self.min_video_duration = min_video_duration
        self.max_video_duration = max_video_duration
        self.max_frames = max_video_duration * fps  # Maximum frames per video
        self.video_inactivity_timeout = video_inactivity_timeout

        # Track data structures
        self.track_frames = defaultdict(list)  # tid -> [(timestamp, image_path, bbox, camera_name)]
        self.track_camera = {}  # tid -> camera_name
        self.video_queue = Queue()  # Changed to simple Queue for frame processing
        self.processing_tracks = set()
        self.processed_files = set()

        # Active video tracking
        self.active_videos = {}  # tid -> {'container': av.Container, 'stream': av.Stream, 'path': Path, 'start_time': datetime, 'last_frame_time': datetime, 'frame_count': int, 'temp_path': Path}
        self.video_locks = {}  # tid -> threading.Lock for individual video access

        # Frame cleanup tracking
        self.processed_frames = {}
        self.frames_to_keep = set()

        # Track last seen times for video triggering
        self.track_last_seen = {}
        self.first_seen_time = {}

        # Shutdown handling
        self.shutdown_event = threading.Event()
        self.finalization_complete = threading.Event()

        # Thread control
        self.running = True
        self.lock = threading.Lock()

        # Start daemon threads
        self.monitor_thread = threading.Thread(target=self._folder_monitor_worker, daemon=True)
        self.frame_writer_thread = threading.Thread(target=self._frame_writer_worker, daemon=True)
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.finalization_thread = threading.Thread(target=self._video_finalization_worker, daemon=True)
        # self.frame_cleanup_thread = threading.Thread(target=self._frame_cleanup_worker, daemon=True)

        self.monitor_thread.start()
        self.frame_writer_thread.start()
        self.cleanup_thread.start()
        self.finalization_thread.start()
        # self.frame_cleanup_thread.start()

        print(f"TrackVideoManager initialized. Monitoring: {self.base_folder}")
        print(f"Output folder: {self.output_folder}")
        print(f"Video constraints: Min={min_frames_for_video} frames, Max={self.max_frames} frames")
        print(f"Inactivity timeout: {video_inactivity_timeout}s")
        print("All daemon threads started successfully")

    def get_video_output_path(self, camera_name, tid, timestamp):
        """Generate structured output path for video."""
        date_folder = timestamp.strftime("%d-%m-%Y")
        video_dir = self.output_folder / date_folder / camera_name
        video_dir.mkdir(parents=True, exist_ok=True)

        video_filename = f"{camera_name}_{tid}.ts"
        temp_filename = f"{camera_name}_{tid}_temp.ts"

        full_path = video_dir / video_filename
        temp_path = video_dir / temp_filename
        relative_path = Path(date_folder) / camera_name / video_filename

        return full_path, temp_path, relative_path

    def track_id_manager(self, track_id, max_size=300):
        """
        Store first-seen time of track IDs.
        Keeps only the latest max_size entries.
        Oldest ones are automatically removed.
        """
        now = datetime.now()
        # Store only if new track_id
        if track_id not in self.first_seen_time:
            self.first_seen_time[track_id] = now
            print(f"✨ New track detected: {track_id} at {now.strftime('%H:%M:%S')}")

            # If size exceeds limit → remove oldest ones
            if len(self.first_seen_time) > max_size:
                # sort items by time (oldest first)
                oldest = sorted(self.first_seen_time.items(), key=lambda x: x[1])
                # remove only 1 oldest (you can remove more if you want)
                oldest_key = oldest[0][0]
                del self.first_seen_time[oldest_key]

        return self.first_seen_time

    def parse_toon_file(self, toon_path):
        """Parse a .toon file and extract track information."""
        try:
            with open(toon_path, 'r') as f:
                lines = f.readlines()

            if len(lines) < 2:
                return None

            header = lines[0].strip()
            match = re.match(r'@f:(.+?)\|(.+?)\|(.+?)\|(.+?)\|n:(\d+)', header)
            if not match:
                return None

            folder, timestamp_str, image_file, resolution, n_tracks = match.groups()
            timestamp = datetime.fromisoformat(timestamp_str)
            width, height = map(int, resolution.split('x'))
            camera_name = folder

            tracks = []
            for line in lines[2:]:
                line = line.strip()
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) >= 4:
                    tid = parts[0]
                    bbox = list(map(int, parts[1].split(',')))
                    tracks.append({
                        'tid': tid,
                        'bbox': bbox,
                        'time': parts[2],
                        'conf': parts[3]
                    })

            return {
                'folder': folder,
                'timestamp': timestamp,
                'image_file': image_file,
                'resolution': (width, height),
                'tracks': tracks,
                'camera_name': camera_name
            }
        except Exception as e:
            # print(f"Error parsing {toon_path}: {e}")
            return None

    def add_frame(self, toon_path):
        """Add a frame from a toon file to the processing queue."""
        data = self.parse_toon_file(toon_path)
        if not data:
            return

        toon_path = Path(toon_path)
        image_path = toon_path.parent / data['image_file']

        if not image_path.exists():
            return

        image_path_str = str(image_path)
        current_time = datetime.now()

        with self.lock:
            for track in data['tracks']:
                tid = track['tid']
                self.track_camera[tid] = data['camera_name']

                frame_data = {
                    'timestamp': data['timestamp'],
                    'image_path': image_path_str,
                    'bbox': track['bbox'],
                    'camera_name': data['camera_name']
                }

                # Add to track frames
                self.track_frames[tid].append(frame_data)
                self.track_last_seen[tid] = current_time
                self.track_id_manager(tid)

                # Queue frame for immediate processing
                self.video_queue.put((tid, frame_data))

                # Debug: Log frame accumulation
                frame_count = len(self.track_frames[tid])
                if frame_count % 10 == 0:
                    time_active = (current_time - self.first_seen_time[tid]).total_seconds()
                    print(f"📊 Track {tid}: {frame_count} frames collected ({time_active:.1f}s active)")

            self.frames_to_keep.add(image_path_str)

    def _get_video_lock(self, tid):
        """Get or create a lock for a specific track video."""
        with self.lock:
            if tid not in self.video_locks:
                self.video_locks[tid] = threading.Lock()
            return self.video_locks[tid]

    def _initialize_video_writer(self, tid, camera_name, width, height, output_path, temp_path):
        """Initialize a new video writer for a track."""
        try:
            # Write to temporary file first
            container = av.open(str(temp_path), mode='w', format='mpegts')
            stream = container.add_stream('h264', rate=self.fps)
            stream.width = width
            stream.height = height
            stream.pix_fmt = 'yuv420p'
            stream.options = {
                'preset': 'medium',
                'crf': '23',
            }

            video_lock = self._get_video_lock(tid)
            with video_lock:
                self.active_videos[tid] = {
                    'container': container,
                    'stream': stream,
                    'path': output_path,
                    'temp_path': temp_path,
                    'start_time': datetime.now(),
                    'last_frame_time': datetime.now(),
                    'frame_count': 0,
                    'width': width,
                    'height': height,
                    'camera_name': camera_name
                }

            print(f"📹 Initialized video writer for track {tid}")
            return True
        except Exception as e:
            print(f"❌ Error initializing video writer for track {tid}: {e}")
            return False

    def _write_frame_to_video(self, tid, frame_data):
        """Write a single frame to an active video."""
        video_lock = self._get_video_lock(tid)

        with video_lock:
            if tid not in self.active_videos:
                # Need to initialize video first
                return False

            video_info = self.active_videos[tid]

            # Check if max frames reached
            if video_info['frame_count'] >= self.max_frames:
                print(f"⏱️ Track {tid} reached max frames ({video_info['frame_count']}), will be finalized")
                return False

            try:
                img = cv2.imread(frame_data['image_path'])
                if img is None:
                    return False

                # Resize if needed
                if img.shape[1] != video_info['width'] or img.shape[0] != video_info['height']:
                    img = cv2.resize(img, (video_info['width'], video_info['height']))

                # Draw bounding box
                bbox = frame_data['bbox']
                x1, y1, x2, y2 = bbox
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Add labels
                label = f"TID: {tid}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(img, (x1, y1 - label_size[1] - 10),
                              (x1 + label_size[0], y1), (0, 255, 0), -1)
                cv2.putText(img, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

                timestamp_str = frame_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                camera_name = frame_data['camera_name']
                cv2.putText(img, f"{camera_name} | ID:{tid}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(img, timestamp_str, (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Convert and encode
                rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                video_frame = av.VideoFrame.from_ndarray(rgb_frame, format='rgb24')

                for packet in video_info['stream'].encode(video_frame):
                    video_info['container'].mux(packet)
                
                video_info['frame_count'] += 1
                video_info['last_frame_time'] = datetime.now()

                return True

            except Exception as e:
                print(f"❌ Error writing frame for track {tid}: {e}")
                return False

    def _finalize_video(self, tid, force=False):
        """Safely finalize or discard a per-track video."""
        video_lock = self._get_video_lock(tid)

        with video_lock:
            if tid not in self.active_videos:
                return None

            video_info = self.active_videos[tid]

            # Prevent double finalization
            if video_info.get("finalizing", False):
                return None
            video_info["finalizing"] = True

            current_time = datetime.now()
            frame_count = video_info.get("frame_count", 0)
            start_time = video_info.get("start_time")
            video_duration = (
                (current_time - start_time).total_seconds()
                if start_time else 0
            )

            # DISCARD SHORT / INVALID VIDEOS
            if not force and frame_count < self.min_frames_for_video:
                print(
                    f"🗑️ Discarding video for track {tid} "
                    f"(frames={frame_count}, min={self.min_frames_for_video})"
                )

                # Close container safely
                try:
                    video_info["container"].close()
                except Exception:
                    pass

                # Remove temp file
                temp_path = video_info.get("temp_path")
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except Exception:
                        pass

                # Cleanup memory
                del self.active_videos[tid]

                with self.lock:
                    self.track_frames.pop(tid, None)
                    self.track_camera.pop(tid, None)
                    self.first_seen_time.pop(tid, None)
                    self.track_last_seen.pop(tid, None)

                return None

            # FINALIZE VALID VIDEO
            try:
                # Flush encoder ONLY if frames exist
                if frame_count > 0:
                    for packet in video_info["stream"].encode():
                        video_info["container"].mux(packet)

                video_info["container"].close()

                temp_path = video_info["temp_path"]
                final_path = video_info["path"]

                if not temp_path.exists():
                    print(f"❌ Temp file missing for track {tid}")
                    del self.active_videos[tid]
                    return None

                # Move temp → final
                shutil.move(str(temp_path), str(final_path))

                relative_path = final_path.relative_to(self.output_folder)

                # Track lifetime
                if tid in self.first_seen_time:
                    track_lifetime = (
                        current_time - self.first_seen_time[tid]
                    ).total_seconds()
                else:
                    track_lifetime = video_duration

                # DB update
                self.obj_db.update_video_path(str(tid), str(relative_path))

                print(f"✅ Finalized video for track {tid}: {relative_path}")
                print(
                    f"📊 Stats: {frame_count} frames | "
                    f"{video_duration:.1f}s duration | "
                    f"track lifetime {track_lifetime:.1f}s"
                )

                # Keep record
                self.keep_video_ids_record.append(tid)
                if len(self.keep_video_ids_record) > 100:
                    self.keep_video_ids_record.pop(0)

                # Cleanup memory
                del self.active_videos[tid]

                with self.lock:
                    self.track_frames.pop(tid, None)
                    self.track_camera.pop(tid, None)
                    self.first_seen_time.pop(tid, None)
                    self.track_last_seen.pop(tid, None)

                return str(relative_path)

            except Exception as e:
                print(f"❌ Error finalizing video for track {tid}: {e}")

                try:
                    video_info["container"].close()
                except Exception:
                    pass

                self.active_videos.pop(tid, None)
                return None

    def _frame_writer_worker(self):
        """Daemon thread that continuously writes frames to active videos."""
       

        while self.running:
            try:
                # Get frame from queue (blocks until available)
                tid, frame_data = self.video_queue.get(timeout=1)

                # Check if video exists for this track
                video_lock = self._get_video_lock(tid)
                with video_lock:
                    video_exists = tid in self.active_videos

                if not video_exists:
                    # Initialize video if this is the first frame
                    with self.lock:
                        frames = self.track_frames.get(tid, [])
                    
                    if len(frames) >= 1:
                        # Get image dimensions
                        img = cv2.imread(frame_data['image_path'])
                        if img is not None:
                            height, width = img.shape[:2]
                            width = width if width % 2 == 0 else width - 1
                            height = height if height % 2 == 0 else height - 1

                            camera_name = frame_data['camera_name']
                            timestamp = frame_data['timestamp']
                            full_path, temp_path, _ = self.get_video_output_path(
                                camera_name, tid, timestamp
                            )

                            self._initialize_video_writer(
                                tid, camera_name, width, height, full_path, temp_path
                            )

                # Write frame to video
                success = self._write_frame_to_video(tid, frame_data)
                
                if not success:
                    # Video might need finalization due to max frames
                    with video_lock:
                        if tid in self.active_videos:
                            video_info = self.active_videos[tid]
                            if video_info['frame_count'] >= self.max_frames:
                                # Will be picked up by finalization worker
                                pass

            except Exception as e:
                if self.running:  # Only log if not shutting down
                    continue

    def _video_finalization_worker(self):
        """Daemon thread that checks for videos that need finalization."""
       
        while self.running or not self.shutdown_event.is_set():
            try:
                time.sleep(1)  # Check every second
                current_time = datetime.now()

                # Get list of active videos to check
                with self.lock:
                    active_tids = list(self.active_videos.keys())

                for tid in active_tids:
                    video_lock = self._get_video_lock(tid)
                    
                    should_finalize = False
                    reason = ""

                    with video_lock:
                        if tid not in self.active_videos:
                            continue

                        video_info = self.active_videos[tid]
                        frame_count = video_info['frame_count']
                        last_frame_time = video_info['last_frame_time']
                        inactive_duration = (current_time - last_frame_time).total_seconds()

                        # Check if max frames reached
                        if frame_count >= self.max_frames:
                            should_finalize = True
                            reason = f"max frames reached ({frame_count})"

                        # Check if ID is in inactive list
                        elif tid in inactive_ids_record and frame_count >= self.min_frames_for_video:
                            should_finalize = True
                            reason = f"ID marked inactive ({frame_count} frames)"

                        # Check inactivity timeout
                        elif inactive_duration >= self.video_inactivity_timeout and frame_count >= self.min_frames_for_video:
                            should_finalize = True
                            reason = f"inactive for {inactive_duration:.1f}s ({frame_count} frames)"

                    if should_finalize:
                        print(f"💤 Finalizing track {tid}: {reason}")
                        self._finalize_video(tid)

            except Exception as e:
                if self.running:
                    print(f"❌ Finalization worker error: {e}")

        self.finalization_complete.set()

    def _folder_monitor_worker(self):
        """Daemon thread worker that continuously monitors folder for new toon files."""
        print("👀 Folder monitor worker started - continuous scanning mode")

        while self.running:
            try:
                toon_files = list(self.base_folder.rglob("*.toon"))
                new_files = []

                with self.lock:
                    for toon_file in toon_files:
                        file_str = str(toon_file)
                        if file_str not in self.processed_files:
                            new_files.append(toon_file)
                            self.processed_files.add(file_str)

                if new_files:
                    print(f"📂 Found {len(new_files)} new toon file(s)")
                    for toon_file in sorted(new_files):
                        self.add_frame(toon_file)

                time.sleep(self.scan_interval)

            except Exception as e:
                print(f"❌ Folder monitor error: {e}")
                time.sleep(self.scan_interval)

    def _cleanup_old_frames(self):
        """
        Scan self.base_folder recursively and delete files older than retention_seconds.
        Uses epoch seconds for comparisons to avoid datetime/float mismatches.
        """
        retention_seconds = float(self.frame_retention_minutes) * 60.0
        now_ts = time.time()
        deleted_count = 0

        for root, dirs, files in os.walk(self.base_folder):
            for file_name in files:
                file_path = os.path.join(root, file_name)

                try:
                    created_ts = os.path.getctime(file_path)
                except (FileNotFoundError, PermissionError):
                    continue
                except Exception as e:
                    print(f"❌ Error getting ctime for {file_path}: {e}")
                    continue

                age_seconds = now_ts - created_ts
                if age_seconds > retention_seconds:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except (FileNotFoundError, PermissionError):
                        continue
                    except Exception as e:
                        print(f"❌ Failed to delete {file_path}: {e}")
        if deleted_count > 0:
            print(f"🗑️ Cleaned up {deleted_count} old frame file(s)")

    def _cleanup_worker(self):
        """Daemon thread worker for cleaning up old frames from memory."""
        print("🔧 Memory cleanup worker started")
        while self.running:
            try:
                self._cleanup_old_frames()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                print(f"❌ Memory cleanup error: {e}")

    # def _cleanup_old_data(self):
    #     """Remove old frame data and processed file references from memory."""
    #     cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
    #     removed_frames = 0
    #     removed_files = 0

    #     with self.lock:
    #         for tid in list(self.track_frames.keys()):
    #             # Skip tracks with active videos
    #             if tid in self.active_videos:
    #                 continue

    #             frames = self.track_frames[tid]
    #             original_count = len(frames)

    #             self.track_frames[tid] = [
    #                 f for f in frames if f['timestamp'] > cutoff_time
    #             ]
    #             removed_frames += original_count - len(self.track_frames[tid])

    #             if not self.track_frames[tid]:
    #                 del self.track_frames[tid]
    #                 if tid in self.track_camera:
    #                     del self.track_camera[tid]

    #         old_processed = set()
    #         for file_path in self.processed_files:
    #             try:
    #                 path = Path(file_path)
    #                 if path.exists():
    #                     mtime = datetime.fromtimestamp(path.stat().st_mtime)
    #                     if mtime < cutoff_time:
    #                         old_processed.add(file_path)
    #                 else:
    #                     old_processed.add(file_path)
    #             except:
    #                 pass

    #         for file_path in old_processed:
    #             self.processed_files.discard(file_path)
    #             removed_files += 1

    #     if removed_frames > 0 or removed_files > 0:
    #         print(f"🧹 Memory cleanup: Removed {removed_frames} old frame(s) from memory, "
    #               f"{removed_files} old file reference(s)")

    def get_stats(self):
        """Get current statistics."""
        with self.lock:
            return {
                'active_tracks': len(self.track_frames),
                'total_frames': sum(len(frames) for frames in self.track_frames.values()),
                'queued_frames': self.video_queue.qsize(),
                'processed_files': len(self.processed_files),
                'tracked_cameras': len(set(self.track_camera.values())),
                'active_videos': len(self.active_videos)
            }

    def stop(self):
        """Stop the daemon threads gracefully and finalize all active videos."""
        print("\n⏹️ Stopping TrackVideoManager...")
        print("📹 Finalizing all active videos...")

        # Signal shutdown
        self.running = False
        self.shutdown_event.set()

        # Finalize all active videos
        with self.lock:
            active_tids = list(self.active_videos.keys())

        print(f"Found {len(active_tids)} active video(s) to finalize")

        for tid in active_tids:
            try:
                print(f"Finalizing video for track {tid}...")
                self._finalize_video(tid, force=True)
            except Exception as e:
                print(f"Error finalizing video for track {tid}: {e}")

        # Wait for finalization thread to complete
        print("Waiting for finalization worker to complete...")
        self.finalization_complete.wait(timeout=30)

        # Wait for other threads
        print("Stopping worker threads...")
        self.monitor_thread.join(timeout=5)
        self.frame_writer_thread.join(timeout=5)
        self.cleanup_thread.join(timeout=5)
        self.finalization_thread.join(timeout=5)
        self.frame_cleanup_thread.join(timeout=5)

        # Final stats
        stats = self.get_stats()
        print(f"📊 Final stats: {stats}")
        print("✅ TrackVideoManager stopped successfully - No videos corrupted")


# Example usage
if __name__ == "__main__":
    # Create manager instance - threads start automatically and monitor continuously
    manager = TrackVideoManager(
        base_folder=r"E:\Zone_Intrusion_Service\frame_data_storage",
        output_folder=r"D:\ZONE_DATA\ZONE_VIDEOS",
        fps=6,
        max_age_hours=24,# now it is comment 
        cleanup_interval=1800,  # Memory cleanup every 30 minutes
        scan_interval=2,  # Check for new files every 2 seconds
        min_frames_for_video=5,  # Minimum frames to create video
        frame_cleanup_interval=60,  # Clean old frames every 1 minute
        frame_retention_minutes=10,  # Keep frames for 10 minutes after processing
        max_video_duration=120,  # Max 120 seconds (2 minutes)
        video_inactivity_timeout=5  # Finalize after 5 seconds of inactivity
    )

    print("\n👀 Continuous monitoring started. Press Ctrl+C to stop.\n")
    print(f"📹 Videos will be stored in structure: output_folder/DD-MM-YYYY/camera_name/camera_name_tid.ts")
    print(f"🗑️ Old frames will be deleted after {manager.frame_retention_minutes} minutes\n")

    # Monitor progress and display stats periodically
    try:
        while True:
            time.sleep(10)  # Print stats every 10 seconds
            stats = manager.get_stats()
            print(f"📊 Stats: Active tracks: {stats['active_tracks']}, "
                  f"Total frames: {stats['total_frames']}, "
                  f"Queue: {stats['queued_frames']}, "
                  f"Files processed: {stats['processed_files']}, "
                  f"Cameras: {stats['tracked_cameras']}, "
                  f"Active videos: {stats['active_videos']}")
    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received")
        manager.stop()