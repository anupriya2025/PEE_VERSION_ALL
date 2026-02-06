# import queue
# import threading
# import time
# import cv2
# import numpy as np
# import torch
# from ultralytics import YOLO
# from config import ConfigLoader


# class PPEDetectionModule:
#     _instance = None
#     _lock = threading.Lock()  # for thread-safe singleton

#     def __new__(cls, *args, **kwargs):
#         if cls._instance is None:
#             with cls._lock:
#                 if cls._instance is None:
#                     cls._instance = super(PPEDetectionModule, cls).__new__(cls)
#         return cls._instance

#     def __init__(self, policy_data=None):
#         # Prevent re-initialization
#         if hasattr(self, "_initialized") and self._initialized:
#             return

#         self._initialized = True

#         self.policy_tabel = policy_data
#         self.stop_signal = threading.Event()
#         self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
#         self.cfg = ConfigLoader()
#         path = self.cfg.get("MODEL.helmet_model_path")
#         self.head_helmet_model = YOLO(path)
#         if self.device=="cuda":
#             self.head_helmet_model.fuse()
#             self.head_helmet_model.to('cuda')
#             self.head_helmet_model.half()
                
#         self.ppe_detection_input_queue = queue.Queue(maxsize=60)
#         self.thread = None
#         self.start_detection_thread()

#     def start_detection_thread(self):
#         self.thread = threading.Thread(target=self.detectAndUpdatePPEStatus, daemon=True)
#         self.thread.start()

#     def detectAndUpdatePPEStatus(self):
#         while not self.stop_signal.is_set():
#             try:
#                 data = self.ppe_detection_input_queue.get(timeout=0.1)
#                 frame, person_id, bbox, cam_id, conf, person_detections= data
#                 x1, y1, x2, y2 = bbox
#                 if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0:
#                     continue

#                 policy = self.policy_tabel.get(cam_id, {})  # {'no helmet':1,'no vest':0}
            

#                 frame_h, frame_w = frame.shape[:2]
#                 # padding = int(self.cfg.get("PPE_DETECTION.padding", 30))
#                 padding=0

#                 x1_crop = max(0, x1 - padding)
#                 y1_crop = max(0, y1 - padding)
#                 x2_crop = min(frame_w, x2 + padding)
#                 y2_crop = min(frame_h, y2 + padding)

#                 person_crop = frame[y1_crop:y2_crop, x1_crop:x2_crop].copy()
                
#                 if person_crop.size == 0:
#                     continue
#                 detection = person_detections.get(person_id)
#                 if detection:
#                     time_gaph_needed = 2
#                     last_detection_time = detection["detected_time"]
#                     if time.time()- last_detection_time <= time_gaph_needed:
#                         continue
#                 with torch.no_grad():
#                     results = self.head_helmet_model(
#                         person_crop,
#                         conf=float(self.cfg.get("PPE_DETECTION.conf_threshold", 0.1)),
#                         iou=float(self.cfg.get("PPE_DETECTION.iou_threshold", 0.4)),
#                         verbose=False,
#                         imgsz=int(self.cfg.get("PPE_DETECTION.img_size", "416")),
#                         half=True if self.device == 'cuda' else False
#                     )
#                     helmet_detected = False
#                     vest_detected = False
#                     head_detected = False
#                     helmet_color = "Unknown"
#                     detection_boxes = []

#                     helmet_conf = float(self.cfg.get("PPE_DETECTION.helmet_conf", 0.6))
#                     vest_conf = float(self.cfg.get("PPE_DETECTION.vest_conf", 0.1))
#                     head_conf = float(self.cfg.get("PPE_DETECTION.head_conf", 0.2))
                    
#                     helmet_boxes = []
#                     head_boxes = []

#                     if results and results[0].boxes is not None:
#                         boxes = results[0].boxes
#                         coords = boxes.xyxy.cpu().numpy()
#                         confs = boxes.conf.cpu().numpy()
#                         clss = boxes.cls.cpu().numpy().astype(int)

#                         # -------------------------------------------------------
#                         # CLASSIFICATION: Collect helmet boxes + head boxes
#                         # -------------------------------------------------------

