# import io
# import platform
# import customtkinter as ctk
# import tkinter as tk
# from tkinter import ttk
# from PIL import Image, ImageTk
# import cv2
# import datetime
# import threading
# import time
# import numpy as np
# from core.database import EventDatabase
# from share_queue import frame_queue_to_show
# import requests
# import base64
# from io import BytesIO
# from PIL import Image
# from core.Analytics import FrameProcessor
# # from core.events import EventFeedMonitor
# import queue
# import math

# # Set appearance mode and color theme
# ctk.set_appearance_mode("light")
# ctk.set_default_color_theme("blue")

# class LiveFeedMonitor:
#     def __init__(self, Camera_no=8):
#         # Initialize main window
#         print(f"Initializing with {Camera_no} cameras")
#         self.root = ctk.CTk()
#         self.history_button = []
#         self.root.title("Live Event - Multi Camera Surveillance")
#         self.root.geometry("1900x1000")
#         self.root.minsize(1900, 1000)
#         if platform.system() == "Windows":
#             self.root.state('zoomed')
#         else:
#             self.root.attributes('-zoomed', True)

#         # Configure root grid
#         self.root.grid_columnconfigure(0, weight=2)
#         self.root.grid_rowconfigure(0, weight=1)
        
#         # Video capture variables
#         self.cap = None
#         self.video_thread = None
#         self.is_running = False
#         self.obj_db = EventDatabase()
#         self.events = []
        
#         # Surveillance system variables
#         self.root_width = 1920
#         self.root_height = 1080
#         self.main_width = int(self.root_width * 0.95)
#         self.main_height = int(self.root_height * 0.95)
#         self.expanded_camera = None
#         self.maximize_buttons = []
#         self.minimize_button = None
#         self.details_frames = []
        
#         # Multi-camera support - Dynamic configuration
#         self.num_cameras = Camera_no
#         self.camera_frames = {}
#         self.camera_labels = []
#         self.camera_frame_widgets = []
#         self.active_cameras = set()
#         self.max_cameras_display = self.num_cameras
        
#         # Grid configuration based on camera count
#         self.grid_config = self._calculate_grid_layout(self.num_cameras)
        
#         # Performance optimization variables
#         self.last_frame_time = 0
#         self.frame_skip_count = 0
#         self.max_fps = 30
#         self.frame_interval = 1.0 / self.max_fps
        
#         # Event update optimization
#         self.last_event_update = 0
#         self.event_update_interval = 0.5
#         self.event_cache = []
#         self.event_update_lock = threading.Lock()
        
#         # UI update queue for thread safety
#         self.ui_update_queue = queue.Queue()
#         self.display_queue = queue.Queue(maxsize=30)
#         self.detection_queue = queue.Queue(maxsize=30)
        
#         self.setup_surveillance_ui()
#         self.start_ui_update_thread()
#         self.start_event_update_thread()
#         self.start_demo_updates()

#     def _calculate_grid_layout(self, num_cameras):
#         """Calculate optimal grid layout for given number of cameras"""
#         if num_cameras == 4:
#             return {'rows': 2, 'cols': 2}
#         elif num_cameras == 6:
#             return {'rows': 2, 'cols': 3}
#         elif num_cameras == 8:
#             return {'rows': 2, 'cols': 4}
#         else:
#             # Default fallback - calculate square-ish grid
#             rows = int(math.ceil(math.sqrt(num_cameras)))
#             cols = int(math.ceil(num_cameras / rows))
#             return {'rows': rows, 'cols': cols}

#     def setup_surveillance_ui(self):
#         """Create surveillance system UI layout"""
#         # Main frame with surveillance system styling
#         self.main_frame = ctk.CTkFrame(self.root, fg_color="#F1F5FA", corner_radius=0)
#         self.main_frame.grid(row=0, column=0, sticky="nsew")
#         self.main_frame.grid_columnconfigure(0, weight=2)
#         self.main_frame.grid_rowconfigure(1, weight=1)
        
