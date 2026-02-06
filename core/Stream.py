
import cv2
import threading
import time
import logging
import os
import torch
import configparser
from collections import defaultdict
from config import ConfigLoader
from  logger import LoggerUtility



class VideoStream:
    def __init__(self, sources, frame_queue, camera_id=None):
        self.cfg = ConfigLoader()
       

        # ---- CONFIG PARAMETERS ----
        self.camera_id = camera_id
        self.sources = sources
        self.frame_queue = frame_queue
        self.frame_count=0
        self.fps_limit = float(self.cfg.get("VIDEO_STREAM.fps_limit", 30))
        self.id_expiry_seconds = int(self.cfg.get("VIDEO_STREAM.id_expiry_seconds", "5"))
        self.reconnect_delay = float(self.cfg.get("VIDEO_STREAM.reconnect_delay", "0.5"))
        self.insert_interval = float(self.cfg.get("VIDEO_STREAM.insert_interval", "1.0 / self.fps_limit"))
        self.max_queue_size = int(self.cfg.get("VIDEO_STREAM.max_queue_size", "50"))
        self.enable_logging = str(self.cfg.get("VIDEO_STREAM.enable_logging", "True")).lower() == "true"
        obj_logger=LoggerUtility()
        self.logger=obj_logger.get_logger(__name__)
            

        # ---- INIT ----
        self.captures = [cv2.VideoCapture(src) for src in sources]
        self.running = True
        self.last_seen = defaultdict(lambda: time.time())
        self.last_times = [0] * len(sources)

        if torch.cuda.is_available():
            pass
        else:
            self.logger.error("GPU is not available. The system is Using CPU.")

    # -----------------------------------
    def start(self):
       
        threading.Thread(target=self.update, daemon=True).start()

    # -----------------------------------
    def is_rtsp_source(self, source):
        return str(source).lower().startswith("rtsp://")

    # -----------------------------------
    def update(self):
        while self.running:
            now = time.time()

            for i, cap in enumerate(self.captures):
                source = self.sources[i]

                # Ensure the stream is open
                if not cap.isOpened():
                    if self.enable_logging:
                        self.logger.warning(f"[Camera {self.camera_id}] Stream Access Failed. Retrying connection...")
                    self._reopen_source(i, source)
                    continue

                ret, frame = cap.read()

                if not ret:
                    if self.enable_logging:
                        self.logger.warning(f"[Camera {self.camera_id}] Failed to Read Frame.")
                    self._handle_failed_frame(i, source)
                    continue
                # h, w = frame.shape[:2]

                # crop_x = int(w * 0.05)   # 5% from left & right
                # crop_y = int(h * 0.10)   # 5% from top & bottom

                # cropped_frame = frame[
                #     crop_y : h - crop_y,
                #     crop_x : w - crop_x
                # ]
                # frame = cv2.resize(cropped_frame,(960,640))

                frame = cv2.resize(frame,(960,640))
                # # For video files, maintain playback speed
                # if not self.is_rtsp_source(source):
                #     fps = cap.get(cv2.CAP_PROP_FPS)
                #     delay = 1.0 / fps if fps > 0 else 0.04
                #     time.sleep(delay)

                # FPS limit / frame insert interval
                # if now - self.last_times[i] >= self.insert_interval:
                #     if self.frame_queue.qsize() > self.max_queue_size:
                #         try:
                #             self.frame_queue.get_nowait()  # remove old frame
                #         except:
                #             pass
                try:
                    self.frame_queue.put((self.camera_id, frame, self.frame_count),block=False)
                except Exception:
                    pass
                self.last_times[i] = now

              
    # -----------------------------------
    def _handle_failed_frame(self, i, source):
        """Handle when frame read fails (reconnect logic)."""
        self.captures[i].release()
        time.sleep(self.reconnect_delay)

        if not self.is_rtsp_source(source):
            if self.enable_logging:
                self.logger.info(f"[Camera {self.camera_id}] Restarting The Local Video File...")
            self.captures[i] = cv2.VideoCapture(os.path.abspath(source))
        else:
            if self.enable_logging:
                self.logger.info(f"[Camera {self.camera_id}] Reconnecting The RTSP Stream...")
            self.captures[i] = cv2.VideoCapture(source, cv2.CAP_FFMPEG)

    # -----------------------------------
    def _reopen_source(self, i, source):
        """Try reopening a failed video source."""
        self.captures[i].release()
        time.sleep(self.reconnect_delay)

        if self.is_rtsp_source(source):
            self.captures[i] = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        else:
            self.captures[i] = cv2.VideoCapture(os.path.abspath(source))

    # -----------------------------------
    def stop(self):
        self.running = False
        for cap in self.captures:
            cap.release()
        if self.enable_logging:
            pass