#                         for i, cls_id in enumerate(clss):
#                             conf = confs[i]
#                             box_coords = coords[i].astype(int)

#                             bx1, by1, bx2, by2 = box_coords

#                             # Helmet Box (class = 0)
#                             if cls_id == 0 and conf > helmet_conf:
#                                 helmet_color = self._extract_helmet_color(person_crop, box_coords)
#                                 helmet_detected=True
#                                 if helmet_color=='Red' or helmet_color=='Blue' or helmet_color=='Black':
#                                     helmet_detected = False
#                                 helmet_boxes.append((box_coords, conf))
                                

#                             # Vest Box (class = 1)
#                             elif cls_id == 1 and conf > vest_conf:
                            
#                                 if policy.get('no vest', 0) == 1:
#                                     vest_detected = True

#                             # Head Box (class = 2)
#                             elif cls_id == 2 and conf > head_conf:
                            
#                                 head_boxes.append((box_coords, conf))
#                                 head_detected = True
#                     # -------------------------------------------------------
#                     # MATCH HELMET TO HEAD ✔️
#                     # -------------------------------------------------------
#                     correct_helmet_box = None

#                     if head_boxes and helmet_boxes:
#                         hx1, hy1, hx2, hy2 = head_boxes[0][0]
#                         head_center = ((hx1 + hx2) // 2, (hy1 + hy2) // 2)

#                         min_distance = float("inf")

#                         for hb, hconf in helmet_boxes:
#                             bx1, by1, bx2, by2 = hb
#                             helmet_center = ((bx1 + bx2) // 2, (by1 + by2) // 2)

#                             distance = ((helmet_center[0] - head_center[0]) ** 2 +
#                                         (helmet_center[1] - head_center[1]) ** 2) ** 0.5

#                             # Helmet must be above or touching the head
#                             if by2 <= hy2 + 25:  # small tolerance
#                                 if distance < min_distance:
#                                     min_distance = distance
#                                     correct_helmet_box = hb

#                         # Assign final helmet
#                         if correct_helmet_box is not None and policy.get('no helmet', 0) == 1:
#                             helmet_detected = True
#                             helmet_color = self._extract_helmet_color(person_crop, correct_helmet_box)
#                             if helmet_color=='Red' or helmet_color=='Blue' or helmet_color=='Black':
#                                 helmet_detected = False

#                 if torch.cuda.is_available():
#                     torch.cuda.empty_cache()

        
#                 helmet_required = policy.get('no helmet', 0) == 1
#                 vest_required = policy.get('no vest', 0) == 1

#                 needs_warning = False
#                 safety_status = "Safe"

#                 if not helmet_required and not vest_required:
#                     safety_status = "Safe (No PPE Required)"
#                 else:
#                     if helmet_required and vest_required:
#                         if helmet_detected and vest_detected:
#                             safety_status = "Safe"
#                         elif helmet_detected and not vest_detected:
#                             safety_status = "Only Helmet"
#                             needs_warning = True
#                         elif not helmet_detected and vest_detected:
#                             safety_status = "Only Vest Detected"
#                             needs_warning = True
#                         else:
#                             safety_status = "No Protection"
#                             needs_warning = True

#                     elif helmet_required and not vest_required:
#                         if helmet_detected:
#                             safety_status = "Helmet Detected"
#                         else:
#                             safety_status = "No Helmet"
#                             needs_warning = True

#                     elif vest_required and not helmet_required:
#                         if vest_detected:
#                             safety_status = "Vest Detected"
#                         else:
#                             safety_status = "No Vest"
#                             needs_warning = True
                            
#                 detection_result = {
#                     'helmet': helmet_detected,
#                     'vest': vest_detected,
#                     'head': head_detected,
#                     'helmet_color': helmet_color,
#                     'safety_status': safety_status,
#                     'needs_warning': needs_warning,
#                     'detection_boxes': detection_boxes,
#                     'detected_time': time.time(),
#                     'person_id': person_id,
#                     'confidence_scores': {
#                         'helmet': max([confs[i] for i in range(len(clss)) if clss[i] == 0], default=0.0),
#                         'vest': max([confs[i] for i in range(len(clss)) if clss[i] == 1], default=0.0),
#                         'head': max([confs[i] for i in range(len(clss)) if clss[i] == 2], default=0.0)
#                     }
#                 }