#         # Create header with counters and title
#         self.create_header_with_counters()
        
#         # Create main content area
#         self.create_main_content()

#     def event_show(self): 
#         pass  
#         # ev=EventFeedMonitor()
#        # pass 

#     def create_header_with_counters(self):
#         """Create header section with entry/exit counters and title"""
#         self.main_content = ctk.CTkFrame(self.main_frame, fg_color="#F1F5FA")
#         self.main_content.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
#         self.main_content.grid_columnconfigure(1, weight=1)
        
#         # Counter frame
#         counter_frame = ctk.CTkFrame(self.main_content, fg_color="#F1F5FA")
#         counter_frame.grid(row=0, column=0, padx=(0, 15), sticky="ns")
        
#         # Entry counter
#         entry_frame = ctk.CTkFrame(counter_frame, fg_color="#E8F5E9")
#         entry_frame.grid(row=0, column=0, padx=(0, 10))
        
#         entry_label = ctk.CTkLabel(entry_frame, text="Entry", font=("", 16), text_color="#2E7D32")
#         entry_label.grid(row=0, column=0, padx=10, pady=5)
        
#         self.entry_count = ctk.CTkLabel(
#             entry_frame, text="0", font=("", 18, "bold"), text_color="#2E7D32",
#             width=50, height=30, fg_color="#C8E6C9", corner_radius=6
#         )
#         self.entry_count.grid(row=0, column=1, padx=10, pady=5)
        
#         # Exit counter
#         exit_frame = ctk.CTkFrame(counter_frame, fg_color="#FBE9E7")
#         exit_frame.grid(row=0, column=1)
        
#         exit_label = ctk.CTkLabel(exit_frame, text="Exit", font=("", 16), text_color="#C62828")
#         exit_label.grid(row=0, column=0, padx=10, pady=5)
        
#         self.exit_count = ctk.CTkLabel(
#             exit_frame, text="0", font=("", 18, "bold"), text_color="#C62828",
#             width=50, height=30, fg_color="#FFCDD2", corner_radius=6
#         )
#         self.exit_count.grid(row=0, column=1, padx=10, pady=5)
        
#         # Title
#         title = ctk.CTkLabel(
#             self.main_content, text=f"Live Event - {self.num_cameras} Cameras", 
#             font=("", 23, "bold"), fg_color="#FBE9E7",
#             text_color="#000000"
#         )
#         title.grid(row=0, column=1, pady=(0, 10), padx=(300, 0), sticky="w")
        
#         history_button = ctk.CTkButton(self.main_content, text="Show history", font=("", 20),
#                                width=150, height=30, fg_color="red", hover_color="#555555",
#                                command=lambda: self.show_event_history())
#         history_button.grid(row=0, column=2, padx=10, pady=5)

#     def create_main_content(self):
#         """Create main content area with video and detection panels"""
#         self.content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
#         self.content.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
#         self.content.grid_columnconfigure(0, weight=6)
#         self.content.grid_columnconfigure(1, weight=4)
#         self.content.grid_rowconfigure(0, weight=1)
#         self.content.grid_propagate(False)
        
#         # Create video frame with dynamic grid
#         self.create_surveillance_video_frame()
        
#         # Create detection sidebar
#         self.create_detection_sidebar()

#     def create_surveillance_video_frame(self):
#         """Create video frame with dynamic camera grid and expand/minimize functionality"""
#         self.live_feed_width = int(self.main_width * 0.75)
#         self.live_feed_height = self.main_height
        
#         video_container = ctk.CTkFrame(
#             self.content, fg_color="white", corner_radius=0, border_width=4,
#             border_color="white", width=self.live_feed_width, height=self.live_feed_height
#         )
#         video_container.grid(row=0, column=0, padx=(0, 0), sticky="nsew")
#         video_container.grid_columnconfigure(0, weight=1)
#         video_container.grid_rowconfigure(0, weight=1)
#         video_container.grid_propagate(False)

