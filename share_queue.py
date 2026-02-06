import queue
frame_queue_to_show= queue.Queue(maxsize=10)
raw_frames_data_for_toon_queue= queue.Queue(maxsize=10)
# frame_queue_to_show_live=queue.Queue(maxsize=10)
frame_queue_to_show_live = {}
pid_last_seen = {}
inactive_ids_record = []
post_buffer_frames = []


def convert_status_to_msg(status):
    helmet = status[0]
    vest= status[1]
    shoes = status[2]
    
    if  helmet and  vest and shoes:
        safety_status = "Safe"
    else:
        if not helmet and not  vest and  not shoes :
            safety_status = "No Protection"
        if helmet and not vest:
            safety_status = "Only Helmet"
        if not helmet and vest:
             safety_status = "Only Vest Detected"
        else:
            safety_status = "No Protection"
    
    return safety_status