#                 person_detections[person_id] = detection_result
#             except Exception as e:
#                 pass
    
#     def _extract_helmet_color(self, helmet_crop, box_coords):
#         try:
#             i=0
#             x1, y1, x2, y2 = map(int, box_coords)
#             cropped = helmet_crop[y1:y2, x1:x2]
#             i=+1

#             if cropped.size == 0:
#                 return None

#             hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)

#             color_ranges = {
#                 'Red': [(np.array([0, 120, 70]), np.array([10, 255, 255])),
#                         (np.array([170, 120, 70]), np.array([180, 255, 255]))],
#                 'Yellow': [(np.array([20, 100, 100]), np.array([30, 255, 255])),
#                           (np.array([10, 100, 20]), np.array([25, 255, 255]))],
#                 'Blue': [(np.array([100, 150, 0]), np.array([140, 255, 255]))],
#                 'Green': [(np.array([40, 70, 70]), np.array([80, 255, 255]))],
#                 'White': [(np.array([0, 0, 200]), np.array([180, 30, 255]))],
#                 'Black': [(np.array([0, 0, 0]), np.array([180, 255, 50]))]
#             }

#             color_counts = {}
#             for color, ranges in color_ranges.items():
#                 mask_total = None
#                 for lower, upper in ranges:
#                     mask = cv2.inRange(hsv, lower, upper)
#                     if mask_total is None:
#                         mask_total = mask
#                     else:
#                         mask_total = cv2.bitwise_or(mask_total, mask)
#                 color_counts[color] = cv2.countNonZero(mask_total)

#             dominant_color = max(color_counts, key=color_counts.get)
       
#             return dominant_color

#         except Exception as e:
#             # self.logger.exception(f"Error in _extract_helmet_color: {e}")
#             return None
    
#     def stop(self):
#         self.stop_signal.set()
#         del self.thread

#___________________________________________________________________________

# import cv2
# import torch
# from ultralytics import YOLO

# # ---------------- CONFIG ----------------
# VIDEO_PATH = "E:\\DEV_DRIVE\\PPE_HELVES\\C071125_00.ts"   # <-- your video path
# HELMET_MODEL_PATH = "HelmetHeadDataset.pt"


# CONF_THRESHOLD = 0.2
# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# print(f"Using device: {DEVICE}")
# # ----------------------------------------

# # Load models on GPU
# helmet_model = YOLO(HELMET_MODEL_PATH).to(DEVICE)


# # Open video
# cap = cv2.VideoCapture(VIDEO_PATH)

# if not cap.isOpened():
#     print("❌ Error opening video")
#     exit()

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break
#     # frame = cv2.resize(frame,(960,640))

#     # Helmet detection
#     helmet_results = helmet_model(
#         frame,
#         conf=CONF_THRESHOLD,
#         device=DEVICE,
#         imgsz=1280,
#         verbose=False
#     )
    

#     # Draw helmet boxes (Blue)
#     for r in helmet_results[0]:
#         for box in r.boxes:
#             x1, y1, x2, y2 = map(int, box.xyxy[0])
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
#             cv2.putText(
#                 frame, "Helmet",
#                 (x1, y1 - 10),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.6,
#                 (255, 0, 0), 2
#             )


#     cv2.imshow("Helmet (GPU)", frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()


# import cv2
# import torch
# import time
# from ultralytics import YOLO

# # ---------------- CONFIG ----------------
# VIDEO_PATH = "E:\\DEV_DRIVE\\PPE_HELVES\\C085832_00.ts"
# OUTPUT_PATH = "record_2.mp4"

# PERSON_MODEL = "yolo11m.pt"   # use yolo11n.pt for speed
# PERSON_CONF = 0.01
# PERSON_IOU = 0.7
# IMGSZ = 1280                 # keep <= 640 for speed

# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# print("Using device:", DEVICE)
# # ----------------------------------------

