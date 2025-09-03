import base64
import io
import math
import platform
import numpy as np
import pyodbc
import customtkinter as ctk
from customtkinter import CTkFrame, CTkLabel, CTkImage, CTkButton, CTkToplevel
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import cv2
import threading
import queue as pyqueue
import time
from datetime import datetime
from core.database import EventDatabase
from gui.Core.audio import AudioController, AudioThreadManager
from gui.Core.Recognistion_process.ConfigLoader import ConfigLoader
from share_queue import queue, frame_queue_to_show

class LiveEventInterface(CTkFrame):
    def __init__(self, root, root_width: int = 1920, root_height: int = 1080):
        super().__init__(root)

        self.root = root
        self.history_button = []
        self.winfo_toplevel().title("Live Event - Multi Camera Surveillance")

        # Video capture variables
        self.cap = None
        self.video_thread = None
        self.is_running = False
        self.obj_db = EventDatabase()
        self.events = []
        
        # Surveillance system variables
        self.root_width = root_width
        self.root_height = root_height
        self.main_width = int(self.root_width * 0.95)
        self.main_height = int(self.root_height * 0.95)
        self.expanded_camera = None
        self.maximize_buttons = []
        self.minimize_button = None
        self.details_frames = []
        
        # Multi-camera support - Dynamic configuration
        self.num_cameras = 4
        self.display_cameras = 4
        self.camera_frames = {}
        self.camera_labels = []
        self.camera_frame_widgets = []
        self.active_cameras = set()
        self.max_cameras_display = self.num_cameras
        
        # Grid configuration based on camera count
        self.grid_config = self._calculate_grid_layout(self.display_cameras)
        
        # Performance optimization variables
        self.last_frame_time = 0
        self.frame_skip_count = 0
        self.max_fps = 60
        self.frame_interval = 1.0 / self.max_fps
        
        # Event update optimization
        self.last_event_update = 0
        self.event_update_interval = 0.5
        self.event_cache = []
        self.event_update_lock = threading.Lock()
        
        # UI update queue for thread safety
        self.ui_update_queue = pyqueue.Queue()
        self.display_queue = pyqueue.Queue(maxsize=100)
        self.detection_queue = pyqueue.Queue(maxsize=30)
        
        self.setup_surveillance_ui()
        self.start_ui_update_thread()
        self.start_event_update_thread()
        self.start_demo_updates()

    def _calculate_grid_layout(self, num_cameras):
        """Calculate optimal grid layout for given number of cameras"""
        if num_cameras == 1:
            return {'rows': 1, 'cols': 1}
        elif num_cameras == 4:
            return {'rows': 2, 'cols': 2}
        elif num_cameras == 6:
            return {'rows': 2, 'cols': 3}
        elif num_cameras == 8:
            return {'rows': 2, 'cols': 4}
        else:
            rows = int(math.ceil(math.sqrt(num_cameras)))
            cols = int(math.ceil(num_cameras / rows))
            return {'rows': rows, 'cols': cols}

    def setup_surveillance_ui(self):
        """Create surveillance system UI layout"""
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#F1F5FA", corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=2)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.create_header_with_counters()
        self.create_main_content()

    def event_show(self): 
        pass

    def create_header_with_counters(self):
        """Create header section with entry/exit counters and title"""
        self.main_content = ctk.CTkFrame(self.main_frame, fg_color="#F1F5FA")
        self.main_content.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.main_content.grid_columnconfigure(1, weight=1)
        
        counter_frame = ctk.CTkFrame(self.main_content, fg_color="#F1F5FA")
        counter_frame.grid(row=0, column=0, padx=(0, 15), sticky="ns")
        
        entry_frame = ctk.CTkFrame(counter_frame, fg_color="#E8F5E9")
        entry_frame.grid(row=0, column=0, padx=(0, 10))
        
        entry_label = ctk.CTkLabel(entry_frame, text="Entry", font=("", 16), text_color="#2E7D32")
        entry_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.entry_count = ctk.CTkLabel(
            entry_frame, text="0", font=("", 18, "bold"), text_color="#2E7D32",
            width=50, height=30, fg_color="#C8E6C9", corner_radius=6
        )
        self.entry_count.grid(row=0, column=1, padx=10, pady=5)
        
        exit_frame = ctk.CTkFrame(counter_frame, fg_color="#FBE9E7")
        exit_frame.grid(row=0, column=1)
        
        exit_label = ctk.CTkLabel(exit_frame, text="Exit", font=("", 16), text_color="#C62828")
        exit_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.exit_count = ctk.CTkLabel(
            exit_frame, text="0", font=("", 18, "bold"), text_color="#C62828",
            width=50, height=30, fg_color="#FFCDD2", corner_radius=6
        )
        self.exit_count.grid(row=0, column=1, padx=10, pady=5)
        
        title = ctk.CTkLabel(
            self.main_content, text=f"Live Event - {self.display_cameras} Cameras", 
            font=("", 23, "bold"), fg_color="#FBE9E7",
            text_color="#000000"
        )
        title.grid(row=0, column=1, pady=(0, 10), padx=(100, 0), sticky="w")
        
        grid_buttons_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        grid_buttons_frame.grid(row=0, column=2, padx=(10, 50), pady=5)
        
        grid_configs = [
            {"cameras": 1, "tooltip": "Single View"},
            {"cameras": 4, "tooltip": "2x2 Grid"},
            {"cameras": 6, "tooltip": "2x3 Grid"},
            {"cameras": 8, "tooltip": "2x4 Grid"},
        ]

        self.grid_icons = {
            1: ImageTk.PhotoImage(Image.open("resource/video/singel_camera.png").resize((32, 32))),
            4: ImageTk.PhotoImage(Image.open("resource/video/4_grid.png").resize((32, 32))),
            6: ImageTk.PhotoImage(Image.open("resource/video/6_grid.png").resize((32, 32))),
            8: ImageTk.PhotoImage(Image.open("resource/video/8_grid.png").resize((32, 32))),
        }

        for i, config in enumerate(grid_configs):
            btn_color = "white" if config["cameras"] == self.display_cameras else "white"
            hover_color = "white" if config["cameras"] == self.display_cameras else "white"
            grid_btn = ctk.CTkButton(
                grid_buttons_frame,
                text="", image=self.grid_icons[config["cameras"]],
                width=50, height=35, fg_color=btn_color, hover_color=hover_color,
                command=lambda c=config["cameras"]: self.set_grid_view(c)
            )
            grid_btn.grid(row=0, column=i, padx=2)
            if not hasattr(self, 'grid_buttons'):
                self.grid_buttons = []
            self.grid_buttons.append((grid_btn, config["cameras"]))
        
        history_button = ctk.CTkButton(
            self.main_content, text="Show History", font=("", 16),
            width=150, height=35, fg_color="#d32f2f", hover_color="#b71c1c",
            command=lambda: self.show_event_history()
        )
        history_button.grid(row=0, column=3, padx=10, pady=5)

        test_button = ctk.CTkButton(
            self.main_content, text="Force Sidebar Update", font=("", 16),
            width=150, height=35, fg_color="#1976D2", hover_color="#0D47A1",
            command=lambda: self.update_detection_sidebar()
        )
        test_button.grid(row=0, column=4, padx=10, pady=5)

    def set_grid_view(self, num_cameras):
        """Set specific grid view directly"""
        if num_cameras == self.display_cameras:
            return
        if num_cameras == 1:
            self.toggle_camera_view(1)
        else:
            self.display_cameras = num_cameras
            self.max_cameras_display = self.display_cameras
            self.grid_config = self._calculate_grid_layout(self.display_cameras)
            
            for btn, btn_cameras in self.grid_buttons:
                if btn_cameras == self.display_cameras:
                    btn.configure(fg_color="#2E7D32", hover_color="#1B5E20")
                else:
                    btn.configure(fg_color="#666666", hover_color="#555555")
            
            for widget in self.main_content.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and "Live Event" in widget.cget("text"):
                    widget.configure(text=f"Live Event - {self.display_cameras} Cameras")
                    break
            
            if self.expanded_camera is not None and self.expanded_camera >= self.display_cameras:
                self.expanded_camera = None
            
            self.recreate_video_frame()

    def toggle_grid_view(self):
        """Toggle between different grid views: 1, 4, 6, 8 cameras"""
        grid_options = [1, 4, 6, 8]
        current_index = grid_options.index(self.display_cameras) if self.display_cameras in grid_options else 0
        next_index = (current_index + 1) % len(grid_options)
        self.set_grid_view(grid_options[next_index])

    def recreate_video_frame(self):
        """Recreate video frame with new grid configuration"""
        for widget in self.camera_frame_widgets:
            widget.destroy()
        for button in self.maximize_buttons:
            button.destroy()
            
        self.camera_labels.clear()
        self.camera_frame_widgets.clear()
        self.maximize_buttons.clear()
        
        rows, cols = self.grid_config['rows'], self.grid_config['cols']
        
        for i in range(10):
            self.live_feed.grid_columnconfigure(i, weight=0)
            self.live_feed.grid_rowconfigure(i, weight=0)
        
        for i in range(cols):
            self.live_feed.grid_columnconfigure(i, weight=1)
        for i in range(rows):
            self.live_feed.grid_rowconfigure(i, weight=1)
        
        for camera_idx in range(self.display_cameras):
            row = camera_idx // cols
            col = camera_idx % cols

            camera_frame = ctk.CTkFrame(self.live_feed, fg_color="black")
            camera_frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
            camera_frame.grid_columnconfigure(0, weight=1)
            camera_frame.grid_rowconfigure(0, weight=1)
            camera_frame.grid_propagate(False)

            self.camera_frame_widgets.append(camera_frame)

            display_text = f"📹\n\nCamera {camera_idx + 1}\nConnecting..."

            label = ctk.CTkLabel(
                camera_frame, text=display_text, fg_color="black",
                text_color="white", font=ctk.CTkFont(size=16, weight="bold")
            )
            label.grid(row=0, column=0, sticky="nsew")
            self.camera_labels.append(label)

            max_button = ctk.CTkButton(
                camera_frame, text="⛶", font=("", 14), width=30, height=30,
                fg_color="#333333", hover_color="#555555",
                command=lambda idx=camera_idx: self.toggle_camera_view(idx)
            )
            max_button.place(relx=1.0, rely=0.0, x=-35, y=5, anchor="ne")
            self.maximize_buttons.append(max_button)

        if hasattr(self, 'minimize_button') and self.minimize_button:
            self.minimize_button.destroy()
            
        self.minimize_button = ctk.CTkButton(
            self.live_feed, text="🗕", font=("", 14), width=30, height=30,
            fg_color="#333333", hover_color="#555555",
            command=lambda: self.toggle_camera_view(self.expanded_camera)
        )
        
        self.root.after(50, self.force_layout_update)

    def create_main_content(self):
        """Create main content area with video and detection panels"""
        self.content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=6)
        self.content.grid_columnconfigure(1, weight=4)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_propagate(False)
        
        self.create_surveillance_video_frame()
        self.create_detection_sidebar()
        print(f"Content visibility: {self.content.winfo_viewable()}, size: {self.content.winfo_geometry()}")  # Debug

    def create_surveillance_video_frame(self):
        """Create video frame with dynamic camera grid and expand/minimize functionality"""
        self.live_feed_width = int(self.main_width * 0.60)
        self.live_feed_height = self.main_height
        
        video_container = ctk.CTkFrame(
            self.content, fg_color="white", corner_radius=0, border_width=4,
            border_color="white", width=self.live_feed_width, height=self.live_feed_height
        )
        video_container.grid(row=0, column=0, padx=(0, 0), sticky="nsew")
        video_container.grid_columnconfigure(0, weight=1)
        video_container.grid_rowconfigure(0, weight=1)
        video_container.grid_propagate(False)

        self.live_feed = ctk.CTkFrame(
            video_container, fg_color="white", corner_radius=0, width=self.live_feed_width
        )
        self.live_feed.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        
        rows, cols = self.grid_config['rows'], self.grid_config['cols']
        for i in range(cols):
            self.live_feed.grid_columnconfigure(i, weight=1)
        for i in range(rows):
            self.live_feed.grid_rowconfigure(i, weight=1)
        
        self.live_feed.grid_propagate(False)

        self.camera_labels = []
        self.camera_frame_widgets = []
        self.maximize_buttons = []
        self.grid_buttons = []

        for camera_idx in range(self.display_cameras):
            row = camera_idx // cols
            col = camera_idx % cols

            camera_frame = ctk.CTkFrame(self.live_feed, fg_color="black")
            camera_frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
            camera_frame.grid_columnconfigure(0, weight=1)
            camera_frame.grid_rowconfigure(0, weight=1)
            camera_frame.grid_propagate(False)

            self.camera_frame_widgets.append(camera_frame)

            display_text = f"📹\n\nCamera {camera_idx + 1}\nConnecting..."

            label = ctk.CTkLabel(
                camera_frame, text=display_text, fg_color="black",
                text_color="white", font=ctk.CTkFont(size=16, weight="bold")
            )
            label.grid(row=0, column=0, sticky="nsew")
            self.camera_labels.append(label)

            max_button = ctk.CTkButton(
                camera_frame, text="⛶", font=("", 14), width=30, height=30,
                fg_color="#333333", hover_color="#555555",
                command=lambda idx=camera_idx: self.toggle_camera_view(idx)
            )
            max_button.place(relx=1.0, rely=0.0, x=-35, y=5, anchor="ne")
            self.maximize_buttons.append(max_button)

        self.minimize_button = ctk.CTkButton(
            self.live_feed, text="🗕", font=("", 14), width=30, height=30,
            fg_color="#333333", hover_color="#555555",
            command=lambda: self.toggle_camera_view(self.expanded_camera)
        )

    def show_event_history(self):
        print("hello history tabel")
        self.event_show()

    def create_detection_sidebar(self):
        """Create detection sidebar similar to original surveillance system"""
        self.sidebar = ctk.CTkFrame(
            self.content, fg_color="#FFFFFF", corner_radius=0, border_width=2,
            border_color="black", height=self.live_feed_height, width=400
        )
        self.sidebar.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 0))
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(1, weight=1)
        self.sidebar.grid_propagate(False)

        sidebar_header = ctk.CTkFrame(self.sidebar, height=100, fg_color="#E3F2FD")
        sidebar_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        sidebar_header.grid_propagate(False)
        
        header_label = ctk.CTkLabel(
            sidebar_header, text="EVENT DETAILS", 
            font=ctk.CTkFont(size=16, weight="bold"), text_color="black"
        )
        header_label.pack(pady=15, fill="x")

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="#FFFFFF", height=self.live_feed_height - 120
        )
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.sidebar.update_idletasks()
        self.scrollable_frame.update_idletasks()
        print("Sidebar created: visible=%s, size=%s" % (self.sidebar.winfo_viewable(), self.sidebar.winfo_geometry()))

        for i in range(5):
            self.create_detection_item(i)

    def create_detection_item(self, row_index):
        """Create detection item in sidebar"""
        frame_height = 200
        
        main_frame = ctk.CTkFrame(
            self.scrollable_frame, fg_color="white", corner_radius=5,
            border_width=2, border_color="green", height=frame_height
        )
        main_frame.grid(row=row_index, column=0, pady=5, padx=5, sticky="ew")
        main_frame.grid_propagate(False)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)
        
        img_frame = ctk.CTkFrame(main_frame, fg_color="pink", corner_radius=0, width=240)
        img_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        img_frame.grid_propagate(False)
        
        img_label = ctk.CTkLabel(img_frame, text="No Image", fg_color="#FFFFFF")
        img_label.grid(row=0, column=0, sticky="nsew")
        img_frame.grid_columnconfigure(0, weight=1)
        img_frame.grid_rowconfigure(0, weight=1)
        
        info_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
        info_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        info_frame.grid_propagate(False)
        
        for i in range(4):
            info_frame.grid_rowconfigure(i, weight=1)
        info_frame.grid_columnconfigure(0, weight=1)
        
        self.details_frames.append({
            'frame': main_frame,
            'img_label': img_label,
            'img_frame': img_frame,
            'info_frame': info_frame,
            'active': False,
            'timestamp': None
        })
        
        main_frame.update_idletasks()
        print(f"Detection item {row_index}: visible=%s, size=%s" % (main_frame.winfo_viewable(), main_frame.winfo_geometry()))

    def toggle_camera_view(self, camera_idx):
        """Toggle between grid view and expanded view"""
        if self.expanded_camera == camera_idx:
            self.expanded_camera = None
            self.restore_grid_view()
        else:
            self.expanded_camera = camera_idx
            self.expand_camera_view(camera_idx)
        self.root.after(50, self.force_layout_update)

    def restore_grid_view(self):
        """Restore dynamic grid layout"""
        print("Restoring grid view...")
        self.minimize_button.place_forget()
        
        rows, cols = self.grid_config['rows'], self.grid_config['cols']
        for i in range(cols):
            self.live_feed.grid_columnconfigure(i, weight=1)
        for i in range(rows):
            self.live_feed.grid_rowconfigure(i, weight=1)
        
        for i in range(self.display_cameras):
            self.camera_frame_widgets[i].grid_remove()
        
        for i in range(self.display_cameras):
            row = i // cols
            col = i % cols
            self.camera_frame_widgets[i].grid(
                row=row, column=col, sticky="nsew", padx=1, pady=1,
                rowspan=1, columnspan=1
            )
            self.camera_labels[i].grid(row=0, column=0, sticky="nsew")
            self.maximize_buttons[i].place(relx=1.0, rely=0.0, x=-35, y=5, anchor="ne")

    def expand_camera_view(self, camera_idx):
        """Expand single camera to full view"""
        print(f"Expanding camera {camera_idx}...")
        for i in range(self.display_cameras):
            self.maximize_buttons[i].place_forget()
        
        for i in range(self.display_cameras):
            self.camera_frame_widgets[i].grid_remove()
        
        rows, cols = self.grid_config['rows'], self.grid_config['cols']
        self.camera_frame_widgets[camera_idx].grid(
            row=0, column=0, sticky="nsew", padx=0, pady=0,
            rowspan=rows, columnspan=cols
        )
        self.camera_labels[camera_idx].grid(row=0, column=0, sticky="nsew")
        self.minimize_button.place(relx=1.0, rely=0.0, x=-35, y=5, anchor="ne")

    def force_layout_update(self):
        """Force layout update after grid changes"""
        try:
            self.live_feed.update_idletasks()
            self.root.update_idletasks()
            if self.expanded_camera is None:
                for i in range(self.display_cameras):
                    if self.camera_frame_widgets[i].winfo_viewable():
                        self.camera_frame_widgets[i].update_idletasks()
                        self.camera_labels[i].update_idletasks()
            else:
                if self.camera_frame_widgets[self.expanded_camera].winfo_viewable():
                    self.camera_frame_widgets[self.expanded_camera].update_idletasks()
                    self.camera_labels[self.expanded_camera].update_idletasks()
            print("Layout update completed")
        except Exception as e:
            print(f"Error in force_layout_update: {e}")

    def start_ui_update_thread(self):
        """Start thread to handle UI updates from other threads"""
        print("Start thread to handle UI updates from other threads")
        def ui_updater():
            while True:
                try:
                    update_func = self.ui_update_queue.get(timeout=0.001)
                    if update_func:
                        self.root.after_idle(update_func)
                except pyqueue.Empty:
                    continue
                except Exception as e:
                    print(f"UI update error: {e}")
        ui_thread = threading.Thread(target=ui_updater, daemon=True)
        ui_thread.start()

    def start_event_update_thread(self):
        """Start separate thread for event updates"""
        def event_updater():
            while True:
                try:
                    current_time = time.time()
                    if current_time - self.last_event_update >= self.event_update_interval:
                        self.fetch_and_cache_events()
                        self.last_event_update = current_time
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Event update error: {e}")
                    time.sleep(1)
        event_thread = threading.Thread(target=event_updater, daemon=True)
        event_thread.start()

    def fetch_and_cache_events(self):
        """Fetch events and queue UI update if changed"""
        try:
            temp = self.obj_db.fetch_latest_events()
            print(f"Fetched {len(temp)} events from database")
            new_events = []
            if temp:
                for data in temp[:10]:
                    ts = data[6]
                    event_time = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                    event_data = {
                        "id": data[0],
                        "Camera Name": data[1] or "Unknown",
                        "image_frame": data[2],
                        "Helmet": str(data[3]) or "N/A",
                        "Vest": str(data[4]) or "N/A",
                        "Shoes": str(data[5]) or "N/A",
                        "Timestamp": event_time,
                        "status": "✓" if all([data[3], data[4], data[5]]) else "✗"
                    }
                    new_events.append(event_data)
                    print(f"Processed event: {event_data['id']}")
            else:
                print("No events returned from database")
            with self.event_update_lock:
                if new_events != self.event_cache:
                    self.event_cache = new_events.copy()
                    print(f"Updated event cache with {len(new_events)} events")
                    self.ui_update_queue.put(self.update_detection_sidebar)
                else:
                    print("No changes in event cache")
        except Exception as e:
            print(f"Error fetching events: {e}")

    def update_detection_sidebar(self):
        """Update the detection sidebar with cached events"""
        try:
            self.sidebar.grid()
            self.scrollable_frame.grid()
            print("Sidebar visibility: %s, Scrollable frame: %s" % (self.sidebar.winfo_viewable(), self.scrollable_frame.winfo_viewable()))
            events = list(self.event_cache)
            print(f"Updating sidebar with {len(events)} events")
            if not self.details_frames:
                print("⚠️ details_frames not initialized")
                return
            for frame in self.details_frames:
                frame['active'] = False
                frame['img_label'].configure(image=None, text="No Image")
                for widget in frame['info_frame'].winfo_children():
                    widget.destroy()
                frame['frame'].grid()
            for i, event in enumerate(events):
                if i >= len(self.details_frames):
                    print(f"Skipping event {i}, not enough frames")
                    break
                frame = self.details_frames[i]
                frame['active'] = True
                print(f"Updating frame {i} with event ID {event['id']}")
                if event.get("image_frame"):
                    try:
                        img_data = base64.b64decode(event["image_frame"])
                        image = Image.open(io.BytesIO(img_data))
                        image.thumbnail((240, 200), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        frame['img_label'].configure(image=photo, text="")
                        frame['img_label'].image = photo
                        print(f"Loaded image for event {event['id']}")
                    except Exception as e:
                        print(f"Image processing error for event {event['id']}: {e}")
                        frame['img_label'].configure(text="Invalid Image")
                else:
                    frame['img_label'].configure(text="No Image")
                    print(f"No image data for event {event['id']}")
                info_items = [
                    ("Event ID", event['id']),
                    ("Camera", event['Camera Name']),
                    ("Helmet", event['Helmet']),
                    ("Vest", event['Vest']),
                    ("Shoes", event['Shoes']),
                    ("Timestamp", event['Timestamp']),
                    ("Status", event['status'])
                ]
                for idx, (label, value) in enumerate(info_items):
                    info_label = ctk.CTkLabel(
                        frame['info_frame'],
                        text=f"{label}: {value}",
                        font=ctk.CTkFont(size=12, weight="bold"),
                        text_color="black",
                        anchor="w"
                    )
                    info_label.grid(row=idx, column=0, sticky="w", padx=8, pady=1)
                    print(f"Added label {label}: {value} to frame {i}")
            for i in range(len(events), len(self.details_frames)):
                frame = self.details_frames[i]
                frame['frame'].grid_remove()
                print(f"Hiding unused frame {i}")
            self.sidebar.update_idletasks()
            self.scrollable_frame.update_idletasks()
            print("Sidebar update completed")
        except Exception as e:
            print(f"Error updating detection sidebar: {e}")

    def start_video_feed(self):
        """Start video feed from cameras"""
        if self.is_running:
            return
        self.is_running = True
        self.video_thread = threading.Thread(target=self._video_loop, daemon=True)
        self.video_thread.start()

    def _video_loop(self):
        """Real-time video loop (show every frame in order, no skipping)"""
        while self.is_running:
            try:
                latest_frames = {}
                try:
                    cam_id, frame = frame_queue_to_show.get_nowait()
                    if frame is not None:
                        latest_frames[cam_id] = frame
                except pyqueue.Empty:
                    pass
                for cam_id, frame in latest_frames.items():
                    display_idx = cam_id % self.max_cameras_display
                    if display_idx >= self.max_cameras_display:
                        continue
                    cols = self.grid_config['cols']
                    rows = self.grid_config['rows']
                    display_size = (
                        self.live_feed_width // cols ,
                        self.live_feed_height // rows 
                    )
                    frame_resized = cv2.resize(frame, display_size)
                    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame_rgb)
                    photo = ImageTk.PhotoImage(image=image)
                    def update_label(idx=display_idx, p=photo):
                        if idx < len(self.camera_labels):
                            self.camera_labels[idx].configure(image=p, text="")
                            self.camera_labels[idx].image = p
                    self.ui_update_queue.put(update_label)
            except Exception as e:
                print(f"Video loop error: {e}")
            time.sleep(0.001)

    def update_camera_display(self, camera_idx, photo):
        """Update specific camera display with new frame"""
        try:
            if camera_idx < len(self.camera_labels):
                self.camera_labels[camera_idx].configure(image=photo, text="")
                self.camera_labels[camera_idx].image = photo
        except Exception as e:
            print(f"Camera {camera_idx} display update error: {e}")

    def start_demo_updates(self):
        """Start demo updates"""
        self.start_video_feed()
        self.fetch_and_cache_events()
        self.root.after(100, self.update_detection_sidebar)
        print("Demo updates started with initial sidebar refresh")

    def reset_interface(self):
        """Reset the interface"""
        self.setup_surveillance_ui()
        self.start_ui_update_thread()
        self.start_demo_updates()

    def run(self):
        """Run the main loop"""
        try:
            self.root.mainloop()
        finally:
            self.is_running = False
            if self.cap:
                self.cap.release()