#         self.live_feed = ctk.CTkFrame(
#             video_container, fg_color="white", corner_radius=0, width=self.live_feed_width
#         )
#         self.live_feed.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        
#         # Configure grid based on camera layout
#         rows, cols = self.grid_config['rows'], self.grid_config['cols']
#         for i in range(cols):
#             self.live_feed.grid_columnconfigure(i, weight=1)
#         for i in range(rows):
#             self.live_feed.grid_rowconfigure(i, weight=1)
        
#         self.live_feed.grid_propagate(False)

#         # Initialize arrays to store widgets
#         self.camera_labels = []
#         self.camera_frame_widgets = []
#         self.maximize_buttons = []

#         # Create camera frames in dynamic grid
#         for camera_idx in range(self.num_cameras):
#             row = camera_idx // cols
#             col = camera_idx % cols

#             # Create camera frame
#             camera_frame = ctk.CTkFrame(self.live_feed, fg_color="black")
#             camera_frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
#             camera_frame.grid_columnconfigure(0, weight=1)
#             camera_frame.grid_rowconfigure(0, weight=1)
#             camera_frame.grid_propagate(False)

#             # Store frame reference
#             self.camera_frame_widgets.append(camera_frame)

#             # Create camera label
#             label = ctk.CTkLabel(
#                 camera_frame, 
#                 text=f"📹\n\nCamera {camera_idx + 1}\nConnecting...",
#                 fg_color="black",
#                 text_color="white",
#                 font=ctk.CTkFont(size=16, weight="bold")
#             )
#             label.grid(row=0, column=0, sticky="nsew")
#             self.camera_labels.append(label)

#             # Create maximize button
#             max_button = ctk.CTkButton(
#                 camera_frame, text="⛶", font=("", 14), width=30, height=30,
#                 fg_color="#333333", hover_color="#555555",
#                 command=lambda idx=camera_idx: self.toggle_camera_view(idx)
#             )
#             max_button.place(relx=1.0, rely=0.0, x=-35, y=5, anchor="ne")
#             self.maximize_buttons.append(max_button)

#         # Create minimize button (hidden initially)
#         self.minimize_button = ctk.CTkButton(
#             self.live_feed, text="🗕", font=("", 14), width=30, height=30,
#             fg_color="#333333", hover_color="#555555",
#             command=lambda: self.toggle_camera_view(self.expanded_camera)
#         )

#     def show_event_history(self):
#         print("hello history tabel")
#         self.event_show()

#     def create_detection_sidebar(self):
#         """Create detection sidebar similar to original surveillance system"""
#         self.sidebar = ctk.CTkFrame(
#             self.content, fg_color="white", corner_radius=0, border_width=0,
#             border_color="white", height=self.live_feed_height,
#             width=int(self.main_width * 0.30)
#         )
#         self.sidebar.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 0))
#         self.sidebar.grid_columnconfigure(0, weight=1)
#         self.sidebar.grid_propagate(False)
       
#         # Create header for detection sidebar
#         sidebar_header = ctk.CTkFrame(self.sidebar, height=100, fg_color="#E3F2FD")
#         sidebar_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
#         sidebar_header.grid_propagate(False)
        
#         header_label = ctk.CTkLabel(
#             sidebar_header, text="EVENT DETAILS", 
#             font=ctk.CTkFont(size=16, weight="bold"),
#             text_color="#1976D2"
#         )
#         header_label.pack(pady=15)
        
#         # Create scrollable frame for detection items
#         self.scrollable_frame = ctk.CTkScrollableFrame(
#             self.sidebar, fg_color="#F5F5F5",height=300
#         )
#         self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
#         self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
#         # Configure sidebar grid
#         self.sidebar.grid_rowconfigure(1, weight=1)
        
#         # Initialize detection frames
#         for i in range(5):
#             self.create_detection_item(i)

#     def create_detection_item(self, row_index):
#         """Create detection item in sidebar"""
#         frame_height = 160
        
