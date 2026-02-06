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
from logger import LoggerUtility
from share_queue import pid_last_seen, inactive_ids_record, post_buffer_frames


class TrackVideoManager:
    """
    Manages video creation for individual track IDs with continuous video updates.
    Features:
    - Minimum/maximum video duration enforcement
    - Continuous video updates for returning tracks
    - Graceful shutdown with video finalization
    - No video corruption during writes
    - Proper duration tracking to capture full track lifetime
    - Efficient memory management with proper cleanup
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
        obj_logger = LoggerUtility()
        self.logger = obj_logger.get_logger(__name__)
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
        
        # Video ID tracking with size limits
        self.keep_video_ids_record = []
        self.max_video_ids_record = 100
        
        # Frame reference tracking
        self.frames_ref_count = defaultdict(int)  # frame_path -> number of videos needing it
        self.track_frame_paths = defaultdict(set)  # tid -> set of frame paths used
        self.frame_to_tids = defaultdict(set)  # frame_path -> set of tids using it
        self.toon_to_tids = defaultdict(set)  # toon_path -> set of tids from it

        # Video duration constraints
        self.min_video_duration = min_video_duration
        self.max_video_duration = max_video_duration
        self.max_frames = max_video_duration * fps  # Maximum frames per video
        self.video_inactivity_timeout = video_inactivity_timeout

        # Track data structures with size limits
        self.track_frames = defaultdict(list)  # tid -> [(timestamp, image_path, bbox, camera_name)]
        self.track_camera = {}  # tid -> camera_name
        self.video_queue = Queue()  # Changed to simple Queue for frame processing
        self.processed_files = set()
        self.max_processed_files = 1000  # Limit processed files tracking

        # Active video tracking
        self.active_videos = {}  # tid -> {'container': av.Container, 'stream': av.Stream, 'path': Path, 'start_time': datetime, 'last_frame_time': datetime, 'frame_count': int, 'temp_path': Path}
        self.video_locks = {}  # tid -> threading.Lock for individual video access

        # Frame cleanup tracking (removed - using ref counting instead)
        self.frames_to_keep = set()
        self.max_frames_to_keep = 500  # Limit this set size

        # Track last seen times for video triggering
        self.track_last_seen = {}
        self.first_seen_time = {}
        self.max_first_seen_time = 300  # Limit this dict size

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
        self.frame_cleanup_thread = threading.Thread(target=self._frame_cleanup_worker, daemon=True)

        self.monitor_thread.start()
        self.frame_writer_thread.start()
        self.cleanup_thread.start()
        self.finalization_thread.start()
        self.frame_cleanup_thread.start()

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

            # If size exceeds limit → remove oldest ones
            if len(self.first_seen_time) > max_size:
                # sort items by time (oldest first)
                oldest = sorted(self.first_seen_time.items(), key=lambda x: x[1])
                # remove oldest entry
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
            self.logger.warning(f"Error parsing toon file {toon_path}: {e}")
            return None

    def add_frame(self, toon_path):
        """Add a frame from a toon file to the processing queue."""
        data = self.parse_toon_file(toon_path)
        
        if not data:
            # Delete invalid toon file
            try:
                Path(toon_path).unlink()
                self.logger.debug(f"Deleted invalid toon file: {toon_path}")
            except Exception as e:
                self.logger.warning(f"Failed to delete invalid toon file {toon_path}: {e}")
            return

        toon_path = Path(toon_path)
        image_path = toon_path.parent / data['image_file']

        if not image_path.exists():
            # Delete toon file if image doesn't exist
            try:
                toon_path.unlink()
                self.logger.debug(f"Deleted toon file with missing image: {toon_path}")
            except Exception as e:
                self.logger.warning(f"Failed to delete toon file {toon_path}: {e}")
            return

        image_path_str = str(image_path)
        toon_path_str = str(toon_path)
        current_time = datetime.now()
        queued_any = False

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
                queued_any = True
                
                # Track reference counts
                self.frames_ref_count[image_path_str] += 1
                self.track_frame_paths[tid].add(image_path_str)
                self.frame_to_tids[image_path_str].add(tid)
                self.toon_to_tids[toon_path_str].add(tid)

                # Debug: Log frame accumulation
                frame_count = len(self.track_frames[tid])
                if frame_count % 10 == 0:
                    time_active = (current_time - self.first_seen_time[tid]).total_seconds()
                    self.logger.debug(f"Track {tid}: {frame_count} frames, {time_active:.1f}s active")

            # Add to frames to keep (with size limit)
            self.frames_to_keep.add(image_path_str)
            if len(self.frames_to_keep) > self.max_frames_to_keep:
                # Remove oldest entry (convert to list, remove first, convert back)
                frames_list = list(self.frames_to_keep)
                self.frames_to_keep.remove(frames_list[0])
            
        # Delete toon file after successful processing
        if queued_any:
            try:
                toon_path.unlink()
                self.logger.debug(f"Deleted processed toon file: {toon_path}")
                with self.lock:
                    self.processed_files.discard(str(toon_path))
            except FileNotFoundError:
                pass
            except Exception as e:
                self.logger.warning(f"Failed to delete toon file {toon_path}: {e}")

    def _release_tid_resources(self, tid):
        """Release all resources owned by a finished track ID."""
        self.logger.debug(f"Releasing resources for track {tid}")

        # ---- FRAME RELEASE ----
        frame_paths = self.track_frame_paths.pop(tid, set())

        for path in frame_paths:
            # Decrement reference count
            if path in self.frames_ref_count:
                self.frames_ref_count[path] -= 1
            
            # Remove tid from frame mapping
            if path in self.frame_to_tids:
                self.frame_to_tids[path].discard(tid)

            # Delete frame if no more references
            if self.frames_ref_count.get(path, 0) <= 0:
                self.frames_ref_count.pop(path, None)
                self.frame_to_tids.pop(path, None)
                self.frames_to_keep.discard(path)

                # Safe delete frame
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        self.logger.debug(f"Deleted unreferenced frame: {path}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete frame {path}: {e}")

        # ---- TOON RELEASE ----
        for toon_path, tids in list(self.toon_to_tids.items()):
            tids.discard(tid)
            if not tids:
                self.toon_to_tids.pop(toon_path, None)
                try:
                    if os.path.exists(toon_path):
                        os.remove(toon_path)
                        self.logger.debug(f"Deleted unreferenced toon: {toon_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete toon {toon_path}: {e}")

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

            self.logger.info(f"Initialized video writer for track {tid}")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing video writer for track {tid}: {e}")
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
                return False

            try:
                img = cv2.imread(frame_data['image_path'])
                if img is None:
                    self.logger.warning(f"Failed to read image: {frame_data['image_path']}")
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
                video_info['last_frame_time'] = frame_data['timestamp']

                return True

            except Exception as e:
                self.logger.exception(f"Error writing frame for track {tid}: {e}")
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

            frame_count = video_info.get("frame_count", 0)
            start_time = video_info.get("start_time")
            last_frame_time_dt = video_info.get("last_frame_time")
            POST_BUFFER_SECONDS = 10
            
            if last_frame_time_dt is not None:
                last_seen_ts = last_frame_time_dt.timestamp()
            else:
                last_seen_ts = None
            
            camera_name = video_info.get("camera_name")
            
            # Add post-buffer frames
            if last_seen_ts is not None:
                post_frames = [
                    f for f in post_buffer_frames
                    if f["camera"] == camera_name
                    and last_seen_ts - 0.1 < f["timestamp"] <= last_seen_ts + POST_BUFFER_SECONDS
                ]
             
                for frame in post_frames:
                    try:
                        rgb_frame = cv2.cvtColor(frame["frame"], cv2.COLOR_BGR2RGB)
                        video_frame = av.VideoFrame.from_ndarray(rgb_frame, format='rgb24')

                        for packet in video_info['stream'].encode(video_frame):
                            video_info['container'].mux(packet)
                        
                        video_info['frame_count'] += 1
                        video_info['last_frame_time'] = datetime.now()
                    except Exception as e:
                        self.logger.warning(f"Error adding post-buffer frame: {e}")
            
            current_time = datetime.now()
            video_duration = (
                (current_time - start_time).total_seconds()
                if start_time else 0
            )

            video_info["finalizing"] = True
            
            # Clean old post-buffer frames
            now = time.time()
            cutoff = now - (1 * 60)
            post_buffer_frames[:] = [
                f for f in post_buffer_frames
                if f["timestamp"] >= cutoff
            ]

            # DISCARD SHORT / INVALID VIDEOS
            if not force and frame_count < self.min_frames_for_video:
                self.logger.info(f"Discarding video for track {tid}: insufficient frames ({frame_count})")
                
                # Close container safely
                try:
                    video_info["container"].close()
                except Exception as e:
                    self.logger.warning(f"Error closing container for track {tid}: {e}")

                # Remove temp file
                temp_path = video_info.get("temp_path")
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                        self.logger.debug(f"Deleted temp file: {temp_path}")
                    except Exception as e:
                        self.logger.warning(f"Failed to delete temp file {temp_path}: {e}")

                # Cleanup memory
                del self.active_videos[tid]
                self.video_locks.pop(tid, None)

                with self.lock:
                    self.track_frames.pop(tid, None)
                    self.track_camera.pop(tid, None)
                    self.track_last_seen.pop(tid, None)
                    self.first_seen_time.pop(tid, None)

                    # Release disk resources LAST
                    self._release_tid_resources(tid)
                
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
                    self.logger.error(f"Temp file not found for track {tid}: {temp_path}")
                    del self.active_videos[tid]
                    self.video_locks.pop(tid, None)
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

                self.logger.info(
                    f"Finalized video for track {tid}: {frame_count} frames, "
                    f"{video_duration:.1f}s duration, {track_lifetime:.1f}s lifetime"
                )

                # DB update
                try:
                    self.obj_db.update_video_path(str(tid), str(relative_path))
                except Exception as e:
                    self.logger.warning(f"Failed to update database for track {tid}: {e}")

                # Keep record with size limit
                self.keep_video_ids_record.append(tid)
                if len(self.keep_video_ids_record) > self.max_video_ids_record:
                    self.keep_video_ids_record.pop(0)

                # Cleanup memory
                del self.active_videos[tid]
                self.video_locks.pop(tid, None)

                with self.lock:
                    self.track_frames.pop(tid, None)
                    self.track_camera.pop(tid, None)
                    self.first_seen_time.pop(tid, None)
                    self.track_last_seen.pop(tid, None)
                    
                    # Release disk resources
                    self._release_tid_resources(tid)

                return str(relative_path)

            except Exception as e:
                self.logger.exception(f"Error finalizing video for track {tid}: {e}")

                try:
                    video_info["container"].close()
                except Exception:
                    pass

                self.active_videos.pop(tid, None)
                self.video_locks.pop(tid, None)
                return None

    def _frame_writer_worker(self):
        """Daemon thread that continuously writes frames to active videos."""
        self.logger.info("Frame writer worker started")

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
                                self.logger.info(f"Track {tid} reached max frames, will finalize")

            except Exception as e:
                if self.running:  # Only log if not shutting down
                    self.logger.warning(f"Frame writer error: {e}")
                continue

        self.logger.info("Frame writer worker stopped")

    def _video_finalization_worker(self):
        """Daemon thread that checks for videos that need finalization."""
        self.logger.info("Video finalization worker started")
        
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
                        self.logger.info(f"Finalizing video for track {tid}: {reason}")
                        self._finalize_video(tid)

            except Exception as e:
                if self.running:
                    self.logger.warning(f"Finalization worker error: {e}")

        self.finalization_complete.set()
        self.logger.info("Video finalization worker stopped")

    def _folder_monitor_worker(self):
        """Daemon thread worker that continuously monitors folder for new toon files."""
        self.logger.info("Folder monitor worker started")

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
                    
                    # Limit processed_files set size
                    if len(self.processed_files) > self.max_processed_files:
                        # Convert to list, remove oldest half, convert back
                        files_list = list(self.processed_files)
                        self.processed_files = set(files_list[len(files_list)//2:])
                        self.logger.debug(f"Trimmed processed_files from {len(files_list)} to {len(self.processed_files)}")

                if new_files:
                    self.logger.debug(f"Found {len(new_files)} new toon files")
                    for toon_file in sorted(new_files):
                        self.add_frame(toon_file)

                time.sleep(self.scan_interval)

            except Exception as e:
                self.logger.warning(f"Folder monitor error: {e}")
                time.sleep(self.scan_interval)

        self.logger.info("Folder monitor worker stopped")

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

                # Skip files that are still referenced
                if file_path in self.frames_ref_count and self.frames_ref_count[file_path] > 0:
                    continue

                try:
                    created_ts = os.path.getctime(file_path)
                except (FileNotFoundError, PermissionError):
                    continue
                except Exception as e:
                    self.logger.warning(f"Error getting ctime for {file_path}: {e}")
                    continue

                age_seconds = now_ts - created_ts
                if age_seconds > retention_seconds:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        # Also remove from tracking
                        with self.lock:
                            self.frames_to_keep.discard(file_path)
                            self.frames_ref_count.pop(file_path, None)
                            self.frame_to_tids.pop(file_path, None)
                    except (FileNotFoundError, PermissionError):
                        continue
                    except Exception as e:
                        self.logger.warning(f"Failed to delete {file_path}: {e}")
        
        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} old files")
            print("cleanedup old filesa")

    def _frame_cleanup_worker(self):
        """Daemon thread worker for cleaning up old frames from disk."""
        self.logger.info("Frame cleanup worker started")
        
        while self.running:
            try:
                self._cleanup_old_frames()
                time.sleep(self.frame_cleanup_interval)
            except Exception as e:
                self.logger.warning(f"Frame cleanup error: {e}")
        
        self.logger.info("Frame cleanup worker stopped")

    def _cleanup_worker(self):
        """Daemon thread worker for cleaning up memory structures."""
        self.logger.info("Memory cleanup worker started")
        
        while self.running:
            try:
                with self.lock:
                    # Clean up old track data for tracks not in active videos
                    current_time = datetime.now()
                    inactive_threshold = timedelta(minutes=self.frame_retention_minutes)
                    
                    # Find tracks to clean
                    tracks_to_clean = []
                    for tid, last_seen in list(self.track_last_seen.items()):
                        if tid not in self.active_videos:
                            if (current_time - last_seen) > inactive_threshold:
                                tracks_to_clean.append(tid)
                    
                    # Clean up inactive tracks
                    for tid in tracks_to_clean:
                        self.track_frames.pop(tid, None)
                        self.track_camera.pop(tid, None)
                        self.track_last_seen.pop(tid, None)
                        # Note: first_seen_time managed by track_id_manager
                    
                    if tracks_to_clean:
                        self.logger.info(f"Cleaned up {len(tracks_to_clean)} inactive tracks from memory")
                        print("cleanup")
                
                time.sleep(self.cleanup_interval)
            except Exception as e:
                self.logger.warning(f"Memory cleanup error: {e}")
        
        self.logger.info("Memory cleanup worker stopped")

    def get_stats(self):
        """Get current statistics."""
        with self.lock:
            return {
                'active_tracks': len(self.track_frames),
                'total_frames': sum(len(frames) for frames in self.track_frames.values()),
                'queued_frames': self.video_queue.qsize(),
                'processed_files': len(self.processed_files),
                'tracked_cameras': len(set(self.track_camera.values())),
                'active_videos': len(self.active_videos),
                'frames_ref_count': len(self.frames_ref_count),
                'frames_to_keep': len(self.frames_to_keep),
                'video_ids_record': len(self.keep_video_ids_record)
            }

    def stop(self):
        self.logger.info("Initiating shutdown...")
        
        # Signal shutdown
        self.running = False
        self.shutdown_event.set()

        # Finalize all active videos
        with self.lock:
            active_tids = list(self.active_videos.keys())

        self.logger.info(f"Finalizing {len(active_tids)} active videos...")
        for tid in active_tids:
            try:
                self._finalize_video(tid, force=True)
            except Exception as e:
                self.logger.error(f"Error finalizing video {tid} during shutdown: {e}")

        # Wait for finalization thread to complete
        self.finalization_complete.wait(timeout=30)

        # Wait for all threads to finish
        self.logger.info("Waiting for threads to finish...")
        self.monitor_thread.join(timeout=5)
        self.frame_writer_thread.join(timeout=5)
        self.cleanup_thread.join(timeout=5)
        self.finalization_thread.join(timeout=5)
        self.frame_cleanup_thread.join(timeout=5)

        # Final stats
        stats = self.get_stats()
        self.logger.info(f"Shutdown complete. Final stats: {stats}")


# Example usage
if __name__ == "__main__":
    # Create manager instance - threads start automatically and monitor continuously
    manager = TrackVideoManager(
        base_folder=r"E:\Zone_Intrusion_Service\frame_data_storage",
        output_folder=r"D:\ZONE_DATA\ZONE_VIDEOS",
        fps=6,
        max_age_hours=24,
        cleanup_interval=1800,  # Memory cleanup every 30 minutes
        scan_interval=2,  # Check for new files every 2 seconds
        min_frames_for_video=5,  # Minimum frames to create video
        frame_cleanup_interval=60,  # Clean old frames every 1 minute
        frame_retention_minutes=10,  # Keep frames for 10 minutes after processing
        max_video_duration=120,  # Max 120 seconds (2 minutes)
        video_inactivity_timeout=5  # Finalize after 5 seconds of inactivity
    )

    # Monitor progress and display stats periodically
    try:
        while True:
            time.sleep(10)  # Print stats every 10 seconds
            stats = manager.get_stats()
            print(f"\n=== Stats ===")
            for key, value in stats.items():
                pass
                # print(f"{key}: {value}")
    except KeyboardInterrupt:
        print("\nShutting down...")
        manager.stop()