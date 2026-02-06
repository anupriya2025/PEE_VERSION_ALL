# import cv2
# from ultralytics import YOLO

# # =============================
# # CONFIG
# # =============================
# RTSP_URL = "rtsp://admin:Admin@123@10.30.30.49/1"  # <-- replace this
# person_model = YOLO("yolo11m.pt")

# # =============================
# # LOAD MODEL
# # =============================


# # =============================
# # OPEN RTSP STREAM
# # =============================
# cap = cv2.VideoCapture(RTSP_URL)

# if not cap.isOpened():
#     print("Error: Cannot open RTSP stream")
#     exit()

# # =============================
# # PROCESS STREAM
# # =============================
# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("Failed to grab frame")
#         break

#     # YOLOv8 tracking (ByteTrack)
#     results = person_model.track(
#         frame,
#         persist=True,     # keep IDs across frames
#         classes=[0],      # class 0 = person
#         conf=0.5,
#         tracker="bytetrack.yaml"
#     )

#     # Draw results
#     if results[0].boxes.id is not None:
#         boxes = results[0].boxes.xyxy.cpu().numpy()
#         ids = results[0].boxes.id.cpu().numpy()

#         for box, track_id in zip(boxes, ids):
#             x1, y1, x2, y2 = map(int, box)

#             # Draw bounding box
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

#             # Draw ID
#             cv2.putText(
#                 frame,
#                 f"Person ID: {int(track_id)}",
#                 (x1, y1 - 10),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.6,
#                 (0, 255, 0),
#                 2
#             )

#     cv2.imshow("YOLOv8 Person Tracking", frame)

#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break

# # =============================
# # CLEANUP
# # =============================
# cap.release()
# cv2.destroyAllWindows()