#         main_frame = ctk.CTkFrame(
#             self.scrollable_frame, fg_color="white", corner_radius=5,
#             border_width=2, border_color="green", height=frame_height
#         )
#         main_frame.grid(row=row_index, column=0, pady=5, padx=5, sticky="ew")
#         main_frame.grid_propagate(False)
#         main_frame.grid_columnconfigure(0, weight=55)
#         main_frame.grid_columnconfigure(1, weight=65)
#         main_frame.grid_rowconfigure(0, weight=1)
        
#         # Image frame
#         img_frame = ctk.CTkFrame(main_frame, fg_color="#f0f0f0", corner_radius=0)
#         img_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
#         img_frame.grid_propagate(False)
        
#         img_label = ctk.CTkLabel(img_frame, text="", fg_color="white")
#         img_label.grid(row=0, column=0, sticky="nsew")
#         img_frame.grid_columnconfigure(0, weight=1)
#         img_frame.grid_rowconfigure(0, weight=1)
        
#         # Info frame
#         info_frame = ctk.CTkFrame(main_frame,height=400,fg_color="white", corner_radius=0)
#         info_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
#         info_frame.grid_propagate(False)
        
#         for i in range(6):
#             info_frame.grid_rowconfigure(i, weight=1)
#         info_frame.grid_columnconfigure(0, weight=1)
        
#         self.details_frames.append({
#             'frame': main_frame,
#             'img_label': img_label,
#             'img_frame': img_frame,
#             'info_frame': info_frame,
#             'active': False,
#             'timestamp': None
#         })

#     def toggle_camera_view(self, camera_idx):
#         """Toggle between grid view and expanded view"""
#         if self.expanded_camera == camera_idx:
#             # Switch back to grid view
#             self.expanded_camera = None
#             self.restore_grid_view()
#         else:
#             # Expand selected camera
#             self.expanded_camera = camera_idx
#             self.expand_camera_view(camera_idx)

#         # Force layout update
#         self.root.after(50, self.force_layout_update)

#     def restore_grid_view(self):
#         """Restore dynamic grid layout"""
#         print("Restoring grid view...")
        
#         # Hide minimize button
#         self.minimize_button.place_forget()
        
#         # Reset grid configuration
#         rows, cols = self.grid_config['rows'], self.grid_config['cols']
#         for i in range(cols):
#             self.live_feed.grid_columnconfigure(i, weight=1)
#         for i in range(rows):
#             self.live_feed.grid_rowconfigure(i, weight=1)
        
#         # Remove all frames from grid first
#         for i in range(self.num_cameras):
#             self.camera_frame_widgets[i].grid_remove()
        
#         # Re-add frames in correct grid positions
#         for i in range(self.num_cameras):
#             row = i // cols
#             col = i % cols
            
#             self.camera_frame_widgets[i].grid(
#                 row=row, column=col, sticky="nsew", padx=1, pady=1,
#                 rowspan=1, columnspan=1
#             )
            
#             # Ensure label fills the frame
#             self.camera_labels[i].grid(row=0, column=0, sticky="nsew")
            
#             # Show maximize button
#             self.maximize_buttons[i].place(relx=1.0, rely=0.0, x=-35, y=5, anchor="ne")

#     def expand_camera_view(self, camera_idx):
#         """Expand single camera to full view"""
#         print(f"Expanding camera {camera_idx}...")
        
#         # Hide all maximize buttons
#         for i in range(self.num_cameras):
#             self.maximize_buttons[i].place_forget()
        
#         # Remove all frames from grid
#         for i in range(self.num_cameras):
#             self.camera_frame_widgets[i].grid_remove()
        
#         # Grid only the selected camera frame spanning full area
#         rows, cols = self.grid_config['rows'], self.grid_config['cols']
#         self.camera_frame_widgets[camera_idx].grid(
#             row=0, column=0, sticky="nsew", padx=0, pady=0,
#             rowspan=rows, columnspan=cols
#         )
        
