
import logging
import threading
from queue import Queue
import time


from gui.GUI_Starter import _main
from core.Stream import VideoStream
from core.Analytics import FrameProcessor
from core.api import create_api
# from core.live_feed_new import LiveFeedMonitor
import sys
from core.events import EventFeedMonitor
from core.login import LoginPage
print(sys.executable)
def gui_Call():
 run=_main()
# lg = LoginPage()



cam_id=0

# def enter_login():
#     lg.run()  
    
# def event_show():   
#     # pass 
#   ev=EventFeedMonitor() 


def call_live_feed(Camera_no):
    pass
    # app = LiveFeedMonitor(Camera_no)
    # app.run()


def start_api_server():
    app = create_api()
    app.run(debug=False, port=5000, use_reloader=False)  # Disable reloader in thread


def start_frame_processor(processor):
    try:
        processor.process()
    finally:
        processor.close()


def main():
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s',
        level=logging.INFO 
    )

    # Show login first
    # enter_login()  # Blocks here until user closes login window

    # After successful login, continue with rest of the code
    sources = [
        # "rtsp://admin:abc@1234@10.30.30.47/1",
        # "rtsp://admin:Admin@123@10.30.30.49/1",
        # "rtsp://admin:Admin@123@10.30.30.49/1",
        # "rtsp://admin:Admin@123@10.30.30.49/1",
        # "rtsp://admin:Admin@123@10.30.30.49/1",
        # "rtsp://admin:123456@10.30.30.52/sub",
        # "rtsp://admin:Admin@123@10.30.30.49/1",
        # "rtsp://admin:123456@10.30.30.52/sub",
        # "rtsp://admin:Admin@123@10.30.30.49/2",
        "resource/video/HD10.mp4",
        "resource/video/2024.mp4",
        "rtsp://admin:Admin@123@10.30.30.49/1",
        "rtsp://admin:abc@1234@10.30.30.46/1",
        # "rtsp://admin:123456@10.30.30.52/sub/1",
        # "rtsp://admin:abc@1234@10.30.30.47/1",
    ]
    
    Camera_no = len(sources)
    person_crop_queue = Queue(maxsize=30)
    camera_queues = {}
   

    # Start video stream threads
    grab_fps = 40
    stream_threads = []
    for i, src in enumerate(sources):
        cam_id = i + 1
        camera_queues[cam_id] = Queue(maxsize=100)
        
        stream = VideoStream(
            sources=[src],
            frame_queue=camera_queues[cam_id],
            fps_limit=grab_fps,
            camera_id=cam_id
        )
        t = threading.Thread(target=stream.start, daemon=True)
        t.start()
        stream_threads.append((stream, t))

   
    

    # Start processors
    processor_threads = []
    for cam_id, cam_queue in camera_queues.items():
        processor = FrameProcessor(
            frame_queue=cam_queue,
            person_crop_queue=person_crop_queue
        )
        t = threading.Thread(target=start_frame_processor, args=(processor,), daemon=True)
        t.start()
        processor_threads.append((processor, t))
    gui_Call()

    # Start live feed
    # def enter_login():
    #  lg.run()  
    # enter_login()
  
    live_thread = threading.Thread(target=lambda: call_live_feed(Camera_no), daemon=True)
    # if(lg.validate_login):
    live_thread.start()

    # Start API
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    try:
        for _, thread in processor_threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down gracefully...")
    finally:
        for processor, _ in processor_threads:
            
            processor.close()
        for stream, _ in stream_threads:
            stream.stop()

        # Do NOT start live_thread again here — it's already started

if __name__ == "__main__":
    
    main()
   
# z