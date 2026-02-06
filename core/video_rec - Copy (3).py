# video_creator_optionA.py
from pathlib import Path
import threading
import av
import cv2
import os
import time
import shutil
import glob
import numpy as np
from queue import Empty, Queue
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from core.common_list_for_video import frame_list  # shared global list
from datetime import datetime
import multiprocessing
from multiprocessing import Queue as MPQueue, Process, Value
from config import ConfigLoader
from core.database import EventDatabase
from logger import LoggerUtility
from share_queue import pid_last_seen
# -------------------------

# -------------------------


def delete_folders_for_completed_pids(temp_dir, completed_pids):
    pass
    # """
    # Deletes folders inside temp_dir if their PID is in completed_pids.
    # Folder names like: CAM49_Camera_1_832 → PID = 832
    # """
    # for folder_name in os.listdir(temp_dir):
    #     folder_path = os.path.join(temp_dir, folder_name)

    #     if not os.path.isdir(folder_path):
    #         continue

    #     try:
    #         pid = str(int(folder_name.split("_")[-1]))
    #     except:
    #         continue

    #     if pid not in completed_pids:
    #         continue

    #     try:
    #         shutil.rmtree(folder_path)
    #         print(f"[CLEANUP] Deleted temp folder for PID {pid}: {folder_path}")
    #     except Exception as e:
    #         print(f"[CLEANUP ERROR] Failed to delete {folder_path}: {e}")
    #         pass
def _create_video_from_images_in_process(
    image_files, pid, cam_id, video_dir, fps, event_id, logger
):
    
    try:
        if not image_files:
            return None

        first_img = None
        for p in image_files:
            if os.path.exists(p):
                first_img = cv2.imread(p)
                if first_img is not None:
                    break

        if first_img is None:
            return None

        h, w, _ = first_img.shape
        timestamp_str = time.strftime("%d%m%Y_%H%M%S")
        date_folder = time.strftime("%d-%m-%Y")

        relative_folder = os.path.join(date_folder, cam_id)
        camera_folder = os.path.join(video_dir, relative_folder)
        os.makedirs(camera_folder, exist_ok=True)

        video_filename = f"{pid}.ts"
        video_path = os.path.join(camera_folder, video_filename)
        db_video_path = os.path.join(relative_folder, video_filename)

        container = av.open(video_path, mode="w", format="mpegts")
        stream = container.add_stream("libx264", rate=fps)
        stream.width = w
        stream.height = h
        stream.pix_fmt = "yuv420p"
        stream.bit_rate = 600_000

        stream.codec_context.options = {
            "preset": "ultrafast",
            "crf": "28",
            "profile": "baseline",
            "tune": "zerolatency"
        }

        frames_written = 0

        for img_path in image_files:
            if not os.path.exists(img_path):
                continue

            frame = cv2.imread(img_path)
            if frame is None:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_frame = av.VideoFrame.from_ndarray(frame_rgb, format="rgb24")

            for packet in stream.encode(video_frame):
                container.mux(packet)

            frames_written += 1

        for packet in stream.encode(None):
            container.mux(packet)

        container.close()
        time.sleep(0.1)  # 🔥 WINDOWS FILE LOCK RELEASE

        if os.path.exists(video_path) and frames_written > 0:
            print("_create_video_from_images_in_process",pid)
            return db_video_path

        if os.path.exists(video_path):
            os.remove(video_path)
        
           

    except Exception as e:
        print(f"[VIDEO STORING ERROR] {e}")
    return None

def video_encoder_process(
    main_queue: MPQueue,
    status_queue: MPQueue,
    temp_dir: str,
    video_dir: str,
    fps: int,
    min_frames: int,
    running_flag,
    logger,
    max_frames_per_pid: int
):

    PID_LOST_TIMEOUT = 10  # seconds (tune if needed)

    pid_to_files = defaultdict(list)
    pid_event = {}
    pid_cam = {}
    # pid_last_seen = {}     # 👈 NEW
    completed_pids = set()

    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)

    while True:
       
        # 🔹 1. Check LOST PIDs
        for pid in list(pid_to_files.keys()):
            if pid in completed_pids:
                continue
            now = time.time()
            last_seen = pid_last_seen.get(pid, now)
            frame_count = len(pid_to_files[pid])

            # PID LOST & enough frames collected
            if frame_count >= min_frames and (now - last_seen) > PID_LOST_TIMEOUT:
                completed_pids.add(pid)

               
        try:
            item = main_queue.get(timeout=1)
        except Exception:
         
            continue

        # if item is None:
        #     break

        try:
            pid, cam_id, ts, jpg_bytes, event_id = item
            pid = str(pid)
        except Exception:
            continue

        if pid in completed_pids:
            continue

        pid_event[pid] = event_id
        pid_cam[pid] = cam_id
        pid_last_seen[pid] =time.time() 
        try:
            person_dir = os.path.join(temp_dir, f"{pid_cam.pop(pid)}_{pid}")
            os.makedirs(person_dir, exist_ok=True)
        except Exception:
            pass

        seq = len(pid_to_files[pid]) + 1

        # 🚫 Hard stop
        if seq > max_frames_per_pid:
            continue

        frame_path = os.path.join(person_dir, f"frame_{ts}.jpg")

        try:
            with open(frame_path, "wb") as f:
                f.write(jpg_bytes)
        except Exception:
            continue

        pid_to_files[pid].append(frame_path)

  

