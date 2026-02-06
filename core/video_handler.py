import os
import threading
import cv2
import av
import time
import shutil
from pathlib import Path


def frames_to_ts_video_daemon(
    parent_folder_path: str,
    video_dir: str,
    min_frames: int,
    fps: int,
    logger=None
):
    while True:
        try:
            parent_folder = Path(parent_folder_path)

            if not parent_folder.exists() or not parent_folder.is_dir():
                return

            for child_folder in parent_folder.iterdir():
                if not child_folder.is_dir():
                    continue

                # 🔹 Extract cam_id from folder name: CAM47_Camera_3_23014
                parts = child_folder.name.split("_")
                cam_id = parts[2] if len(parts) >= 3 else "unknown"
                folder_name= parts[0]+"_"+parts[1]
                event_id= parts[3]
                image_files = sorted(
                    str(p) for p in child_folder.glob("*.jpg")
                )

                if len(image_files) < 10:
                    continue

                first_img = None
                for p in image_files:
                    img = cv2.imread(p)
                    if img is not None:
                        first_img = img
                        break

                if first_img is None:
                    continue

                h, w, _ = first_img.shape

                date_folder = time.strftime("%d-%m-%Y")

                relative_folder = os.path.join(date_folder, folder_name)
                camera_folder = os.path.join(video_dir, relative_folder)
                os.makedirs(camera_folder, exist_ok=True)

                video_filename = f"{cam_id}_{event_id}.ts"
                video_path = os.path.join(camera_folder, video_filename)

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
                    frame = cv2.imread(img_path)
                    if frame is None:
                        continue

                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    video_frame = av.VideoFrame.from_ndarray(
                        frame_rgb, format="rgb24"
                    )

                    for packet in stream.encode(video_frame):
                        container.mux(packet)

                    frames_written += 1

                # Flush encoder
                for packet in stream.encode(None):
                    container.mux(packet)

                container.close()
                time.sleep(0.1)  # Windows file lock release

                if frames_written > 0 and os.path.exists(video_path):
                    shutil.rmtree(child_folder)
                   
                    # print(
                    #         f"TS video created | cam_id={cam_id} | {video_path}"
                    #     )
                else:
                    if os.path.exists(video_path):
                        os.remove(video_path)

        except Exception as e:
            if logger:
                logger.error(f"[TS VIDEO ERROR] {e}")
            else:
                pass
                # print(f"[TS VIDEO ERROR] {e}")
        time.sleep(1)



def start_daemon_thread(
    folder_path: str,
    output_video_path: str,
    min_frames: int,
    fps: int = 30
):
    
    thread = threading.Thread(
    target=frames_to_ts_video_daemon,
    args=(
       folder_path,
        output_video_path,
        min_frames,   # min_frames
        fps     # fps
    ),
    daemon=True
)
    thread.start()