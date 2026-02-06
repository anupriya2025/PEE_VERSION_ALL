import base64
from datetime import datetime
import json
import glob
import json
import math
import random
import threading
import cv2
import time
import os
import torch
import numpy as np
from ultralytics import YOLO
from config import ConfigLoader
from collections import defaultdict, deque
from core.video_handler import start_daemon_thread
from threading import Lock, Event
import queue
from torch.cuda.amp import autocast
from share_queue import pid_last_seen,inactive_ids_record
from core.sort1 import Sort
from core.video_rec import VideoCreator
import concurrent.futures
from functools import lru_cache
import gc
import weakref
import share_queue
import glob
import json
import cv2
import os
import time
import numpy as np
from collections import defaultdict, Counter
import threading
from core.common_list_for_video import frame_list
from  logger import LoggerUtility

class FrameProcessor:
    def __init__(self, frame_queue,obj_db,prev_id=0):
        try:
            self.frame_queue = frame_queue
            self.camera_roi_map={}
 
            self.cfg = ConfigLoader()
            self.db =obj_db
            self.prev_id= prev_id + 1
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.maxsize=int(self.cfg.get("MAIN.max_queue_size","100"))
            self.person_model = YOLO("yolo11m.pt")
            self.base_folder = self.db.fetch_Image_folder_path()
            
            self.person_video_frame_count = defaultdict(int)
            self.person_video_lock = Lock()
            self.MAX_VIDEO_FRAMES_PER_PERSON =int(self.cfg.get("RECORDING.recording_max_frames_per_pid","100"))

            self.video_frame_count = defaultdict(int)   # person_id -> count
            self.video_frame_lock = Lock()
            MAX_VIDEO_FRAMES = int(self.cfg.get("RECORDING.recording_max_frames_per_pid","100"))
            

            self.event_queue = queue.Queue(maxsize=self.maxsize)
            self.store_frame = {}
            self.lock= threading.Lock()
            obj_logger=LoggerUtility()
            self.logger=obj_logger.get_logger(__name__)
            
            # Single model for detection
            path=self.cfg.get("MODEL.helmet_model_path")
            self.head_helmet_model = YOLO(path)
            self.head_model = YOLO(path)
            if self.device=="cuda":
                self.head_helmet_model.fuse()
                self.head_helmet_model.to('cuda')
                
                self.person_model.fuse()
                self.person_model.to('cuda')
            self.recording_data = {}
            self.store_video = queue.Queue(maxsize=100)

            buffer_len = int(self.cfg.get("DETECTION.buffer_frames", "300"))  # default ~300 frames
            self.frame_buffers = defaultdict(lambda: deque(maxlen=buffer_len))

            # Camera-specific SORT trackers for better tracking per camera
            self.camera_trackers = {}
            self.tracker_lock = threading.Lock()
            
            self.running = True
            
            # Database and event tracking
            
            
            # Camera-specific threads and queues
            self.camera_threads = {}
            self.camera_locks = defaultdict(threading.Lock)
            self.camera_running = {}
            
            # Shared resources with thread safety
            self.latest_frame_lock = threading.Lock()
            self.person_tracking_lock = threading.Lock()
            
            # Person tracking and detection (per camera)
            self.active_persons = {}
            self.person_detections = {}
            self.pending_detections = {}
            self.detection_lock = Lock()
            self.person_lock = Lock()
            self.policy_tabel={}
            self.policy_tabel=self.db.fetch_camera_ppe_policy()
            self.camera_roi_map = self.db.load_all_camera_roi()

         

               # called ONCE

           
            
            
            # ID management (per camera)
            self.track_id_mapping = defaultdict(dict)  # cam_id -> {sort_id: custom_id}
            self.custom_id_counter = defaultdict(int)  # cam_id -> counter
            self.track_history = defaultdict(dict)
            
            # Performance settings
            width=int(self.cfg.get("PERFORMANCE.target_width","640"))
            height=int(self.cfg.get("PERFORMANCE.target_height","480"))
            self.target_size = (width, height)
            self.min_box_size = int(self.cfg.get("PERFORMANCE.min_box_size","40"))
            self.min_person_area = int(self.cfg.get("PERFORMANCE.min_person_area","200"))
            
            # Frame processing optimization
            self.frame_counter = defaultdict(int)
            self.detection_interval = int(self.cfg.get("PERFORMANCE.detection_interval","200"))
           
            self.colour_helmet_not_Allowed = [c.lower() for c in self.db.fetch_not_allowed_colors()]
            #
            self.vc = VideoCreator(self.db)
            self.vc.start()
            
            # Detection processing with thread pool for parallel PPE detection
            self.detection_queue = queue.Queue(maxsize=self.maxsize)
            self.detection_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=int(self.cfg.get("DETECTION.detection_workers","4")),
                thread_name_prefix="PPE-Detection"
            )
            
            # Start database insertion thread
            insert_db_thread = threading.Thread(target=self._save_to_database, daemon=True)
            insert_db_thread.start()
            insert_video_store_thread = threading.Thread(target=self.save_frame_and_detections, daemon=True)
            insert_video_store_thread.start()
            start_daemon_thread(self.cfg.get("RECORDING.recording_temp_dir", "N/A"),self.cfg.get("RECORDING.recording_video_dir", "N/A"),int(self.cfg.get("RECORDING.recording_max_frames_per_pid", "30")),int(self.cfg.get("RECORDING.recording_fps", "5")))

            
            
            # Colors for visualization
            self.colors = {
                'person': (255, 255, 0),
                'head': (0, 255, 255),
                'helmet': (0, 255, 0),
                'vest': (255, 0, 255),
                'safe': (0, 255, 0),
                'unsafe': (0, 0, 255),
                'tracking': (255, 165, 0)
            }
            
            # Latest processed frames
            self.latest_frames = {}
            self.max_bbox_history =int(self.cfg.get("DETECTION.max_bbox_history","5"))
            self.max_latest_frames = int(self.cfg.get("DETECTION.max_latest_frames","8"))
            
            # Memory management
            self.memory_cleanup_counter = defaultdict(int)
            
            # Start detection worker threads (multiple workers for parallel processing)
            self._start_detection_workers(num_workers=3)
            
        except Exception as e:
            self.logger.exception(f"[ERROR] Initialization failed: {e}")
            raise
    

    






    def _start_detection_workers(self, num_workers=3):
        """Start multiple background threads for PPE detection processing"""
        try:
            self.detection_workers = []
            for i in range(num_workers):
                worker_thread = threading.Thread(
                    target=self._detection_worker,
                    daemon=True,
                    name=f"Detection-Worker-{i}"
                )
                worker_thread.start()
                self.detection_workers.append(worker_thread)
        except Exception as e:
            self.logger.exception(f"[ERROR] Failed to start detection workers: {e}")


    

    def _detection_worker(self):
        """Background worker for processing PPE detections"""
        i=3
        while self.running:
            random_suffix_digits = int(self.cfg.get("DB_SAVER.random_suffix_digits", 3))
            frame_detections = []
            
            try:
                try:
                    detection_data = self.detection_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                if detection_data is None:
                    break
               
                
                person_id, frame, bbox, cam_id, conf = detection_data
                x1, y1, x2, y2 = bbox

                frame_detections.append([x1, y1, x2, y2, person_id])
             
               
                
                # Process PPE detection
                results = self.person_model.track(source=frame, verbose=False)
               

                detection_result = self._perform_ppe_detection(frame, person_id, bbox, cam_id,conf)
                
            
                
                if detection_result:
                    with self.detection_lock:
                        self.person_detections[person_id] = detection_result
                    
                    if detection_result['needs_warning']:
                        try:
                            event_id_str = f"{person_id}"
                           
                            timestamp_str = datetime.now().strftime("%S%M%H%d%m")
                      
                            self.event_queue.put((frame, person_id, cam_id, detection_result, bbox,event_id_str), timeout=0.01)
                            i=i+1
                        except queue.Full:
                            pass
                
                del frame
                self.detection_queue.task_done()
                
            except Exception as e:
                self.logger.exception(f"[ERROR] Detection worker error: {e}")
                time.sleep(0.1)

    # def get_or_create_tracker(self, cam_id):
    #     """Get or create SORT tracker for specific camera"""
    #     with self.tracker_lock:
    #         if cam_id not in self.camera_trackers:
    #             self.camera_trackers[cam_id] = Sort(
    #                 max_age=int(self.cfg.get("SORT.max_age",20)),
    #                 min_hits=int(self.cfg.get("SORT.min_hits",3)),
    #                 iou_threshold=float(self.cfg.get("SORT.min_hitsiou_threshold",0.3)),
    #             )
    #         return self.camera_trackers[cam_id]

    def add_frame_to_camera_queue(self, cam_id, frame,count):
        """Add frame to camera-specific queue and start processing thread if needed"""
        if cam_id not in self.store_frame:
            self.store_frame[cam_id] = queue.Queue(maxsize=1)
            self.camera_running[cam_id] = True
                 # Start dedicated processing thread for this camera
            camera_thread = threading.Thread(
                target=self.process_camera,
                args=(cam_id,),
                daemon=True,
                name=f"Camera-{cam_id}-Thread"
            )
            self.camera_threads[cam_id] = camera_thread
            camera_thread.start()
        
        cam_queue = self.store_frame[cam_id]
        
        # Drop old frames if queue is full to prevent lag
        if cam_queue.full():
            try:
                old_frame = cam_queue.get_nowait()
                del old_frame
            except queue.Empty:
                pass
        
        try:
            cam_queue.put((frame,count), block=False)
        except queue.Full:
            pass



    def _perform_ppe_detection(self, frame, person_id, bbox, cam_id, conf):

        """Perform PPE detection on person crop, respecting camera PPE policy and optional PPE requirements."""
        try:
            x1, y1, x2, y2 = bbox
            if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0:
                return None

            policy = self.policy_tabel.get(cam_id, {})  # {'no helmet':1,'no vest':0}
        

            frame_h, frame_w = frame.shape[:2]
            # padding = int(self.cfg.get("PPE_DETECTION.padding", 30))
            padding=0

            x1_crop = max(0, x1 - padding)
            y1_crop = max(0, y1 - padding)
            x2_crop = min(frame_w, x2 + padding)
            y2_crop = min(frame_h, y2 + padding)

            person_crop = frame[y1_crop:y2_crop, x1_crop:x2_crop].copy()
            
            if person_crop.size == 0:
                return None

            with torch.no_grad():
                results = self.head_helmet_model(
                    person_crop,
                    conf=float(self.cfg.get("PPE_DETECTION.conf_threshold", 0.1)),
                    iou=float(self.cfg.get("PPE_DETECTION.iou_threshold", 0.4)),
                    verbose=False,
                    imgsz=int(self.cfg.get("PPE_DETECTION.img_size", "416")),
                    half=True if self.device == 'cuda' else False
                )

                helmet_detected = False
                vest_detected = False
                head_detected = False
                helmet_color = "Unknown"
                detection_boxes = []

                helmet_conf = float(self.cfg.get("PPE_DETECTION.helmet_conf", 0.6))
                vest_conf = float(self.cfg.get("PPE_DETECTION.vest_conf", 0.1))
                head_conf = float(self.cfg.get("PPE_DETECTION.head_conf", 0.2))
                 

                helmet_boxes = []
                head_boxes = []

                if results and results[0].boxes is not None:
                    boxes = results[0].boxes
                    coords = boxes.xyxy.cpu().numpy()
                    confs = boxes.conf.cpu().numpy()
                    clss = boxes.cls.cpu().numpy().astype(int)

                    # -------------------------------------------------------
                    # CLASSIFICATION: Collect helmet boxes + head boxes
                    # -------------------------------------------------------

                    for i, cls_id in enumerate(clss):
                        conf = confs[i]
                        box_coords = coords[i].astype(int)

                        bx1, by1, bx2, by2 = box_coords

                        # Helmet Box (class = 0)
                        if cls_id == 0 and conf > helmet_conf:
                            helmet_color = self._extract_helmet_color(person_crop, box_coords)
                            helmet_detected=True
                            if helmet_color=='Red' or helmet_color=='Blue' or helmet_color=='Black':
                                # print("not printingggggg helment colour ",helmet_color)
                                helmet_detected = False
                            helmet_boxes.append((box_coords, conf))
                            

                        # Vest Box (class = 1)
                        elif cls_id == 1 and conf > vest_conf:
                          
                            if policy.get('no vest', 0) == 1:
                                vest_detected = True

                        # Head Box (class = 2)
                        elif cls_id == 2 and conf > head_conf:
                         
                            head_boxes.append((box_coords, conf))
                            head_detected = True

                # -------------------------------------------------------
                # MATCH HELMET TO HEAD ✔️
                # -------------------------------------------------------
                correct_helmet_box = None

                if head_boxes and helmet_boxes:
                    hx1, hy1, hx2, hy2 = head_boxes[0][0]
                    head_center = ((hx1 + hx2) // 2, (hy1 + hy2) // 2)

                    min_distance = float("inf")

                    for hb, hconf in helmet_boxes:
                        bx1, by1, bx2, by2 = hb
                        helmet_center = ((bx1 + bx2) // 2, (by1 + by2) // 2)

                        distance = ((helmet_center[0] - head_center[0]) ** 2 +
                                    (helmet_center[1] - head_center[1]) ** 2) ** 0.5

                        # Helmet must be above or touching the head
                        if by2 <= hy2 + 25:  # small tolerance
                            if distance < min_distance:
                                min_distance = distance
                                correct_helmet_box = hb

                    # Assign final helmet
                    if correct_helmet_box is not None and policy.get('no helmet', 0) == 1:
                        helmet_detected = True
                        helmet_color = self._extract_helmet_color(person_crop, correct_helmet_box)
                        if helmet_color=='Red' or helmet_color=='Blue' or helmet_color=='Black':
                            # print("not printingggggg helment colour ",helmet_color)
                            helmet_detected = False


                        # Debug rectangle (optional)
                        cx1, cy1, cx2, cy2 = correct_helmet_box
                       
                        


            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # -------------------------------------------------------
            #   PPE Logic Same As Your Original
            # -------------------------------------------------------

            helmet_required = policy.get('no helmet', 0) == 1
            vest_required = policy.get('no vest', 0) == 1

            needs_warning = False
            safety_status = "Safe"

            if not helmet_required and not vest_required:
                safety_status = "Safe (No PPE Required)"
            else:
                if helmet_required and vest_required:
                    if helmet_detected and vest_detected:
                        safety_status = "Safe"
                    elif helmet_detected and not vest_detected:
                        safety_status = "Only Helmet"
                        needs_warning = True
                    elif not helmet_detected and vest_detected:
                        safety_status = "Only Vest Detected"
                        needs_warning = True
                    else:
                        safety_status = "No Protection"
                        needs_warning = True

                elif helmet_required and not vest_required:
                    if helmet_detected:
                        safety_status = "Helmet Detected"
                    else:
                        safety_status = "No Helmet"
                        needs_warning = True

                elif vest_required and not helmet_required:
                    if vest_detected:
                        safety_status = "Vest Detected"
                    else:
                        safety_status = "No Vest"
                        needs_warning = True
                        
            detection_result = {
                'helmet': helmet_detected,
                'vest': vest_detected,
                'head': head_detected,
                'helmet_color': helmet_color,
                'safety_status': safety_status,
                'needs_warning': needs_warning,
                'detection_boxes': detection_boxes,
                'detected_time': time.time(),
                'person_id': person_id,
                'confidence_scores': {
                    'helmet': max([confs[i] for i in range(len(clss)) if clss[i] == 0], default=0.0),
                    'vest': max([confs[i] for i in range(len(clss)) if clss[i] == 1], default=0.0),
                    'head': max([confs[i] for i in range(len(clss)) if clss[i] == 2], default=0.0)
                }
            }

            return detection_result

        except Exception as e:
            self.logger.exception(f"[ERROR] PPE detection failed: {e}")
            return None





    def _crop_to_absolute_coords(self, box_coords, x1_crop, y1_crop, crop_shape):
        """Convert crop coordinates to absolute frame coordinates"""
        try:
            abs_bbox = [
                int(x1_crop + box_coords[0]),
                int(y1_crop + box_coords[1]),
                int(x1_crop + box_coords[2]),
                int(y1_crop + box_coords[3])
            ]
            return abs_bbox
        except:
            return [0, 0, 0, 0]

    def _extract_helmet_color(self, helmet_crop, box_coords):
        try:
            i=0
            x1, y1, x2, y2 = map(int, box_coords)
            cropped = helmet_crop[y1:y2, x1:x2]
            i=+1

            if cropped.size == 0:
                return None

            hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)

            color_ranges = {
                'Red': [(np.array([0, 120, 70]), np.array([10, 255, 255])),
                        (np.array([170, 120, 70]), np.array([180, 255, 255]))],
                'Yellow': [(np.array([20, 100, 100]), np.array([30, 255, 255])),
                          (np.array([10, 100, 20]), np.array([25, 255, 255]))],
                'Blue': [(np.array([100, 150, 0]), np.array([140, 255, 255]))],
                'Green': [(np.array([40, 70, 70]), np.array([80, 255, 255]))],
                'White': [(np.array([0, 0, 200]), np.array([180, 30, 255]))],
                'Black': [(np.array([0, 0, 0]), np.array([180, 255, 50]))]
            }

            color_counts = {}
            for color, ranges in color_ranges.items():
                mask_total = None
                for lower, upper in ranges:
                    mask = cv2.inRange(hsv, lower, upper)
                    if mask_total is None:
                        mask_total = mask
                    else:
                        mask_total = cv2.bitwise_or(mask_total, mask)
                color_counts[color] = cv2.countNonZero(mask_total)

            dominant_color = max(color_counts, key=color_counts.get)
       
            return dominant_color

        except Exception as e:
            self.logger.exception(f"Error in _extract_helmet_color: {e}")
            return None

    def _determine_safety_status(self, helmet, vest, head, helmet_color):
        """Determine overall safety status"""
        if helmet and vest:
            return "fully_protected"
        elif helmet and not vest :
            return "helmet_only"
        elif not helmet and vest:
            return "vest_only"
        elif head and not helmet and not vest:
            return "no_protection"
        else:
            return "unknown"
        
  



    def _save_to_database(self):
        """Thread that saves detection events (images + DB entries) with annotated helmet/vest status above the bounding box."""
        try:
           
            last_state = defaultdict(dict)
            # frame_detections = []

            # 🔹 Load config values once
            target_kb = int(self.cfg.get("DB_SAVER.image_target_kb", 200))
            min_quality = int(self.cfg.get("DB_SAVER.min_jpeg_quality", 30))
            max_quality = int(self.cfg.get("DB_SAVER.max_jpeg_quality", 95))
            queue_timeout = float(self.cfg.get("DB_SAVER.queue_timeout", 1.0))
            # random_suffix_digits = int(self.cfg.get("DB_SAVER.random_suffix_digits", 3))
            annotation_thickness = int(self.cfg.get("DB_SAVER.annotation_thickness", 4))

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            font_color = (255, 255, 255)  # White text
            bg_color = (0, 0, 0)  # Black background for visibility
            text_thickness = 2

            while self.running:
                processed = False
                try:
                    item = self.event_queue.get(timeout=queue_timeout)
                    processed = True

                    if item is None:
                        break

                    # Unpack event data
                    # frame, person_id, cam_id, detection_result, bbox
                    
                    
                    frame, event_id, cam_id, detection_result, bbox,event_id_str = item
                    x1, y1, x2, y2 = bbox
                   

                    current_state = (
                        detection_result.get('helmet', False),
                        detection_result.get('vest', False),
                        detection_result.get('shoes', False),
                        detection_result.get('helmet_color', None)
                    )
                    # frame_detections.append([x1, y1, x2, y2, event_id])

                    # Skip duplicate states for same event
                    if (event_id in last_state[cam_id] and
                            last_state[cam_id][event_id] == current_state):
                        continue

                    last_state[cam_id][event_id] = current_state

                    # Fetch camera name
                    camera_name = self.db.fetch_Camera_name_deatils(cam_id)
                    

                    # Generate unique event ID
                    # timestamp_str = datetime.now().strftime("%S%M%H%d%m")
                    # unique_suffix = str(random.randint(10**(random_suffix_digits-1),
                    #                                 (10**random_suffix_digits)-1))
                    # event_id_str = f"{timestamp_str}{unique_suffix}"

                    # Annotate frame
                    annotated_frame = frame.copy()
                    cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)),
                                (0, 0, 255), annotation_thickness)

                    # ✅ Add helmet and vest text ABOVE the bounding box
                    helmet_text = f"Helmet: {'Yes' if detection_result.get('helmet') else 'No'}"
                    helmet_present = detection_result.get('helmet', False)
                    vest_text = f"Vest: {'Yes' if detection_result.get('vest') else 'No'}"

                    # Background rectangle for text
                    top_box_height = 60
                    y_text_top = max(0, y1 - top_box_height - 5)
                    # cv2.rectangle(annotated_frame, (x1, y_text_top),
                    #             (x1 + 250, y1 - 5), bg_color, -1)
                    
                    for det_type, det_bbox, extra in detection_result.get('detection_boxes', []):
                        dx1, dy1, dx2, dy2 = map(int, det_bbox)

                        if det_type == 'helmet':
                            color = (0, 255, 0)  # Green for helmet
                            label = f"Helmet"
                        elif det_type == 'head':
                            color = (255, 255, 0)  # Yellow for head
                            label = "Head"
                        elif det_type == 'vest':
                            color = (255, 0, 0)  # Blue for vest
                            label = "Vest"
                        else:
                            continue

                        # Draw bounding box
                        cv2.rectangle(annotated_frame, (dx1, dy1), (dx2, dy2), color, 2)

                        # Draw label on top of the box
                        cv2.putText(annotated_frame, label, (dx1, dy1 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
                        


                
                    # Compress image
                    def compress_image_to_kb(image, target_kb, min_q, max_q):
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), max_q]
                        success, encoded_img = cv2.imencode(".jpg", image, encode_param)
                        size_kb = len(encoded_img) / 1024

                        while size_kb > target_kb and encode_param[1] > min_q:
                            encode_param[1] -= 5
                            success, encoded_img = cv2.imencode(".jpg", image, encode_param)
                            size_kb = len(encoded_img) / 1024

                        return encoded_img

                    compressed_image = compress_image_to_kb(annotated_frame, target_kb, min_quality, max_quality)
                    del annotated_frame

                    base_folder = self.base_folder
                    # If DB returned None or empty, assign a default folder
                    if not base_folder:
                        base_folder = os.path.join(os.getcwd(), "app_data", "images")

                    # Create folder if it does not exist
                    if not os.path.exists(base_folder):
                        os.makedirs(base_folder, exist_ok=True)

                    # Save final usable folder
                    self.base_folder = base_folder
                    today_folder = datetime.now().strftime("%d-%m-%Y")
                    camera_folder = os.path.join(base_folder, today_folder, camera_name)
                    os.makedirs(camera_folder, exist_ok=True)

                    # filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jpg"
                    filename = datetime.now().strftime("%d%m%Y_%H%M%S_%f") + ".jpg"
                    videoname = f"{event_id}.ts"

                    image_path = os.path.join(camera_folder, filename)

                    # Save compressed image
                    with open(image_path, "wb") as f:
                        f.write(compressed_image)

                    relative_image_path = os.path.join(today_folder, camera_name, filename)
                    relative_video_path=os.path.join(today_folder, camera_name, videoname)
                    helmet_color = detection_result.get('helmet_color', None)
                    if not helmet_present:
                            helmet_color = None
                    elif not helmet_color or str(helmet_color).strip().lower() == "unknown":
                            helmet_color = None
                    
                    # Insert event into DB
                    self.db.insert_event(
                        track_id=event_id_str,
                        camera_id=cam_id,
                        camera_name=camera_name,
                        Image_Path=relative_image_path,
                        helmet="Yes" if detection_result.get('helmet') else "No",
                        vest="Yes" if detection_result.get('vest') else "No",
                        shoes="Yes" if detection_result.get('shoes', True) else "No",
                        helmet_color= None,
                        relative_video_path=relative_video_path
                        # helmet_color=helmet_color if helmet_color else None
                    
                    )
                    # self.store_video.put_nowait((frame, frame_detections, event_id, camera_name,event_id_str))
                    self.db.insert_notification_if_allowed()
          

                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.exception(f"[ERROR] Database save failed: {e}")
                finally:
                    if processed:
                        try:
                            self.event_queue.task_done()
                        except Exception:
                            pass

        except Exception as e:
            self.logger.exception(f"[ERROR] DB saver thread crashed: {e}")
        finally:
            self.logger.exception("[DB-SAVER] Exiting DB saver thread")


     

    def get_sort_custom_id(self, sort_id, cam_id):
        """Get or create custom ID for SORT tracking per camera"""
        try:
            if sort_id not in self.track_id_mapping[cam_id]:
                self.custom_id_counter[cam_id] += 1
                self.track_id_mapping[cam_id][sort_id] = self.custom_id_counter[cam_id]
            return self.track_id_mapping[cam_id][sort_id]
        except Exception as e:
            self.logger.exception(f"[ERROR] ID mapping failed: {e}")
            return sort_id

  
    def update_person_tracking(self, person_id, bbox, confidence, timestamp):
        """Update person tracking information and mark person as ACTIVE"""

        try:
            with self.person_lock:

                # Person appears for the first time
                if person_id not in self.active_persons:
                    self.active_persons[person_id] = {
                        'first_seen': timestamp,
                        'last_seen': timestamp,
                        'bbox_history': [bbox],
                        'status': 'new',          # new → active → lost
                        'is_active': True,
                        'detection_count': 1,
                        'confidence': confidence
                    }

                    pid_last_seen[person_id] = {
                        'first_seen': timestamp,
                        'last_seen': timestamp,
                        'frame_count':0
                    }

                else:
                    # Update existing person
                    person_data = self.active_persons[person_id]

                    person_data['last_seen'] = timestamp
                    person_data['bbox_history'].append(bbox)
                    person_data['detection_count'] += 1
                    person_data['confidence'] = confidence
                    person_data['is_active'] = True

                    # Promote status
                    if person_data['status'] == 'new' and person_data['detection_count'] >= 3:
                        person_data['status'] = 'active'

                    # Limit bbox history
                    if len(person_data['bbox_history']) > self.max_bbox_history:
                        person_data['bbox_history'].pop(0)

                    pid_last_seen[person_id]['last_seen'] = timestamp
                    pid_last_seen[person_id]['frame_count'] += 1


        except Exception as e:
            self.logger.exception(f"[ERROR] Person tracking update failed: {e}")


    def should_process_detection(self, person_id,const=None):
        try:
            if not hasattr(self, "person_frame_count"):
                self.person_frame_count = {}
                const=False

            self.person_frame_count[person_id] = self.person_frame_count.get(person_id, 0) + 1

            if person_id in self.person_detections:
                if self.person_frame_count[person_id] > 6:
                    self.person_frame_count[person_id] = 0
                    
                    const=True
                    return True,const
                else:
                    return False

            with self.person_lock:
                if person_id not in self.active_persons:
                    return False,const

                person_info = self.active_persons[person_id]
                if person_info['detection_count'] >= 1:
                    return True,const

            return False,const

        except Exception as e:
            self.logger.exception(f"Error in should_process_detection: {e}")
            return False

    # def draw_visualizations(self, frame, person_id, bbox, cam_id):
    #     """Draw bounding boxes, IDs, and helmet info on frame"""
    #     try:

    #         x1, y1, x2, y2 = bbox

    #         detection_result = None
    #         with self.detection_lock:
    #             if person_id in self.person_detections:
    #                 detection_result = self.person_detections[person_id]

    #         if not detection_result or detection_result.get('safety_status') == "unknown":
    #             return None

    #         if detection_result:
    #             if detection_result.get('needs_warning'):
    #                 main_color = self.colors['unsafe']
    #                 status_text = f"ID:{person_id} - {detection_result.get('safety_status', 'Warning').replace('_', ' ').title()}"
    #             else:
    #                 main_color = self.colors['safe']
    #                 status_text = f"ID:{person_id} - SAFE"
    #         else:
    #             main_color = self.colors['tracking']
    #             status_text = f"ID:{person_id} - TRACKING"

    #         cv2.rectangle(frame, (x1, y1), (x2, y2), main_color, 2)

    #         font = cv2.FONT_HERSHEY_SIMPLEX
    #         font_scale = 0.7
    #         thickness = 2
    #         (text_w, text_h), _ = cv2.getTextSize(status_text, font, font_scale, thickness)

    #         # cv2.rectangle(frame, (x1, y1 - text_h - 6), (x1 + text_w + 4, y1), main_color, -1)
    #         cv2.putText(frame, status_text, (x1 + 2, y1 - 4), font, font_scale, (0, 0, 0), thickness)

    #         if detection_result and 'detection_boxes' in detection_result:
    #             for det in detection_result['detection_boxes']:
    #                 if len(det) < 2:
    #                     continue
    #                 det_type, det_bbox = det[0], det[1]
    #                 extra_info = det[2] if len(det) > 2 else None

    #                 if det_type in ['head', 'vest']:
    #                     continue

    #                 color = self.colors.get(det_type, (128, 128, 128))
    #                 cv2.rectangle(frame, (det_bbox[0], det_bbox[1]), (det_bbox[2], det_bbox[3]), color, 2)

    #                 if det_type == 'helmet' and extra_info:
    #                     label = f"{det_type.title()} ({extra_info})"
    #                 else:
    #                     label = det_type.title()

    #                 cv2.putText(frame, label, (det_bbox[0], det_bbox[1] - 5), font, 0.4, color, 1)
        
    #     except Exception as e:
    #         self.logger.exception(f"[ERROR] Visualization drawing failed: {e}")

    def draw_visualizations(self, frame, person_id, bbox, cam_id):
        """Draw bounding boxes, IDs, and helmet info on frame"""
        try:
            x1, y1, x2, y2 = bbox

            detection_result = None
            with self.detection_lock:
                if person_id in self.person_detections:
                    detection_result = self.person_detections[person_id]

            if not detection_result or detection_result.get('safety_status') == "unknown":
                return None

            if detection_result.get('needs_warning'):
                main_color = self.colors['unsafe']
                status_text = f"ID:{person_id} - {detection_result.get('safety_status', 'Warning').replace('_', ' ').title()}"
            else:
                main_color = self.colors['safe']
                status_text = f"ID:{person_id} - SAFE"

            # Draw main person bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), main_color, 2)

            # ----- TEXT WITH WHITE BACKGROUND -----
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            thickness = 2
            pad_x, pad_y = 4, 4

            (text_w, text_h), _ = cv2.getTextSize(
                status_text, font, font_scale, thickness
            )

            # Background rectangle coords
            bg_x1 = x1
            bg_y1 = max(y1 - text_h - pad_y * 2, 0)
            bg_x2 = x1 + text_w + pad_x * 2
            bg_y2 = y1

            # White background
            cv2.rectangle(
                frame,
                (bg_x1, bg_y1),
                (bg_x2, bg_y2),
                (255, 255, 255),
                -1
            )

            # Optional border (looks nice)
            cv2.rectangle(
                frame,
                (bg_x1, bg_y1),
                (bg_x2, bg_y2),
                main_color,
                1
            )

            # Draw text
            cv2.putText(
                frame,
                status_text,
                (bg_x1 + pad_x, bg_y2 - pad_y),
                font,
                font_scale,
                (0, 0, 0),
                thickness,
                cv2.LINE_AA
            )

            # ----- DRAW EXTRA DETECTIONS -----
            if 'detection_boxes' in detection_result:
                for det in detection_result['detection_boxes']:
                    if len(det) < 2:
                        continue

                    det_type, det_bbox = det[0], det[1]
                    extra_info = det[2] if len(det) > 2 else None

                    if det_type in ['head', 'vest']:
                        continue

                    color = self.colors.get(det_type, (128, 128, 128))
                    cv2.rectangle(
                        frame,
                        (det_bbox[0], det_bbox[1]),
                        (det_bbox[2], det_bbox[3]),
                        color,
                        2
                    )

                    label = (
                        f"{det_type.title()} ({extra_info})"
                        if det_type == 'helmet' and extra_info
                        else det_type.title()
                    )

                    cv2.putText(
                        frame,
                        label,
                        (det_bbox[0], det_bbox[1] - 5),
                        font,
                        0.4,
                        color,
                        1,
                        cv2.LINE_AA
                    )

        except Exception as e:
            self.logger.exception(f"[ERROR] Visualization drawing failed: {e}")


    def cleanup_old_persons(self, current_time, cam_id):
        """Clean up old person records for specific camera"""
        try:
            cleanup_threshold = int(self.cfg.get("PPE_DETECTION.cleanup_threshold","30"))
            persons_to_remove = []
            
            with self.person_lock:
                for person_id, person_info in self.active_persons.items():
                    if person_id.startswith(f"{cam_id}_") and current_time - person_info['last_seen'] > cleanup_threshold:
                        persons_to_remove.append(person_id)
            
            for person_id in persons_to_remove:
                with self.person_lock:
                    if person_id in self.active_persons:
                        del self.active_persons[person_id]
                
                with self.detection_lock:
                    if person_id in self.person_detections:
                        del self.person_detections[person_id]
                
                sort_ids_to_remove = [k for k, v in self.track_id_mapping[cam_id].items() 
                                     if f"{cam_id}_{v}" == person_id]
                for sort_id in sort_ids_to_remove:
                    del self.track_id_mapping[cam_id][sort_id]
                        
        except Exception as e:
            self.logger.exception(f"[ERROR] Cleanup failed: {e}")

    def _memory_cleanup(self, cam_id):
        """Perform periodic memory cleanup per camera"""
        try:
            self.memory_cleanup_counter[cam_id] += 1
            
            if self.memory_cleanup_counter[cam_id] % 100 == 0 and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            with self.latest_frame_lock:
                if len(self.latest_frames) > self.max_latest_frames:
                    oldest_key = min(self.latest_frames.keys()) if self.latest_frames else None
                    if oldest_key is not None:
                        del self.latest_frames[oldest_key]
            
            if self.memory_cleanup_counter[cam_id] % 100 == 0:
                gc.collect()
                
        except Exception as e:
            self.logger.exception(f"[ERROR] Memory cleanup failed: {e}")


    def save_frame_and_detections(self):
      
        """Store frames and detections in memory (frame_list) instead of writing to disk."""
        self.frame_list_lock = Lock()  # Thread safety

        try:
            while self.store_video:
                try:
                    # Expecting (frame, detections, person_id, cam_id)
                    frame, detections, person_id, camera_name ,event_id= self.store_video.get(timeout=0.5)
                    
              

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

                    # --- Prepare detection data ---
                    data = {
                        
                        "camera_id": camera_name,
                        "timestamp": timestamp,
                        "image": frame.copy(),   # store numpy frame
                        "detections": [],
                        "event_id":event_id,
                        "person_id":person_id
                    }

                    for det in detections:
                        # det = [x1, y1, x2, y2, conf, person_id]
                        detection_result = None

                        with self.detection_lock:
                            if person_id in self.person_detections:
                                detection_result = self.person_detections[person_id]

                        # Skip if no valid detection info
                        if not detection_result or detection_result.get('safety_status') == "unknown":
                            continue

                        # Determine label text & color (not drawn yet)
                        if detection_result.get('needs_warning'):
                            main_color = self.colors['unsafe']
                            status_text = f"ID:{person_id} - {detection_result.get('safety_status', 'Warning').replace('_', ' ').title()}"
                        else:
                            main_color = self.colors['safe']
                            status_text = f"ID:{person_id} - SAFE"

                     

                        data["detections"].append({
                            "person_id": det[-1],
                            "bbox": [int(det[0]), int(det[1]), int(det[2]), int(det[3])],
                            "confidence": status_text,
                            "color": main_color
                        })

                    # --- Store in memory safely ---
                    with self.frame_list_lock:
                        frame_list.put(data,block=False)
                    time.sleep(0.1)

                except Exception as e:
                    time.sleep(0.1)
                    continue

        except Exception as e:
            pass


    def save_frame_structured(self,frame, person_id, camera_name):
        # Generate folder structure
        date_folder = datetime.now().strftime("%Y-%m-%d")
        
        base_dir = f"saved_frames/camera_{camera_name}/person_{person_id}/{date_folder}"
        os.makedirs(base_dir, exist_ok=True)

        # File name with timestamp
        timestamp = int(time.time() * 1000)
        file_path = f"{base_dir}/{timestamp}.jpg"

        # Save image
        cv2.imwrite(file_path, frame)


    def draw_roi_on_frame(self,frame, roi_points):
       

        h, w = frame.shape[:2]

        # Remove duplicate last point if same as first
        if roi_points[0] == roi_points[-1]:
            roi_points = roi_points[:-1]

        # % → pixel conversion
        pts = np.array(
            [
                [
                    int(p["x"] * w / 100.0),
                    int(p["y"] * h / 100.0)
                ]
                for p in roi_points
            ],
            dtype=np.int32
        )

        # 🔴 REQUIRED by OpenCV
        pts = pts.reshape((-1, 1, 2))

        # Draw polygon ROI
        cv2.polylines(frame, [pts], isClosed=True, color=(0, 255,0), thickness=2)
     


  

    
       
    

    def process_camera(self, cam_id):
        """Dedicated processing loop for a specific camera with optimized performance"""
        last_cleanup_time = time.time()
        confidance=float(self.cfg.get("PROCESS_CAMERA.detection_conf", 0.5))
        detction_ios=float(self.cfg.get("PROCESS_CAMERA.detection_iou", 0.5))

        try:
            while self.running and self.camera_running.get(cam_id, True):
                try:
                    cam_queue = self.store_frame.get(cam_id)

                    if cam_queue is None:
                        break

                    try:
                        frame_timeout = float(self.cfg.get("PROCESS_CAMERA.frame_timeout", 0.01))
                        
                        frame, count = cam_queue.get(timeout=frame_timeout)
                        
                       
                        
                    except queue.Empty:
                        continue

                    if frame is None:
                        break

                    current_time = time.time()
                    display_frame = frame.copy()
                    
                    points = self.camera_roi_map.get(cam_id)

                    if points and len(points) >= 3:
                        self.draw_roi_on_frame(display_frame, points)
                        h, w = frame.shape[:2]
                        roi_polygon = np.array(
                            [(int(p["x"] * w / 100), int(p["y"] * h / 100)) for p in points],
                            dtype=np.int32
                        ).reshape((-1, 1, 2))

                
                    try:
                        with torch.no_grad():
                            results = self.person_model.track(
                                source=frame,
                                conf=confidance,
                                iou=detction_ios,
                                verbose=False,
                                persist=True
                            )
                           
                                    

                            frame_detections = []

                            if results and results[0].boxes is not None:

                                for box in results[0].boxes:
                                    cls_id = int(box.cls.item())
                                    if cls_id != 0:   # Only person class
                                        continue

                                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                                    conf = float(box.conf.item())
                                    track_id = int(box.id.item()) if box.id is not None else -1
                                    track_id = self.prev_id + track_id
                                    cx = (x1 + x2) // 2
                                    cy = (y1 + y2) // 2

                                    if roi_polygon is not None:
                                        if cv2.pointPolygonTest(roi_polygon, (cx, cy), False) < 0:
                                            continue   # 🚫 outside ROI
                                                                        

                                    person_id = f"{cam_id}_{track_id}"

                                    # Update tracking memory
                                    self.update_person_tracking(person_id, [x1, y1, x2, y2], conf, current_time)
                                    
                                    frame_detections.append([x1, y1, x2, y2, conf, person_id])
                                    
                                    try:
                                        self.detection_queue.put(
                                            (person_id, frame.copy(), [x1, y1, x2, y2], cam_id, conf),
                                            block=False
                                        )
                                    except queue.Full:
                                        pass
                                
                                    camera_name = self.db.fetch_Camera_name_deatils(cam_id)
                                    event_id_str = f"{person_id}"
                                    send_to_video = True

                                    with self.person_video_lock:
                                        if self.person_video_frame_count[person_id] >= self.MAX_VIDEO_FRAMES_PER_PERSON:
                                            send_to_video = False
                                        else:
                                            self.person_video_frame_count[person_id] += 1

                                    if send_to_video and self.store_video is not None:
                                        try:
                                            self.store_video.put_nowait(
                                                (frame, frame_detections, person_id, camera_name, event_id_str)
                                            )
                                        except queue.Full:
                                            pass
                                        except Exception as e:
                                            self.logger.exception(f"[STORE_VIDEO] Unexpected error: {e}")

                                    self.draw_visualizations(display_frame, person_id, [x1, y1, x2, y2], cam_id)
                                    

                                  

                            del results

                    except Exception as e:
                        print(e,"____analytics ")
                       
                        # self.logger.exception(f"[ERROR] Camera {cam_id} detection error: {e}")

                    # -------------------------
                    # Display
                    # -------------------------
                    if self.cfg.get("PROCESS_CAMERA.show_window", "True") == "True":
                        prefix = self.cfg.get("PROCESS_CAMERA.display_window_prefix", "PPE Detection - Camera")
                        if int(self.cfg.get("PROCESS_CAMERA.vieo_mode",0)):
                            cv2.imshow(f"{prefix} {cam_id}", display_frame)
                            cv2.waitKey(int(self.cfg.get("PROCESS_CAMERA.wait_key", 1)))

                    # Save latest frame
                    with self.latest_frame_lock:
                        self.latest_frames[cam_id] = display_frame.copy()
                        if len(self.latest_frames) > self.max_latest_frames:
                            del self.latest_frames[min(self.latest_frames.keys())]

                    # Cleanup
                    if time.time() - last_cleanup_time > float(self.cfg.get("PROCESS_CAMERA.cleanup_interval", 15)):
                        self.cleanup_old_persons(current_time, cam_id)
                        last_cleanup_time = time.time()

                    self._memory_cleanup(cam_id)
                    del display_frame

                except KeyboardInterrupt:
                    self.logger.exception(f"[INFO] Camera {cam_id} processing interrupted")
                    break
                except Exception as e:
                    time.sleep(0.1)
                    print(e)
                    self.logger.exception(f"[ERROR] Camera {cam_id} frame processing error: {e}")
                self.cleanup_inactive_tracks()
        finally:
            self.logger.info(f"[INFO] Camera {cam_id} processing thread stopped")
            cv2.destroyAllWindows()
            


    def cleanup_inactive_tracks(self, max_age=5):
        inactive_ids = []
        current_time = time.time()

        for pid in self.active_persons:
            last_seen = self.active_persons[pid]['last_seen']
            if (current_time - last_seen) > max_age:
                inactive_ids.append(pid)

        for pid in inactive_ids:
            
            del self.active_persons[pid]
            inactive_ids_record.append(pid)


    def process(self):
        """Main processing loop - distributes frames to camera threads"""
        try:
            
            while self.running:
                try:
                    try:
                        cam_id, frame, count = self.frame_queue.get(timeout=0.01)
                      
                        if frame is None:
                            break
                     
                       
                        # Distribute frame to camera-specific queue
                        self.add_frame_to_camera_queue(cam_id, frame,count)
                        
                        # Mark as processed
                        try:
                            self.frame_queue.task_done()
                        except:
                            pass
                    
                    except queue.Empty:
                        continue
                    except Exception as e:
                        self.logger.exception(f"[ERROR] Frame distribution error: {e}")
                        continue
                
                except KeyboardInterrupt:
                    self.logger.exception("[INFO] Frame distribution interrupted by user")
                    break
                except Exception as e:
                    self.logger.exception(f"[ERROR] Distribution loop error: {e}")
                    time.sleep(0.001)
        
        except Exception as e:
            self.logger.exception(f"[ERROR] Main processing loop crashed: {e}")
        finally:
            # Stop all camera threads
            self.logger.info("[INFO] Stopping all camera processing threads...")
            for cam_id in self.camera_running:
                self.camera_running[cam_id] = False
            
            # Wait for threads to finish
            for cam_id, thread in self.camera_threads.items():
                thread.join(timeout=2.0)
              
            cv2.destroyAllWindows()




    def _expand_head_to_person(self, frame, head_bbox):
        try:
            x1, y1, x2, y2 = head_bbox
            # return [ x1, y1, x2, y2]
            frame_h, frame_w = frame.shape[:2]
            
            head_width = x2 - x1
            head_height = y2 - y1
            
            # Approximate person dimensions
            person_width = int(head_width *2)#if u want to go for person  (head_width*2.5)
            person_height = int(head_height*2)# if u want to go for person  (head_height*6)
            
            # Calculate person bbox
            center_x = (x1 + x2) // 2
            person_x1 = max(0, center_x - person_width // 2)
            person_x2 = min(frame_w, center_x + person_width // 2)
            person_y1 = max(0, y1 - head_height // 4)
            person_y2 = min(frame_h, y1 + person_height)
            
            return [person_x1, person_y1, person_x2, person_y2]
            
        except:
            return head_bbox

    def fect_event_photo(self):
        """Placeholder for fetching event photos"""
        pass

    def stop(self):
        """Stop all processing"""
        self.running = False
        
        # Stop all camera threads
        for cam_id in list(self.camera_running.keys()):
            self.camera_running[cam_id] = False
        
        # Wait for all camera threads
        for thread in self.camera_threads.values():
            thread.join(timeout=2.0)
        
        # Signal detection workers to stop
        for _ in range(len(self.detection_workers) if hasattr(self, 'detection_workers') else 0):
            try:
                self.detection_queue.put(None, timeout=0.5)
            except:
                pass
        
        # Wait for detection workers to finish
        if hasattr(self, 'detection_workers'):
            for worker in self.detection_workers:
                if worker.is_alive():
                    worker.join(timeout=2.0)
        
        # Shutdown detection exec
        if hasattr(self, 'detection_executor'):
            self.detection_executor.shutdown(wait=True, cancel_futures=True)
        
        # Call event photo fetch
        self.fect_event_photo()
        
        # Clear all data structures
        with self.person_lock:
            self.active_persons.clear()
        
        with self.detection_lock:
            self.person_detections.clear()
        
        with self.latest_frame_lock:
            self.latest_frames.clear()
        
        # Clear tracking mappings
        self.track_id_mapping.clear()
        self.track_history.clear()
        self.pending_detections.clear()
        
        # Clear camera trackers
        with self.tracker_lock:
            self.camera_trackers.clear()
        
        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Force garbage collection
        gc.collect()
        
        cv2.destroyAllWindows()

    def close(self):
        """Close all resources"""
        # self.vc.stop()
        self.stop()
        try:
            if hasattr(self, 'db'):
                self.db.close()
        except Exception as e:
            self.logger.exception(f"[ERROR] Resource cleanup failed: {e}")


