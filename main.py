import logging
import multiprocessing
import threading
from queue import Queue
import time

# from gui.GUI_Starter import _main
from config import ConfigLoader
from core.Stream import VideoStream
from core.Analytics import FrameProcessor
from core.api import create_api
from core.database import EventDatabase
# from core.ppe_detection_module import PPEDetectionModule
from core.video_record_handler import TrackVideoManager
from  logger import LoggerUtility
import sys

cam_id=0


def start_frame_processor(processor):
    try: 
        processor.process()
    finally:
        processor.close()


def main():
   
    sources=[]
    db = EventDatabase()
    cameras = db.fetch_Camera_deatils()
    db.cleanup_Retension_data()

    # prev_ids_data= db.fetch_last_event_ids()
    # if not  prev_ids_data:
    #     prev_ids_data=1


    

    camera_info = {}
    cfg = ConfigLoader()
    frame_lock=threading.Lock()
    obj_logger=LoggerUtility()
    obj_logger._log_system_info()
    logger=obj_logger.get_logger(__name__)
            


    for cam_id, cam_name, url in cameras:
        sources.append(url)
        camera_info[cam_id] = {
            "id": cam_id,
            "name": cam_name,
            "url": url
        }

  
    camera_queues = {}
    stream_threads = []
    no_of_cam=0
    for cam_id, cam_name,src in cameras:
      

        camera_queues[cam_id] = Queue(maxsize=int(cfg.get("Main.maxsize", "100")))

        stream = VideoStream(
            sources=[src],
            frame_queue=camera_queues[cam_id],
            camera_id=cam_id
        )
        t = threading.Thread(target=stream.start, daemon=True)
        t.start()
        stream_threads.append((stream, t))

   
     

    # Start processors
    # obj_ppe_detector_class = PPEDetectionModule(db.camera_ppe_policy)
    
    processor_threads = []
    for cam_id, cam_queue in camera_queues.items():
        # last_id = 0  
        # for i in prev_ids_data:
        #     if cam_id == i["camera_id"]:
        #         last_id = i["event_id"]
        #         break
        processor = FrameProcessor(
            cam_queue,
            db,
           
            # int(last_id),
            frame_lock=frame_lock
        )
        t = threading.Thread(target=start_frame_processor, args=(processor,), daemon=True)
        t.start()
        processor_threads.append((processor, t))
    
    # obj_ppe_detector_class.start_detection_thread()
 
  

    # # # Start API
    obj_video_recorder= TrackVideoManager(
                                        base_folder=r"E:\PPE_TEMP_FRAMES",
                                        output_folder=r"E:\Ppe_Events\PPE_VIDEOS",
                                        fps=10,
                                        max_age_hours=24,
                                        cleanup_interval=120,  # Memory cleanup every 30 minutes
                                        scan_interval=2,  # Check for new files every 2 seconds
                                        min_frames_for_video=1,  # Minimum frames to create video
                                        frame_retention_minutes=5,  # Keep frames for 10 minutes after processing
                                        min_video_duration=1, max_video_duration=400
                                          )


    try:
        for _, thread in processor_threads:
            thread.join()
    except KeyboardInterrupt:
        hold_on_error()
        logger.exception("\n[INFO] Shutting down gracefully...")
    finally:
        for processor, _ in processor_threads:
            
            processor.close()
        for stream, _ in stream_threads:
            stream.stop()

import sys
import traceback

def hold_on_error():
   
    traceback.print_exc()
    input("\nPress ENTER to exit...")  # stops auto-close


if __name__ == "__main__":
    multiprocessing.freeze_support()   #  REQUIRED FOR EXE
    main()