# -------------------------
# Main VideoCreator class to be used in main process
# -------------------------
class VideoCreator:
    def __init__(self,db:EventDatabase):
        self.running = False
        self.db = db
        self.cfg = ConfigLoader()
        obj_logger=LoggerUtility()
        self.logger=obj_logger.get_logger(__name__)
        self.record_enabled = self.cfg.get("RECORDING.enable_recording", "true").lower() == "true"
        
        self.fps = int(self.cfg.get("RECORDING.recording_fps", 30))
        self.min_frames = int(self.cfg.get("RECORDING.recording_min_frames", 50))
        self.max_frames_per_pid = int(self.cfg.get("RECORDING.recording_max_frames_per_pid", 30))
        self.backlog_threshold = int(self.cfg.get("RECORDING.recording_backlog_threshold", 300))



        self.temp_dir = self.cfg.get("RECORDING.recording_temp_dir", r"E:\PPE_TEMP_FRAMES")
        self.video_dir = self.cfg.get("RECORDING.recording_video_dir", r"E:\Ppe_Events\PPE_VIDEOS")

        # Fallback paths (auto-created inside current directory)
        fallback_temp = os.path.join(os.getcwd(), "app_data", "temp_frames")
        fallback_video = os.path.join(os.getcwd(), "app_data", "videos")


        # ------------ SAFE TEMP DIR ------------
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
        except Exception:
            print(f"[WARNING] Cannot create folder: {self.temp_dir}")
            print(f"          Using fallback path: {fallback_temp}")
            os.makedirs(fallback_temp, exist_ok=True)
            self.temp_dir = fallback_temp


        # ------------ SAFE VIDEO DIR ------------
        try:
            os.makedirs(self.video_dir, exist_ok=True)
        except Exception:
            print(f"[WARNING] Cannot create folder: {self.video_dir}")
            print(f"          Using fallback path: {fallback_video}")
            os.makedirs(fallback_video, exist_ok=True)
            self.video_dir = fallback_video

        # locks & metadata
        self.lock = threading.Lock()
        self.frame_counter = defaultdict(int)
        self.person_metadata = defaultdict(list)

        # local thread pool to convert frames -> jpeg bytes
        self.frame_saver_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="FrameSaver")

        # encoder queue and status queue (multiprocessing)
        self.encoder_queue = MPQueue(maxsize=1000)
        self.status_queue = MPQueue(maxsize=1000)
        self.encoder_queue_size = int(self.cfg.get("RECORDING.encoder_queue_size", 1000))
        self.status_queue_size = int(self.cfg.get("RECORDING.status_queue_size", 1000))

        # self.video_update_queue=int(self.cfg.get("MAIN.max_queue_size","100"))
        self.video_update_queue = Queue()
        

        # encoder process / running flag
        self.encoder_process = None
        self.encoder_running_flag = multiprocessing.Value('b', False)

        # sampling behavior to drop frames under high backlog
        self.sample_rate = 1
        self.sample_increment = 1
        self.sample_upper = 10

        # completed_pids: once a PID has a video created, we stop saving frames for it
        self.completed_pids = set()
        self.completed_pids_lock = threading.Lock()
        threading.Thread(target=self.video_update_worker, daemon=True).start()


        # start-up: ensure dirs exist
        self._setup_directories()

        # thread that listens to encoder status queue
        self.status_listener_thread = None

    def _setup_directories(self):
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            # self.logger.info(f"[INFO] Temp directory created/verified: {self.temp_dir}")
        except Exception as e:
            self.logger.exception(f"[WARN] Temp dir create fail: {e}; fallback to local temp_frames")
            self.temp_dir = "temp_frames"
            os.makedirs(self.temp_dir, exist_ok=True)
        try:
            os.makedirs(self.video_dir, exist_ok=True)
            # self.logger.info(f"[INFO] Video directory created/verified: {self.video_dir}")
        except Exception as e:
            self.logger.exception(f"[WARN] Video dir create fail: {e}; fallback to recorded_videos")
            self.video_dir = "recorded_videos"
            os.makedirs(self.video_dir, exist_ok=True)

    def start(self):
        """Start encoder process and frame collector"""
        # self.logger.info("[INFO] VideoCreator (Option A) starting.._________________________________.")
        self.running = True
        
        # start encoder process
        self.encoder_running_flag.value = True
        self.encoder_process = Process(
            target=video_encoder_process,
            args=(self.encoder_queue, self.status_queue, self.temp_dir, self.video_dir,
                  self.fps, self.min_frames, self.encoder_running_flag,self.logger,self.max_frames_per_pid),
            daemon=True
        )
        self.encoder_process.start()
        self.logger.info(f"[INFO] Encoder process started (pid={self.encoder_process.pid})")

        # start frame collector thread from global frame_list
        threading.Thread(target=self._collect_frames_from_global, daemon=True, name="FrameCollector").start()
  

    def stop(self):
        """Stop the whole VideoCreator (request encoder flush then exit)"""
        self.logger.info("[INFO] Stopping VideoCreator (Option A)...")
        self.running = False

        # wait briefly for in-flight tasks
        time.sleep(0.5)

        # signal encoder process to stop accepting new frames
        self.encoder_running_flag.value = False

        # send sentinel so encoder can exit cleanly
        try:
            self.encoder_queue.put_nowait(None)
        except Exception as e:
            pass

        # join encoder process
        if self.encoder_process:
            self.encoder_process.join(timeout=30)
            if self.encoder_process.is_alive():
                try:
                    self.encoder_process.terminate()
                except:
                    pass

        # wait for status listener to process remaining messages
        if self.status_listener_thread:
            self.status_listener_thread.join(timeout=2.0)

        # shutdown executor
        try:
            self.frame_saver_executor.shutdown(wait=False, cancel_futures=True)
        except:
      
            pass
        self.logger.exception("[INFO] VideoCreator stopped.")

    #
    # ----------------- collect frames -----------------
    def _collect_frames_from_global(self):
        """
        Moves items from shared global frame_list into local processing by submitting
        to frame_saver_executor. Each submitted task prepares jpeg bytes and tries to
        enqueue to encoder process. If PID is completed, skip saving.
        """
        while self.running:
            try:
                if not frame_list:
                    time.sleep(0.5)
                    continue

                
                batch_size = min(8, frame_list.qsize())
                if batch_size <= 0:
                    time.sleep(0.1)
                    continue

                for _ in range(batch_size):
                    try:
                        fdata = frame_list.get(block=False)
                    except Exception:
                        continue

                    # Submit to executor to convert to jpg bytes + enqueue to encoder
                    self.frame_saver_executor.submit(self._handle_frame_for_encoding, fdata)

            except Exception as e:
             
                self.logger.exception(f"[ERROR] Frame collector failed: {e}")
                time.sleep(0.5)

    # ----------------- prepare & enqueue -----------------

    def video_update_worker(self):
        while True:
            try:
                event_id, video_path = self.video_update_queue.get(timeout=1)
                self.db.update_video_path(event_id, video_path)
                self.video_update_queue.task_done()
                
            except Exception:
                continue
  


    def _save_frame_and_toon(self, frame, tracked_objects, camera_name, timestamp):
        """Save frame image and detection data in TOON format (Token-Oriented Object Notation)"""
        try:
            self.frames_saved=0
            # Create folder structure: camera_name/YYYY-MM-DD/
            date_str = timestamp.strftime("%Y-%m-%d")

            folder_path = Path(self.temp_dir)
            folder_path.mkdir(parents=True, exist_ok=True)
            # Generate filename: timestamp_microseconds
            filename_base = timestamp.strftime("%Y%m%d_%H%M%S_%f")

            # Save image
            image_path = folder_path / f"{filename_base}.jpg"
            cv2.imwrite(str(image_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

            # Prepare TOON format data
            # TOON uses compact, token-efficient notation
            toon_path = folder_path / f"{filename_base}.toon"

            with open(toon_path, 'w') as f:
                # Frame metadata (compact single line)
                h, w = frame.shape[:2]
                f.write(
                    f"@f:{camera_name}|{timestamp.isoformat()}|{filename_base}.jpg|{w}x{h}|n:{len(tracked_objects)}\n")

                f.write("@d:pid|b|t|c\n")

                # Write each detection in compact format
                for obj in tracked_objects:
                    tid = obj.get('person_id', -1)
                    box = obj.get('bbox', [0, 0, 0, 0])
                    # Compact bbox notation: x1,y1,x2,y2
                    bbox_str = f"{box[0]},{box[1]},{box[2]},{box[3]}"
                    # Abbreviated values for common types to save tokens
                    confidence = obj.get('confidence', "N/A")
                    # Single line per detection, pipe-separated
                    f.write(f"{tid}|{bbox_str}|{timestamp}|{confidence}\n")

            self.frames_saved += 1

            if self.frames_saved % 100 == 0:
                self.logger.info(f"Frame data storage: {self.frames_saved} frames saved (TOON format)")

        except Exception as e:
            self.logger.warning(f"Failed to save frame data: {e}", exc_info=True)
            self.frames_failed += 1

    def _handle_frame_for_encoding(self, fdata):
        try:
            img = fdata.get("image")
            detections = fdata.get("detections", [])
            cam_id = fdata.get("camera_id", "0")
            event_id = fdata.get("event_id", "")

            if img is None or not detections:
                return


            self._save_frame_and_toon(
                img,
                detections,
                cam_id,
                datetime.now()
            )

        except Exception as e:
            self.logger.exception(f"[ENCODER INPUT ERROR] {e}")



    def flush_all_videos(self):
      
        """
        Optionally request encoder flush. For Option A we rely on stop() to flush.
        """
        self.logger.info("[INFO] Requesting encoder flush (handled on stop).")

# EOF