#         # Ensure label fills the expanded frame
#         self.camera_labels[camera_idx].grid(row=0, column=0, sticky="nsew")
        
#         # Show minimize button
#         self.minimize_button.place(relx=1.0, rely=0.0, x=-35, y=5, anchor="ne")

#     def force_layout_update(self):
#         """Force layout update after grid changes"""
#         try:
#             self.live_feed.update_idletasks()
#             self.root.update_idletasks()
            
#             if self.expanded_camera is None:
#                 for i in range(self.num_cameras):
#                     if self.camera_frame_widgets[i].winfo_viewable():
#                         self.camera_frame_widgets[i].update_idletasks()
#                         self.camera_labels[i].update_idletasks()
#             else:
#                 if self.camera_frame_widgets[self.expanded_camera].winfo_viewable():
#                     self.camera_frame_widgets[self.expanded_camera].update_idletasks()
#                     self.camera_labels[self.expanded_camera].update_idletasks()
            
#             print("Layout update completed")
#         except Exception as e:
#             print(f"Error in force_layout_update: {e}")

#     def start_ui_update_thread(self):
#         """Start thread to handle UI updates from other threads"""
#         def ui_updater():
#             while True:
#                 try:
#                     update_func = self.ui_update_queue.get(timeout=0.01)
#                     if update_func:
#                         self.root.after_idle(update_func)
#                 except queue.Empty:
#                     continue
#                 except Exception as e:
#                     print(f"UI update error: {e}")
                    
#         ui_thread = threading.Thread(target=ui_updater, daemon=True)
#         ui_thread.start()

#     def start_event_update_thread(self):
#         """Start separate thread for event updates"""
#         print("Start separate thread for event updates")
#         print("start_event_update_thread")
#         def event_updater():
#             while True:
#                 try:
#                     current_time = time.time()
#                     if current_time - self.last_event_update >= self.event_update_interval:
#                         self.fetch_and_cache_events()
#                         self.last_event_update = current_time
#                     time.sleep(0.1)
#                 except Exception as e:
#                     print(f"Event update error: {e}")
#                     time.sleep(1)
                    
#         event_thread = threading.Thread(target=event_updater, daemon=True)
#         event_thread.start()

#     def fetch_and_cache_events(self):
#         """Fetch events and update detection sidebar"""
#         print("fetch_and_cache_events")
#         try:
#             temp = self.obj_db.fetch_latest_events()
#             new_events = []
#             if temp:
#                 for data in temp[:8]:  # Limit to 5 most recent events
#                     new_events.append({
#                         "id": data[0], 
#                         "Camera Name": data[1],
#                         "image_frame": data[2], 
#                         "Helmet": data[3],
#                         "Shoes": data[5],
#                         "Vest": data[4],
#                         "status": "✓"
#                     })
                
#                 # Update detection sidebar
#                 with self.event_update_lock:
#                     if new_events != self.event_cache:
#                         self.event_cache = new_events.copy()
#                         self.ui_update_queue.put(lambda: self.update_detection_sidebar())
                    
#         except Exception as e:
#             print(f"Error fetching events: {e}")

#     def update_detection_sidebar(self):
#         """Update detection sidebar with latest events"""
#         print("update detection sidebar _________________________________")
#         try:
#             with self.event_update_lock:
#                 for i, event in enumerate(self.event_cache):
#                     if i >= len(self.details_frames):
#                         break
                    
#                     frame = self.details_frames[i]
                    
#                     # Clear existing info
#                     for widget in frame['info_frame'].winfo_children():
#                         widget.destroy()
                    
#                     # Update image
#                     try:
#                         img_data = base64.b64decode(event["image_frame"])
#                         image = Image.open(io.BytesIO(img_data))
#                         image.thumbnail((340, 150), Image.Resampling.LANCZOS)
#                         photo = ImageTk.PhotoImage(image)
                        