# # Load model
# person_model = YOLO(PERSON_MODEL).to(DEVICE)

# # Open video
# cap = cv2.VideoCapture(VIDEO_PATH)
# if not cap.isOpened():
#     print("❌ Cannot open video")
#     exit()

# # Get video properties (IMPORTANT)
# fps = cap.get(cv2.CAP_PROP_FPS)
# width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# # Video writer (MATCH SIZE)
# fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# out = cv2.VideoWriter(
#     OUTPUT_PATH,
#     fourcc,
#     fps,
#     (width, height)
# )

# counter = 0

# # ---------------- MAIN LOOP ----------------
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     counter += 1
#     display_frame = frame.copy()

#     # Run detection every 4th frame
#     if counter % 1 == 0:
#         with torch.no_grad():
#             results = person_model.track(
#                 source=frame,
#                 conf=PERSON_CONF,
#                 iou=PERSON_IOU,
#                 imgsz=IMGSZ,
#                 persist=True,
#                 verbose=False
#             )

#         if results and results[0].boxes is not None:
#             for box in results[0].boxes:
#                 if int(box.cls.item()) != 0:
#                     continue

#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 track_id = int(box.id.item()) if box.id is not None else -1

#                 cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                 cv2.putText(
#                     display_frame,
#                     f"Helmet",
#                     (x1, y1 - 8),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     0.6,
#                     (0, 255, 0),
#                     2
#                 )

#     # ✅ WRITE EVERY FRAME
#     out.write(display_frame)

#     # ✅ SHOW EVERY FRAME
#     cv2.imshow("Person Detection (Recording)", display_frame)
#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break

# # ---------------- CLEANUP ----------------
# cap.release()
# out.release()
# cv2.destroyAllWindows()

# print("✅ Video saved as:", OUTPUT_PATH)



# import cv2
# import torch
# import time
# from ultralytics import YOLO

# # ---------------- CONFIG ----------------
# VIDEO_PATH = "E:\\DEV_DRIVE\\PPE_HELVES\\C095206_00.ts"
# OUTPUT_PATH = "output_person_detection.mp4"

# PERSON_MODEL = "yolo11m.pt"   # change to yolo11n.pt for faster FPS
# PERSON_CONF = 0.25
# PERSON_IOU = 0.5
# IMGSZ = 640                  # DO NOT use >1280

# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# print("Using device:", DEVICE)
# # ----------------------------------------

# # Load model
# person_model = YOLO(PERSON_MODEL).to(DEVICE)

# # Open video
# cap = cv2.VideoCapture(VIDEO_PATH)
# if not cap.isOpened():
#     print("❌ Failed to open video")
#     exit()

# # Video properties
# fps = cap.get(cv2.CAP_PROP_FPS)
# width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# # Video writer
# fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# out = cv2.VideoWriter(
#     OUTPUT_PATH,
#     fourcc,
#     fps,
#     (width, height)
# )

# counter = 0

# # ---------------- MAIN LOOP ----------------
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     counter += 1
#     display_frame = frame.copy()

#     # Run detection every 4th frame
#     if counter % 4 == 0:
#         with torch.no_grad():
#             results = person_model.track(
#                 source=frame,
#                 conf=PERSON_CONF,
#                 iou=PERSON_IOU,
#                 imgsz=IMGSZ,
#                 persist=True,
#                 verbose=False
#             )

#         if results and results[0].boxes is not None:
#             for box in results[0].boxes:
#                 if int(box.cls.item()) != 0:
#                     continue

#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 track_id = int(box.id.item()) if box.id is not None else -1

#                 cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                 cv2.putText(
#                     display_frame,
#                     f"Person ID: {track_id}",
#                     (x1, y1 - 8),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     0.6,
#                     (0, 255, 0),
#                     2
#                 )

#     # WRITE EVERY FRAME (IMPORTANT)
#     out.write(display_frame)

#     # SHOW
#     cv2.imshow("Person Detection (Recorded)", display_frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # ---------------- CLEANUP ----------------
# cap.release()
# out.release()
# cv2.destroyAllWindows()

# print("✅ Video saved as:", OUTPUT_PATH)
