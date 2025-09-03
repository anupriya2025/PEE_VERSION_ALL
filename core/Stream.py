# videostream.py
from collections import defaultdict

import cv2
import threading
import time
import logging
import os
import torch
no_sorcse=0

if torch.cuda.is_available():
    print("Using GPU:", torch.cuda.get_device_name(0))
else:
    print("GPU not available. Using CPU.")

class VideoStream:
    def __init__(self, sources, frame_queue, fps_limit=20, camera_id=None):
        self.camera_id=camera_id
        

        self.sources = sources
        
        self.frame_queue = frame_queue
        self.captures = [cv2.VideoCapture(src) for src in sources]
        self.running = True
        self.last_seen = defaultdict(lambda: time.time())
        self.id_expiry_seconds = 5
        self.last_times = [0] * len(sources)
        self.insert_interval = 2.0 / fps_limit  # Limit to N frames per second

    def start(self):
        threading.Thread(target=self.update, daemon=True).start()

    def is_rtsp_source(self,source):
        return str(source).lower().startswith("rtsp://")


    def update(self):
        while self.running:
            now = time.time()

            for i, cap in enumerate(self.captures):
                source = self.sources[i]

                if not cap.isOpened():
                    logging.warning(f"[Camera {i}] Stream not opened. Attempting to reopen...")
                    self.captures[i] = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                    cap = self.captures[i]

                ret, frame = cap.read()

                if not ret:
                    logging.warning(f"[Camera {i}] Failed to read frame.")

                    if not self.is_rtsp_source(source):
                        logging.info(f"[Camera {i}] Video file ended. Restarting...")
                    cap.release()
                    self.captures[i] = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                    break  # skip rest of loop for this camera

                # For video files, sleep to maintain real-time playback
                if not self.is_rtsp_source(source):
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    delay = 1.0 / fps if fps > 0 else 0.04  # fallback 25 FPS
                    time.sleep(delay)
       
                if now - self.last_times[i] >= self.insert_interval:
                    if self.frame_queue.full():
                        try:
                            self.frame_queue.get_nowait()
                        except:
                            pass
                    # if frame is not None:
                    #     cv2.imshow(f"Camera {self.camera_id}", frame)

                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     break
                    self.frame_queue.put((self.camera_id, frame))  # camera-specific queue
                    self.last_times[i] = now
   

    def stop(self):
        print("stop stream flowww")
        self.running = False
       
        for cap in self.captures:
            cap.release()
