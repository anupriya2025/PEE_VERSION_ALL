import io
import platform
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import datetime
import threading
import time
import numpy as np
from core.database import EventDatabase
import base64
from io import BytesIO
from PIL import Image
import queue
import math

# Set appearance mode and color theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class EventFeedMonitor:
    def __init__(self):
        # Initialize main window
        self.root = ctk.CTk()
        self.root.title("Historical Events Viewer")
        self.root.geometry("1900x1000")
        self.root.minsize(1900, 1000)
        if platform.system() == "Windows":
            self.root.state('zoomed')
        else:
            self.root.attributes('-zoomed', True)

        # Configure root grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Database and events
        self.obj_db = EventDatabase()
        self.all_events = []
        self.filtered_events = []
        self.current_page = 0
        self.events_per_page = 12
        self.total_pages = 0
        
        # Statistics
        self.total_events = 0
        self.helmet_compliant = 0
        self.vest_compliant = 0
        self.shoes_compliant = 0
        
        # Event update optimization
        self.last_event_update = 0
        self.event_update_interval = 5.0  # Update every 5 seconds for historical data
        self.event_update_lock = threading.Lock()
        
        # UI update queue for thread safety
        self.ui_update_queue = queue.Queue()
        
        # Filter variables
        self.filter_camera = tk.StringVar(value="All Cameras")
        self.filter_helmet = tk.StringVar(value="All")
        self.filter_vest = tk.StringVar(value="All")
        self.filter_shoes = tk.StringVar(value="All")
        self.filter_date = tk.StringVar(value="All Dates")
        
        self.setup_historical_ui()
        self.start_ui_update_thread()
        self.start_event_update_thread()
        self.load_historical_events()

    def setup_historical_ui(self):
        """Create historical events UI layout"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Create header with statistics and title
        self.create_header_with_statistics()
        
        # Create main content area
        self.create_main_content()

    def create_header_with_statistics(self):
        """Create header section with statistics and title"""
        self.main_content = ctk.CTkFrame(self.main_frame, fg_color="#F1F5FA")
        self.main_content.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.main_content.grid_columnconfigure(1, weight=1)
        
        # Statistics frame
        stats_frame = ctk.CTkFrame(self.main_content, fg_color="#F1F5FA")
        stats_frame.grid(row=0, column=0, padx=(0, 15), sticky="ns")
        
        # Total Events counter
        total_frame = ctk.CTkFrame(stats_frame, fg_color="#E3F2FD")
        total_frame.grid(row=0, column=0, padx=(0, 10))
        
        total_label = ctk.CTkLabel(total_frame, text="Total Events", font=("", 16), text_color="#1976D2")
        total_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.total_count = ctk.CTkLabel(
            total_frame, text="0", font=("", 18, "bold"), text_color="#1976D2",
            width=50, height=30, fg_color="#BBDEFB", corner_radius=6
        )
        self.total_count.grid(row=0, column=1, padx=10, pady=5)
        
        # Helmet Compliance
        helmet_frame = ctk.CTkFrame(stats_frame, fg_color="#E8F5E9")
        helmet_frame.grid(row=0, column=1, padx=(0, 10))
        
        helmet_label = ctk.CTkLabel(helmet_frame, text="Helmet ✓", font=("", 16), text_color="#2E7D32")
        helmet_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.helmet_count = ctk.CTkLabel(
            helmet_frame, text="0", font=("", 18, "bold"), text_color="#2E7D32",
            width=50, height=30, fg_color="#C8E6C9", corner_radius=6
        )
        self.helmet_count.grid(row=0, column=1, padx=10, pady=5)
        
        # Vest Compliance
        vest_frame = ctk.CTkFrame(stats_frame, fg_color="#FFF3E0")
        vest_frame.grid(row=0, column=2, padx=(0, 10))
        
        vest_label = ctk.CTkLabel(vest_frame, text="Vest ✓", font=("", 16), text_color="#F57C00")
        vest_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.vest_count = ctk.CTkLabel(
            vest_frame, text="0", font=("", 18, "bold"), text_color="#F57C00",
            width=50, height=30, fg_color="#FFE0B2", corner_radius=6
        )
        self.vest_count.grid(row=0, column=1, padx=10, pady=5)
        
        # Shoes Compliance
        shoes_frame = ctk.CTkFrame(stats_frame, fg_color="#F3E5F5")
        shoes_frame.grid(row=0, column=3)
        
        shoes_label = ctk.CTkLabel(shoes_frame, text="Shoes ✓", font=("", 16), text_color="#7B1FA2")
        shoes_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.shoes_count = ctk.CTkLabel(
            shoes_frame, text="0", font=("", 18, "bold"), text_color="#7B1FA2",
            width=50, height=30, fg_color="#E1BEE7", corner_radius=6
        )
        self.shoes_count.grid(row=0, column=1, padx=10, pady=5)
        
        # Title
        title = ctk.CTkLabel(
            self.main_content, text="Historical Events Archive", font=("", 23, "bold"),
            text_color="#000000"
        )
        title.grid(row=0, column=1, pady=(0, 10), padx=(200, 0), sticky="w")

    def create_main_content(self):
        """Create main content area with filters and events grid"""
        self.content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)
        
        # Create filters section
        self.create_filters_section()
        
        # Create events grid
        self.create_events_grid()
        
        # Create pagination controls
        self.create_pagination_controls()

    def create_filters_section(self):
        """Create filters section"""
        filters_frame = ctk.CTkFrame(self.content, fg_color="#F5F5F5", height=80)
        filters_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filters_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        filters_frame.grid_propagate(False)
        
        # Filter title
        filter_title = ctk.CTkLabel(filters_frame, text="Filters:", font=("", 16, "bold"))
        filter_title.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Camera filter
        camera_label = ctk.CTkLabel(filters_frame, text="Camera:", font=("", 12))
        camera_label.grid(row=0, column=1, padx=(10, 5), pady=(5, 0), sticky="sw")
        
        self.camera_combo = ctk.CTkComboBox(
            filters_frame, values=["All Cameras"], variable=self.filter_camera,
            command=self.apply_filters, width=120, height=28
        )
        self.camera_combo.grid(row=0, column=1, padx=(10, 5), pady=(25, 10), sticky="nw")
        
        # Helmet filter
        helmet_label = ctk.CTkLabel(filters_frame, text="Helmet:", font=("", 12))
        helmet_label.grid(row=0, column=2, padx=5, pady=(5, 0), sticky="sw")
        
        self.helmet_combo = ctk.CTkComboBox(
            filters_frame, values=["All", "Yes", "No"], variable=self.filter_helmet,
            command=self.apply_filters, width=80, height=28
        )
        self.helmet_combo.grid(row=0, column=2, padx=5, pady=(25, 10), sticky="nw")
        
        # Vest filter
        vest_label = ctk.CTkLabel(filters_frame, text="Vest:", font=("", 12))
        vest_label.grid(row=0, column=3, padx=5, pady=(5, 0), sticky="sw")
        
        self.vest_combo = ctk.CTkComboBox(
            filters_frame, values=["All", "Yes", "No"], variable=self.filter_vest,
            command=self.apply_filters, width=80, height=28
        )
        self.vest_combo.grid(row=0, column=3, padx=5, pady=(25, 10), sticky="nw")
        
        # Shoes filter
        shoes_label = ctk.CTkLabel(filters_frame, text="Shoes:", font=("", 12))
        shoes_label.grid(row=0, column=4, padx=5, pady=(5, 0), sticky="sw")
        
        self.shoes_combo = ctk.CTkComboBox(
            filters_frame, values=["All", "Yes", "No"], variable=self.filter_shoes,
            command=self.apply_filters, width=80, height=28
        )
        self.shoes_combo.grid(row=0, column=4, padx=5, pady=(25, 10), sticky="nw")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            filters_frame, text="🔄 Refresh", command=self.load_historical_events,
            width=100, height=35, font=("", 12, "bold")
        )
        refresh_btn.grid(row=0, column=5, padx=(10, 10), pady=20, sticky="e")

    def create_events_grid(self):
        """Create scrollable grid for events"""
        # Create scrollable frame
        self.events_container = ctk.CTkScrollableFrame(
            self.content, fg_color="#FFFFFF", corner_radius=5
        )
        self.events_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        # Configure grid for events (4 columns)
        for i in range(4):
            self.events_container.grid_columnconfigure(i, weight=1)
        
        self.event_frames = []

    def create_event_card(self, event, row, col):
        """Create individual event card"""
        # Main card frame
        card_frame = ctk.CTkFrame(
            self.events_container, fg_color="white", corner_radius=8,
            border_width=2, border_color="#E0E0E0", width=300, height=250
        )
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card_frame.grid_propagate(False)
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure(0, weight=1)
        card_frame.grid_rowconfigure(1, weight=0)
        
        # Image frame
        img_frame = ctk.CTkFrame(card_frame, fg_color="#f8f8f8", height=150)
        img_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        img_frame.grid_propagate(False)
        img_frame.grid_columnconfigure(0, weight=1)
        img_frame.grid_rowconfigure(0, weight=1)
        
        # Image label
        img_label = ctk.CTkLabel(img_frame, text="Loading...", fg_color="#f8f8f8")
        img_label.grid(row=0, column=0, sticky="nsew")
        
        # Load and display image
        try:
            if event.get("image_frame"):
                img_data = base64.b64decode(event["image_frame"])
                image = Image.open(io.BytesIO(img_data))
                image.thumbnail((280, 240), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                img_label.configure(image=photo, text="")
                img_label.image = photo
        except Exception as e:
            img_label.configure(text="No Image Available")
            print(f"Image processing error: {e}")
        
        # Info frame
        info_frame = ctk.CTkFrame(card_frame, fg_color="white", height=90)
        info_frame.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")
        info_frame.grid_propagate(False)
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Event info
        event_id_label = ctk.CTkLabel(
            info_frame, text=f"Event ID: {event['id']}", 
            font=("", 12, "bold"), anchor="w"
        )
        event_id_label.grid(row=0, column=0, padx=8, pady=2, sticky="w")
        
        camera_label = ctk.CTkLabel(
            info_frame, text=f"Camera: {event['Camera Name']}", 
            font=("", 11), anchor="w"
        )
        camera_label.grid(row=1, column=0, padx=8, pady=1, sticky="w")
        
        # Compliance indicators
        compliance_frame = ctk.CTkFrame(info_frame, fg_color="white")
        compliance_frame.grid(row=2, column=0, padx=8, pady=2, sticky="w")
        
        # Helmet status
        helmet_color = "#4CAF50" if event['Helmet'] == "Yes" else "#F44336"
        helmet_text = "✓" if event['Helmet'] == "Yes" else "✗"
        helmet_indicator = ctk.CTkLabel(
            compliance_frame, text=f"H:{helmet_text}", font=("", 20, "bold"),
            text_color=helmet_color, width=35
        )
        helmet_indicator.grid(row=0, column=0, padx=2)
        
        # Vest status
        vest_color = "#4CAF50" if event['Vest'] == "Yes" else "#F44336"
        vest_text = "✓" if event['Vest'] == "Yes" else "✗"
        vest_indicator = ctk.CTkLabel(
            compliance_frame, text=f"V:{vest_text}", font=("",  20, "bold"),
            text_color=vest_color, width=35
        )
        vest_indicator.grid(row=0, column=1, padx=2)
        
        # Shoes status
        shoes_color = "#4CAF50" if event['Shoes'] == "Yes" else "#F44336"
        shoes_text = "✓" if event['Shoes'] == "Yes" else "✗"
        shoes_indicator = ctk.CTkLabel(
            compliance_frame, text=f"S:{shoes_text}", font=("",  20, "bold"),
            text_color=shoes_color, width=35
        )
        shoes_indicator.grid(row=0, column=2, padx=2)
        
        # Timestamp (if available)
        if event.get('timestamp'):
            time_label = ctk.CTkLabel(
                info_frame, text=f"Time: {event['timestamp']}", 
                font=("", 9), anchor="w", text_color="#666666"
            )
            time_label.grid(row=3, column=0, padx=8, pady=1, sticky="w")
        
        return card_frame

    def create_pagination_controls(self):
        """Create pagination controls"""
        pagination_frame = ctk.CTkFrame(self.content, fg_color="#F5F5F5", height=60)
        pagination_frame.grid(row=2, column=0, sticky="ew")
        pagination_frame.grid_columnconfigure(1, weight=1)
        pagination_frame.grid_propagate(False)
        
        # Previous button
        self.prev_btn = ctk.CTkButton(
            pagination_frame, text="◀ Previous", command=self.previous_page,
            width=100, height=35, state="disabled"
        )
        self.prev_btn.grid(row=0, column=0, padx=20, pady=12, sticky="w")
        
        # Page info
        self.page_info = ctk.CTkLabel(
            pagination_frame, text="Page 0 of 0", font=("", 14, "bold")
        )
        self.page_info.grid(row=0, column=1, pady=12)
        
        # Next button
        self.next_btn = ctk.CTkButton(
            pagination_frame, text="Next ▶", command=self.next_page,
            width=100, height=35, state="disabled"
        )
        self.next_btn.grid(row=0, column=2, padx=20, pady=12, sticky="e")

    def load_historical_events(self):
        """Load all historical events from database"""
        try:
            events_data = self.obj_db.fetch_latest_All_events()  # Assuming this method exists
            self.all_events = []
            
            if events_data:
                # Get unique cameras for filter
                cameras = set()
                
                for data in events_data:
                    event = {
                        "id": data[0], 
                        "Camera Name": data[1],
                        "image_frame": data[2], 
                        "Helmet": data[3],
                        "Vest": data[4],
                        "Shoes": data[5],
                        "timestamp": None
                    }
                    self.all_events.append(event)
                    cameras.add(data[1])
                
                # Update camera filter options
                camera_options = ["All Cameras"] + sorted(list(cameras))
                self.camera_combo.configure(values=camera_options)
                
                # Calculate statistics
                self.calculate_statistics()
                
                # Apply initial filters and display
                self.apply_filters()
                
        except Exception as e:
            print(f"Error loading historical events: {e}")
            # If fetch_all_events doesn't exist, try to use existing method
            try:
                temp = self.obj_db.fetch_latest_events()
                if temp:
                    cameras = set()
                    for data in temp:
                        event = {
                            "id": data[0], 
                            "Camera Name": data[1],
                            "image_frame": data[2], 
                            "Helmet": data[3],
                            "Vest": data[4],
                            "Shoes": data[5],
                            "timestamp": None
                        }
                        self.all_events.append(event)
                        cameras.add(data[1])
                    
                    camera_options = ["All Cameras"] + sorted(list(cameras))
                    self.camera_combo.configure(values=camera_options)
                    self.calculate_statistics()
                    self.apply_filters()
            except Exception as e2:
                print(f"Error with fallback method: {e2}")

    def calculate_statistics(self):
        """Calculate statistics from all events"""
        self.total_events = len(self.all_events)
        self.helmet_compliant = sum(1 for event in self.all_events if event['Helmet'] == "Yes")
        self.vest_compliant = sum(1 for event in self.all_events if event['Vest'] == "Yes")
        self.shoes_compliant = sum(1 for event in self.all_events if event['Shoes'] == "Yes")
        
        # Update statistics display
        self.ui_update_queue.put(lambda: self.update_statistics_display())

    def update_statistics_display(self):
        """Update statistics display in header"""
        try:
            self.total_count.configure(text=str(self.total_events))
            self.helmet_count.configure(text=str(self.helmet_compliant))
            self.vest_count.configure(text=str(self.vest_compliant))
            self.shoes_count.configure(text=str(self.shoes_compliant))
        except Exception as e:
            print(f"Error updating statistics display: {e}")

    def apply_filters(self, *args):
        """Apply filters to events"""
        self.filtered_events = self.all_events.copy()
        
        # Apply camera filter
        if self.filter_camera.get() != "All Cameras":
            self.filtered_events = [e for e in self.filtered_events 
                                  if e['Camera Name'] == self.filter_camera.get()]
        
        # Apply helmet filter
        if self.filter_helmet.get() != "All":
            self.filtered_events = [e for e in self.filtered_events 
                                  if e['Helmet'] == self.filter_helmet.get()]
        
        # Apply vest filter
        if self.filter_vest.get() != "All":
            self.filtered_events = [e for e in self.filtered_events 
                                  if e['Vest'] == self.filter_vest.get()]
        
        # Apply shoes filter
        if self.filter_shoes.get() != "All":
            self.filtered_events = [e for e in self.filtered_events 
                                  if e['Shoes'] == self.filter_shoes.get()]
        
        # Reset to first page
        self.current_page = 0
        self.update_events_display()

    def update_events_display(self):
        """Update events display with current page"""
        # Clear existing event cards
        for widget in self.events_container.winfo_children():
            widget.destroy()
        
        # Calculate pagination
        total_filtered = len(self.filtered_events)
        self.total_pages = max(1, math.ceil(total_filtered / self.events_per_page))
        
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
        
        # Get events for current page
        start_idx = self.current_page * self.events_per_page
        end_idx = min(start_idx + self.events_per_page, total_filtered)
        current_events = self.filtered_events[start_idx:end_idx]
        
        # Display events in grid (4 columns)
        for i, event in enumerate(current_events):
            row = i // 4
            col = i % 4
            self.create_event_card(event, row, col)
        
        # Update pagination controls
        self.update_pagination_controls()

    def update_pagination_controls(self):
        """Update pagination control states"""
        # Update page info
        if self.total_pages > 0:
            self.page_info.configure(text=f"Page {self.current_page + 1} of {self.total_pages}")
        else:
            self.page_info.configure(text="No events found")
        
        # Update button states
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < self.total_pages - 1 else "disabled")

    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_events_display()

    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_events_display()

    def start_ui_update_thread(self):
        """Start thread to handle UI updates from other threads"""
        def ui_updater():
            while True:
                try:
                    update_func = self.ui_update_queue.get(timeout=0.01)
                    if update_func:
                        self.root.after_idle(update_func)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"UI update error: {e}")
                    
        ui_thread = threading.Thread(target=ui_updater, daemon=True)
        ui_thread.start()

    def start_event_update_thread(self):
        """Start separate thread for periodic event updates"""
        def event_updater():
            while True:
                try:
                    current_time = time.time()
                    if current_time - self.last_event_update >= self.event_update_interval:
                        self.ui_update_queue.put(lambda: self.load_historical_events())
                        self.last_event_update = current_time
                    time.sleep(1)
                except Exception as e:
                    print(f"Event update error: {e}")
                    time.sleep(5)
                    
        event_thread = threading.Thread(target=event_updater, daemon=True)
        event_thread.start()
        
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Application error: {e}")

if __name__ == "__main__":
    app = EventFeedMonitor()
    app.run()