#                         frame['img_label'].configure(image=photo)
#                         frame['img_label'].image = photo
#                     except Exception as e:
#                         print(f"Image processing error: {e}")
#                         frame['img_label'].configure(text="No Image")
                    
#                     # Update info
#                     info_items = [
#                         ("Event ID", event['id']),
#                         ("Camera", event['Camera Name']),
#                         ("Helmet", event['Helmet']),
#                         ("Vest", event['Vest']),
#                         ("Shoes", event['Shoes']),
#                         ("Status", event['status'])
#                     ]
                    
#                     for idx, (label, value) in enumerate(info_items):
#                         info_label = ctk.CTkLabel(
#                             frame['info_frame'],
#                             text=f"{label}: {value}",
#                             font=ctk.CTkFont(size=12, weight="bold"),
#                             text_color="black",
#                             anchor="w"
#                         )
#                         info_label.grid(row=idx, column=0, sticky="w", padx=8, pady=1)
                        
#         except Exception as e:
#             print(f"Error updating detection sidebar: {e}")

#     def start_video_feed(self):
#         """Start video feed from cameras"""
#         if self.is_running:
#             return
            
#         self.is_running = True
#         self.video_thread = threading.Thread(target=self._video_loop, daemon=True)
#         self.video_thread.start()

#     def _video_loop(self):
#         while self.is_running:
#             latest_frames = {}

#             try:
#                 # Keep only the latest frame from the queue
#                 while not self.frame_queue_to_show.empty():
#                     cam_id, frame = self.frame_queue_to_show.get_nowait()
#                     latest_frames[cam_id] = frame  # overwrite older frames

#                 # Display only the most recent frame per camera
#                 for cam_id, frame in latest_frames.items():
#                     display_idx = cam_id % self.max_cameras_display
#                     if display_idx >= self.max_cameras_display:
#                         continue

#                     # Resize frame efficiently
#                     # display_width=400
#                     # display_height=430
#                     # if(self.max_cameras_display==4):
#                     #     display_width=630,
#                     #     display_height=430
#                     # if(self.max_cameras_display==6):
#                     #     display_width=430,
#                     #     display_height=350
#                     # if(self.max_cameras_display==8):
#                     #     display_width=330,
#                     #     display_height=330
                    
#                     display_size = (980, 900) if self.expanded_camera == display_idx else (640, 430)
#                     frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                     frame_resized = cv2.resize(frame_rgb, display_size, interpolation=cv2.INTER_LINEAR)
#                     img = Image.fromarray(frame_resized)
#                     photo = ImageTk.PhotoImage(image=img)

#                     # Cache photo to prevent garbage collection
#                     self.camera_frames[display_idx] = photo
#                     self.ui_update_queue.put(lambda p=photo, idx=display_idx: self.update_camera_display(idx, p))

#             except Exception as e:
#                 print(f"Video loop error: {e}")

#             time.sleep(0.001)  # small sleep to avoid 100% CPU

#     def update_camera_display(self, camera_idx, photo):
#         """Update specific camera display with new frame"""
#         try:
#             if camera_idx < len(self.camera_labels):
#                 self.camera_labels[camera_idx].configure(image=photo, text="")
#                 self.camera_labels[camera_idx].image = photo
#         except Exception as e:
#             print(f"Camera {camera_idx} display update error: {e}")

#     def start_demo_updates(self):
#         """Start demo updates"""
#         self.start_video_feed()
#         self.fetch_and_cache_events()
        
#     def run(self):
#         try:
#             self.root.mainloop()
#         finally:
#             self.is_running = False
#             if self.cap:
#                 self.cap.release()

# if __name__ == "__main__":
#     # Example usage:
#     # For 4 cameras: app = LiveFeedMonitor(Camera_no=4)
#     # For 6 cameras: app = LiveFeedMonitor(Camera_no=6) 
#     # For 8 cameras: app = LiveFeedMonitor(Camera_no=8)
#     app = LiveFeedMonitor(Camera_no=8)  # Change this number as needed
#     app.run()