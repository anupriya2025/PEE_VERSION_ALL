import base64
import threading
import cv2
import time
import os
import torch
import numpy as np
from ultralytics import YOLO
from core.database import EventDatabase
from collections import defaultdict
from threading import Lock, Event
import queue
from torch.cuda.amp import autocast
from share_queue import frame_queue_to_show,show_queue
from core.sort1 import Sort
import concurrent.futures
from functools import lru_cache

import share_queue

os.makedirs("person_crops", exist_ok=True)

class FrameProcessor:
    def __init__(self, frame_queue, person_crop_queue):
        try:
            self.frame_queue = frame_queue
            self.person_crop_queue = person_crop_queue
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.frame_queue_to_store_detection= queue.Queue(maxsize=100)
            
            # Initialize SORT tracker with optimized parameters
            self.sort_tracker = Sort(
                max_age=30,
                min_hits=4,
                iou_threshold=0.3
            )
            # show_queues[cam_id] = Queue(maxsize=50)
            
            # Optimized thread management
            self._load_and_optimize_models()
            self.detection_executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=8,  # Increased for better parallel processing
                thread_name_prefix="detection"
            )
            self.detection_thread_lock = Lock()
            self.active_detection_threads = 0
            self.max_detection_threads = 8  # Increased from 5
            det_thread= threading.Thread(target=self.detection_process, daemon=True)
            det_thread.start()
            

            
            # Load and optimize models
            # self._load_and_optimize_models()
            
            self.db = EventDatabase()
            self.all_events = set()
            
            # SORT-specific tracking settings
            self.track_id_mapping = {}
            self.custom_id_counter = 1
            self.track_history = {}
            self.lost_tracks = {}
            
            # Optimized caching with TTL
            self.detection_cache = {}
            self.cache_ttl = {}
            self.cache_duration = 0.3  # Reduced for better accuracy
            
            # Performance settings
            self.target_size = (640, 480)
            self.min_box_size = 30
            self.running = True
            
            # Frame processing optimization
            self.frame_counter = 0
            self.last_detections = []
            
            # Batch processing for database operations
            self.db_batch = []
            self.db_batch_size = 5
            self.last_db_flush = time.time()
            self.db_lock = Lock()
            
            # Smart detection intervals based on tracking confidence
            self.detection_intervals = {}  # track_id -> next_detection_time
            self.high_conf_interval = 0.5   # High confidence tracks: detect every 0.5s
            self.low_conf_interval = 0.2    # Low confidence tracks: detect every 0.2s
            
            # FPS tracking
            self.fps_counter = 0
            self.fps_start_time = time.time()
            self.fps_history = []
            
            # Video end detection
            self.consecutive_empty_frames = 0
            self.max_empty_frames = 30
            
            # Detection visualization settings
            self.colors = {
                'helmet': (0, 255, 0),
                'vest': (255, 0, 255),
                'head': (0, 0, 255),
                'shoes': (255, 165, 0),
                'person': (255, 255, 0),
                'full_body': (0, 255, 255),
                'partial_body': (128, 128, 128)
            }
            
            # Track inserted person IDs with expiry to avoid duplicates
            self.inserted_person_ids = {}  # person_id -> timestamp
            self.insertion_cooldown = 5.0  # 5 seconds cooldown
            
            print("[INFO] Optimized FrameProcessor initialized successfully")
            
        except Exception as e:
            print(f"[ERROR] Initialization failed: {e}")
            raise

    def _load_and_optimize_models(self):
        """Load and optimize all models for better performance"""
        try:
            # print("[INFO] Loading and optimizing models...")
            
            # Load models
            self.detection_model = YOLO("resource/helmet_vest.pt")
            self.model_shoes = YOLO("resource/model_shoes.pt")
            self.pose_model = YOLO('resource/yolov8n-pose.pt')
            self.tracking_model = YOLO("resource/yolov8n.pt")
            
            if torch.cuda.is_available():
                # print("[INFO] Applying CUDA optimizations...")
                
                models = [self.detection_model, self.tracking_model, self.pose_model, self.model_shoes]
                
                for model in models:
                    model.to('cuda')
                    # Enable model optimizations
                    try:
                        model.fuse()  # Fuse conv and bn layers for speed
                    except Exception as e:
                        print(f"[WARNING] Model fusion failed: {e}")
                    
                    # Use half precision for inference speed
                    try:
                        model.half()
                    except Exception as e:
                        print(f"[WARNING] Half precision conversion failed: {e}")
                
                # Warm up models with dummy data
                dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
                for model in models:
                    try:
                        with torch.no_grad():
                            _ = model(dummy_img, verbose=False, imgsz=320)
                    except:
                        pass
                        
                print("[INFO] Models optimized and warmed up")
                
        except Exception as e:
            print(f"[ERROR] Model loading failed: {e}")
            raise

  
   
    def detect_helmet_vest_head(self, frame, person_id, bbox):
        """Optimized detection with smart caching"""
        try:
            current_time = time.time()
            
            # Check cache with TTL
            cache_key = f"{person_id}_{current_time // self.cache_duration}"
            if (cache_key in self.detection_cache and 
                cache_key in self.cache_ttl and 
                current_time - self.cache_ttl[cache_key] < self.cache_duration):
                return self.detection_cache[cache_key]

            x1, y1, x2, y2 = bbox
            
            # Validate bbox
            if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0:
                return None

            # Optimized cropping with minimal padding
            padding = 10  # Reduced from 15
            frame_h, frame_w = frame.shape[:2]
            
            x1_crop = max(0, x1 - padding)
            y1_crop = max(0, y1 - padding)
            x2_crop = min(frame_w, x2 + padding)
            y2_crop = min(frame_h, y2 + padding)

            person_crop = frame[y1_crop:y2_crop, x1_crop:x2_crop]
            
            if person_crop.size == 0:
                return None

            # Optimized resize
            original_height, original_width = person_crop.shape[:2]
            if max(original_height, original_width) > 416:
                scale = 416 / max(original_width, original_height)
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                person_crop = cv2.resize(person_crop, (new_width, new_height), 
                                       interpolation=cv2.INTER_LINEAR)

            # Single model inference with optimizations
            with torch.no_grad():
                # First pass: original image for vest detection
                results = self.detection_model(
                    person_crop,
                    conf=0.1,  # Keep original threshold
                    verbose=False,
                    imgsz=320,  # Reduced from 416 for speed
                    half=True if self.device == 'cuda' else False
                )

                vest_detected = False
                helmet_detected = False
                vest_bbox = None
                helmet_bbox = None

                # Process results
                if results and results[0].boxes:
                    for box in results[0].boxes:
                        box_cls = int(box.cls[0].item())
                        conf = float(box.conf[0])
                        
                        if box_cls == 1 and conf > 0.2:  # Reflective-Jacket
                            vest_detected = True
                            box_coords = box.xyxy[0].cpu().numpy().astype(int)
                            scale_x = (x2_crop - x1_crop) / person_crop.shape[1]
                            scale_y = (y2_crop - y1_crop) / person_crop.shape[0]
                            vest_bbox = [
                                int(x1_crop + box_coords[0] * scale_x),
                                int(y1_crop + box_coords[1] * scale_y),
                                int(x1_crop + box_coords[2] * scale_x),
                                int(y1_crop + box_coords[3] * scale_y)
                            ]
                        elif box_cls == 0 and conf > 0.4:  # Safety-Helmet
                            helmet_detected = True
                            box_coords = box.xyxy[0].cpu().numpy().astype(int)
                            scale_x = (x2_crop - x1_crop) / person_crop.shape[1]
                            scale_y = (y2_crop - y1_crop) / person_crop.shape[0]
                            helmet_bbox = [
                                int(x1_crop + box_coords[0] * scale_x),
                                int(y1_crop + box_coords[1] * scale_y),
                                int(x1_crop + box_coords[2] * scale_x),
                                int(y1_crop + box_coords[3] * scale_y)
                            ]

                # If helmet not detected in color, try grayscale
                if not helmet_detected:
                    gray_frame = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY)
                    person_crop_gray = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)
                    
                    results_gray = self.detection_model(
                        person_crop_gray,
                        conf=0.1,
                        verbose=False,
                        imgsz=320,
                        half=True if self.device == 'cuda' else False
                    )

                    if results_gray and results_gray[0].boxes:
                        for box in results_gray[0].boxes:
                            box_cls = int(box.cls[0].item())
                            conf = float(box.conf[0])
                            
                            if box_cls == 0 and conf > 0.6:  # Safety-Helmet
                                helmet_detected = True
                                box_coords = box.xyxy[0].cpu().numpy().astype(int)
                                scale_x = (x2_crop - x1_crop) / person_crop_gray.shape[1]
                                scale_y = (y2_crop - y1_crop) / person_crop_gray.shape[0]
                                helmet_bbox = [
                                    int(x1_crop + box_coords[0] * scale_x),
                                    int(y1_crop + box_coords[1] * scale_y),
                                    int(x1_crop + box_coords[2] * scale_x),
                                    int(y1_crop + box_coords[3] * scale_y)
                                ]
                                break

            # Determine status
            if helmet_detected and vest_detected:
                safety_status = "helmet_and_vest"
            elif helmet_detected:
                safety_status = "helmet_only"
            elif vest_detected:
                safety_status = "vest_only"
            else:
                safety_status = "no_protection"

            result = {
                'vest': {'detected': vest_detected, 'bbox': vest_bbox},
                'helmet': {'detected': helmet_detected, 'bbox': helmet_bbox},
                'status': safety_status
            }
            
            # Cache result with TTL
            self.detection_cache[cache_key] = result
            self.cache_ttl[cache_key] = current_time
            
            return result

        except Exception as e:
            print(f"[ERROR] detect_helmet_vest_head: {e}")
            return None

    def detect_shoes_optimized(self, frame, person_bbox):
        """Optimized shoes detection within person region"""
        # print("Optimized shoes detection within person region")
        try:
            
            x1, y1, x2, y2 = person_bbox
            height, width, _ = frame.shape

            # Extend detection area below person bbox
            if height > y2 + 30:  # Reduced from 50
                y2 = y2 + 30

            # Validate bbox
            if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0:
                return "false", None

            # Define shoe region (lower 30% of the extended bbox)
            shoe_region_start = int(y1 + (y2 - y1) * 0.7)
            shoe_region = frame[shoe_region_start:y2, x1:x2]

            if shoe_region.size == 0:
                return "false", None

            # Optimized shoes detection
            with torch.no_grad():
                shoes_results = self.model_shoes(
                    shoe_region, 
                    conf=0.1, 
                    verbose=False,
                    imgsz=320,  # Reduced from default for speed
                    half=True if self.device == 'cuda' else False
                )

            shoes_detected = "false"
            shoe_bbox = None

            if shoes_results and shoes_results[0].boxes:
                for box in shoes_results[0].boxes:
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])

                    if cls < len(self.model_shoes.names):
                        label = self.model_shoes.names[cls].lower()

                        if label == "safety_shoe" and conf > 0.3:
                            # print("✅ Shoes detected!")
                            shoes_detected = "shoes"
                            box_coords = box.xyxy[0].cpu().numpy().astype(int)
                            shoe_bbox = [
                                x1 + box_coords[0],
                                shoe_region_start + box_coords[1],
                                x1 + box_coords[2],
                                shoe_region_start + box_coords[3]
                            ]
                            return shoes_detected, shoe_bbox

            return shoes_detected, shoe_bbox

        except Exception as e:
            print(f"[ERROR] detect_shoes_optimized: {e}")
            return "false", None

    def should_run_detection(self, person_id, track_confidence):
        """Smart detection scheduling based on tracking confidence"""
        current_time = time.time()
        
        # Determine detection interval based on confidence
        if track_confidence > 0.7:
            interval = self.high_conf_interval
        else:
            interval = self.low_conf_interval
            
        # Check if it's time for detection
        if person_id not in self.detection_intervals:
            self.detection_intervals[person_id] = current_time
            return True
            
        if current_time - self.detection_intervals[person_id] >= interval:
            self.detection_intervals[person_id] = current_time
            return True
            
        return False

    def _flush_db_batch(self):
        """Flush database batch operations"""
        try:
            if not self.db_batch:
                return
                
            for entry in self.db_batch:
                self.db.insert_event(
                    entry['cam_id'],
                    entry['image'],
                    entry['helmet'],
                    entry['vest'],
                    entry['shoes']
                )
            
            # print(f"[DB] Flushed {len(self.db_batch)} entries")
            self.db_batch.clear()
            self.last_db_flush = time.time()
            
        except Exception as e:
            print(f"[ERROR] _flush_db_batch: {e}")

    def detection_process(self):
        """
        Optimized detection process:
        - Runs in a separate thread
        - Processes frames from frame_queue_to_store_detection
        - Deletes frames that are already processed & inserted into DB
        - Handles helmet, vest, shoes detection with caching
        """
        while self.frame_queue_to_store_detection:
            try:
                # Get next frame for detection
                item = self.frame_queue_to_store_detection.get(timeout=0.1)
                frame, x1, x2, y1, y2, person_id, cam_id = item

                start_time = time.time()
                with self.detection_thread_lock:
                    self.active_detection_threads += 1

                # Get person crop for detection
                y1_crop = max(0, y1 )
                y2_crop = min(frame.shape[0], y2 )
                person_cropped_image = frame[y1_crop:y2_crop, x1:x2]

                if person_cropped_image.size == 0:
                    self.frame_queue_to_store_detection.task_done()
                    continue

                # Detect helmet & vest
                safety_detection = self.detect_helmet_vest_head(frame, person_id, (x1, y1, x2, y2))
                vest_detected = safety_detection and safety_detection['vest']['detected']
                helmet_detected = safety_detection and safety_detection['helmet']['detected']

                # Detect shoes
                shoes_detected, shoe_bbox = self.detect_shoes_optimized(frame, (x1, y1, x2, y2))

                # Prepare DB insertion if needed
                needs_warning = not helmet_detected or not vest_detected or shoes_detected == "None"
                current_time = time.time()
                can_insert = True
                if person_id in self.inserted_person_ids:
                    if current_time - self.inserted_person_ids[person_id] < self.insertion_cooldown:
                        can_insert = False

                if needs_warning and can_insert:
                    try:
                        # Cleanup old person IDs
                        if len(self.inserted_person_ids) > 100:
                            old_entries = [pid for pid, ts in self.inserted_person_ids.items() if current_time - ts > 30.0]
                            for pid in old_entries:
                                del self.inserted_person_ids[pid]

                        # Resize & encode image for DB
                        person_cropped_image = cv2.resize(person_cropped_image, (300, 400))
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                        _, buffer = cv2.imencode('.jpg', person_cropped_image, encode_param)
                        encoded_image = base64.b64encode(buffer).decode('utf-8')

                        # DB entry
                        db_entry = {
                            'cam_id': cam_id,
                            'image': encoded_image,
                            'helmet': "Yes" if helmet_detected else "No",
                            'vest': "Yes" if vest_detected else "No",
                            'shoes': "Yes" if shoes_detected == "shoes" else "No",
                            'person_id': person_id
                        }

                        # Batch DB insertion
                        with self.db_lock:
                            self.db_batch.append(db_entry)
                            if len(self.db_batch) >= self.db_batch_size or current_time - self.last_db_flush > 2.0:
                                self._flush_db_batch()

                        # Mark as inserted
                        self.inserted_person_ids[person_id] = current_time

                    except Exception as e:
                        print(f"[ERROR] DB insertion failed for person {person_id}: {e}")

                # Mark this frame as done in queue
                self.frame_queue_to_store_detection.task_done()

                # Optional: Remove already processed frames to keep queue smooth
                with self.frame_queue_to_store_detection.mutex:
                    if len(self.frame_queue_to_store_detection.queue) > 0:
                        latest = self.frame_queue_to_store_detection.queue[-1]
                        self.frame_queue_to_store_detection.queue.clear()
                        self.frame_queue_to_store_detection.queue.append(latest)
                # with self.frame_queue_to_store_detection.mutex:
                #     self.frame_queue_to_store_detection.queue = [
                #         f for f in self.frame_queue_to_store_detection.queue
                #     ]

                end_time = time.time()
                # print(f"[DETECTION] Person {person_id} processed in {end_time - start_time:.3f}s")

            except queue.Empty:
                # No frames to process, just wait
                time.sleep(0.01)
                continue
            except Exception as e:
                print(f"[ERROR] detection_process: {e}")
            finally:
                with self.detection_thread_lock:
                    self.active_detection_threads = max(0, self.active_detection_threads - 1)

        
    

    def draw_detection_box(self, frame, bbox, label, color, confidence=None):
        """Draw detection box with label"""
        if bbox is None:
            return
            
        try:
            x1, y1, x2, y2 = bbox
            
            # Validate coordinates
            if x1 >= x2 or y1 >= y2:
                return
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Prepare label text
            if confidence:
                text = f"{label} ({confidence:.2f})"
            else:
                text = label
                
            # Draw label background
            # (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            # cv2.rectangle(frame, (x1, y1 - text_height - 5), (x1 + text_width, y1), color, -1)
            
            # # Draw label text
            # cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
        except Exception as e:
            print(f"[ERROR] draw_detection_box: {e}")

    def cleanup_cache(self, current_time):
        """Optimized cache cleanup"""
        try:
            if len(self.detection_cache) > 200:  # Cleanup threshold
                # Remove entries older than cache duration
                current_slot = int(current_time // self.cache_duration)
                expired_keys = []
                
                for key in list(self.detection_cache.keys()):
                    if '_' in key:
                        try:
                            key_slot = int(float(key.split('_')[-1]))
                            if current_slot - key_slot > 3:  # Keep recent cache
                                expired_keys.append(key)
                        except:
                            expired_keys.append(key)
                
                for key in expired_keys:
                    self.detection_cache.pop(key, None)
                    self.cache_ttl.pop(key, None)
                    
        except Exception as e:
            print(f"[ERROR] cleanup_cache: {e}")

    def get_sort_custom_id(self, sort_id):
        """Get or create custom ID for SORT tracking ID"""
        try:
            if sort_id not in self.track_id_mapping:
                self.track_id_mapping[sort_id] = self.custom_id_counter
                self.custom_id_counter += 1
                # print(f"[TRACK] New person assigned ID: {self.track_id_mapping[sort_id]}")
            return self.track_id_mapping[sort_id]
        except Exception as e:
            print(f"[ERROR] get_sort_custom_id: {e}")
            return sort_id

    def update_track_history(self, track_id, bbox, confidence):
        """Update track history for smoothing"""
        try:
            if track_id not in self.track_history:
                self.track_history[track_id] = []
            
            self.track_history[track_id].append({
                'bbox': bbox,
                'confidence': confidence,
                'timestamp': time.time()
            })
            
            # Keep only recent history (reduced for memory efficiency)
            if len(self.track_history[track_id]) > 8:
                self.track_history[track_id].pop(0)
                
        except Exception as e:
            print(f"[ERROR] update_track_history: {e}")

    def smooth_bbox(self, track_id, current_bbox):
        """Smooth bounding box using track history"""
        try:
            if track_id not in self.track_history or len(self.track_history[track_id]) < 2:
                return current_bbox
            
            history = self.track_history[track_id]
            recent_bboxes = [h['bbox'] for h in history[-3:]]  # Last 3 frames
            
            # Weighted moving average (more weight to recent frames)
            weights = [0.5, 0.3, 0.2] if len(recent_bboxes) == 3 else [0.6, 0.4] if len(recent_bboxes) == 2 else [1.0]
            
            x1_avg = sum([bbox[0] * w for bbox, w in zip(recent_bboxes, weights)])
            y1_avg = sum([bbox[1] * w for bbox, w in zip(recent_bboxes, weights)])
            x2_avg = sum([bbox[2] * w for bbox, w in zip(recent_bboxes, weights)])
            y2_avg = sum([bbox[3] * w for bbox, w in zip(recent_bboxes, weights)])
            
            return [int(x1_avg), int(y1_avg), int(x2_avg), int(y2_avg)]
            
        except Exception as e:
            print(f"[ERROR] smooth_bbox: {e}")
            return current_bbox

    def cleanup_tracks(self):
        """Clean up old tracks and mappings"""
        try:
            current_time = time.time()
            
            # Clean old track history (older than 5 seconds)
            tracks_to_remove = []
            for track_id, history in self.track_history.items():
                if history and current_time - history[-1]['timestamp'] > 5.0:
                    tracks_to_remove.append(track_id)
             
            for track_id in tracks_to_remove:
                if track_id in self.track_history:
                    del self.track_history[track_id]
                if track_id in self.track_id_mapping:
                    # print(f"[TRACK] Removed expired track ID: {self.track_id_mapping[track_id]}")
                    del self.track_id_mapping[track_id]
                    
        except Exception as e:
            print(f"[ERROR] cleanup_tracks: {e}")

    def get_fps(self):
        """Calculate FPS"""
        try:
            current_time = time.time()
            self.fps_counter += 1
            
            if current_time - self.fps_start_time >= 1.0:
                fps = self.fps_counter / (current_time - self.fps_start_time)
                self.fps_history.append(fps)
                if len(self.fps_history) > 10:
                    self.fps_history.pop(0)
                
                self.fps_counter = 0
                self.fps_start_time = current_time
                return fps
            
            return sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
            
        except Exception as e:
            print(f"[ERROR] get_fps: {e}")
            return 0

    def process(self):
        """Optimized real-time processing loop"""
        try:
            # print("[INFO] Starting frame processing...")

            # [UPDATED] Store last fully processed frame per camera
            if not hasattr(self, 'latest_frames'):
                self.latest_frames = {}  # key: cam_id, value: frame
                self.latest_frame_lock = threading.Lock()

            while self.running:
                try:
                    # [GET FRAME]
                    try:
                        cam_id, frame = self.frame_queue.get(timeout=0.0001)
                        show_queue[cam_id] = queue.Queue(maxsize=100)
                        self.consecutive_empty_frames = 0
                    except queue.Empty:
                        self.consecutive_empty_frames += 1
                        if self.consecutive_empty_frames >= self.max_empty_frames:
                            print("[INFO] No more frames - video ended")
                        continue
                    except Exception as e:
                        print(f"[ERROR] Frame queue error: {e}")
                        break

                    if frame is None:
                        break

                    current_time = time.time()
                    self.frame_counter += 1

                    show_frame = frame.copy()

                    # [UPDATED] Detection + Tracking
                    try:
                        results = self.tracking_model.predict(
                            source=frame,
                            conf=0.3,
                            iou=0.7,
                            classes=[0],
                            verbose=False,
                            imgsz=320
                        )

                        boxes = results[0].boxes
                        detections = []

                        if boxes is not None and boxes.xyxy is not None:
                            coords = boxes.xyxy.cpu().numpy()
                            confs = boxes.conf.cpu().numpy()
                            clss = boxes.cls.cpu().numpy().astype(int)

                            for i, cls_id in enumerate(clss):
                                x1, y1, x2, y2 = coords[i]
                                if (x2 - x1) > self.min_box_size and (y2 - y1) > self.min_box_size:
                                    detections.append([x1, y1, x2, y2, confs[i]])

                        if len(detections) > 0:
                            detections_np = np.array(detections)
                            tracks = self.sort_tracker.update(detections_np)
                        else:
                            tracks = self.sort_tracker.update(np.empty((0, 5)))

                        for track in tracks:
                            x1, y1, x2, y2, sort_id = map(int, track)

                            person_id = self.get_sort_custom_id(sort_id)

                            track_confidence = 0.2
                            for det in detections:
                                det_x1, det_y1, det_x2, det_y2, det_conf = det
                                if (abs(det_x1 - x1) < 20 and abs(det_y1 - y1) < 20 and
                                    abs(det_x2 - x2) < 20 and abs(det_y2 - y2) < 20):
                                    track_confidence = det_conf
                                    break

                            self.update_track_history(sort_id, [x1, y1, x2, y2], track_confidence)
                            smoothed_bbox = self.smooth_bbox(sort_id, [x1, y1, x2, y2])
                            x1, y1, x2, y2 = smoothed_bbox

                            frame_h, frame_w = frame.shape[:2]
                            x1 = max(0, min(x1, frame_w - 1))
                            y1 = max(0, min(y1, frame_h - 1))
                            x2 = max(x1 + 1, min(x2, frame_w))
                            y2 = max(y1 + 1, min(y2, frame_h))
                            # y2 += 20
                            # y1 -= 10
                            
                            cv2.rectangle(show_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            cv2.putText(show_frame, f"ID: {person_id}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 3)
                            # with self.latest_frame_lock:
                            #  self.latest_frames[cam_id] = show_frame

                            self.frame_queue_to_store_detection.put((frame, x1, x2, y1, y2, person_id, cam_id))
                            
                            # if (self.latest_frame_lock):
                            #         frame_to_show = self.latest_frames.get(cam_id)

                            # while frame_queue_to_show.full():
                            #         try:
                            #             frame_queue_to_show.get_nowait()  # Remove the oldest frame
                            #         except queue.Empty:
                            #             break  # 
                                        
                            
                           
                            

                        

                            # [SPAWN DETECTION THREAD IF NEEDED]
                            # with self.detection_thread_lock:
                            #     can_start_thread = self.active_detection_threads < self.max_detection_threads

                            # if can_start_thread:
                                # detection_thread = threading.Thread(
                                #     target=self.detection_process,
                                #     args=(frame, x1, x2, y1, y2, person_id, cam_id),
                                #     daemon=True
                                # )
                                # detection_thread.start()

                    except Exception as e:
                        print(f"[ERROR] SORT tracking error: {e}")

                    # [UPDATED] Update shared processed frame (thread-safe)
                    with self.latest_frame_lock:
                        self.latest_frames[cam_id] = show_frame

                    # [UPDATED] Display logic moved outside.
                    try:
                        with self.latest_frame_lock:
                            frame_to_show = self.latest_frames.get(cam_id)

                        while frame_queue_to_show.full():
                            try:
                                frame_queue_to_show.get_nowait()  # Remove the oldest frame
                            except queue.Empty:
                                break  # Shouldn't happen, but just in case
                        # if frame is not None:
                        #  cv2.imshow(f"Camera {cam_id}", frame)

                        # if cv2.waitKey(1) & 0xFF == ord('q'):
                        #  break

                        frame_queue_to_show.put((cam_id, frame_to_show), timeout=0.001)
                        # self.frame_queue_to_store_detection.put((frame, x1, x2, y1, y2, person_id, cam_id))
                    except queue.Full:
                        pass

                    self.cleanup_cache(current_time)

                    try:
                        self.frame_queue.task_done()
                    except:
                        pass

                except KeyboardInterrupt:
                    print("[INFO] Interrupted by user")
                    break
                except Exception as e:
                    
                    print(f"[ERROR] Frame processing: {e}")
                    time.sleep(0.01)

        except Exception as e:
            print(f"[ERROR] Processing loop crashed: {e}")

    def stop(self):
        """Stop processing and cleanup"""
        # print("[INFO] Stopping frame processor...")
        self.running = False

    
        cv2.destroyAllWindows()

    def close(self):
        """Close all resources"""
        self.running = False

        
        try:
            self.stop()
            if hasattr(self, 'db'):
                self.db.close()
        except Exception as e:
            print(f"[ERROR] close: {e}")


def create_frame_processor(frame_queue,  person_crop_queue):
    """Create the optimized frame processor"""
    return FrameProcessor(frame_queue,  person_crop_queue)