import customtkinter as ctk
from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkComboBox, CTkEntry
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import threading
import time
import queue
import math
from core.camera import CameraDatabase



class CameraManagementInterface(CTkFrame):
    def __init__(self, parent, *args, root_width: int = 1920, root_height: int = 1080, **kwargs):
        super().__init__(parent, *args, **kwargs)
        print("********************************************* Camera Management Interface *******************************************************************")
        
        self.root = parent
        self.winfo_toplevel().title("Camera Management")
        self.winfo_toplevel().geometry(f"{root_width}x{root_height}")

        # Configure root grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Database and cameras
        self.obj_db = CameraDatabase()
        self.all_cameras = []
        self.filtered_cameras = []
        self.current_page = 0
        self.cameras_per_page = 12
        self.total_pages = 0

        # Statistics
        self.total_cameras = 0

        # Camera update optimization
        self.last_camera_update = 0
        self.camera_update_interval = 5.0  # Update every 5 seconds
        self.camera_update_lock = threading.Lock()

        # UI update queue for thread safety
        self.ui_update_queue = queue.Queue()

        # Filter variables
        self.filter_direction = tk.StringVar(value="All Directions")

        # Selected camera for editing
        self.selected_camera = None

        self.setup_camera_ui()
        self.start_ui_update_thread()
        self.start_camera_update_thread()
        self.load_cameras()

    def setup_camera_ui(self):
        print("Create camera management UI layout")
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
        print("Create header section with statistics and title")
        self.main_content = ctk.CTkFrame(self.main_frame, fg_color="#F1F5FA")
        self.main_content.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.main_content.grid_columnconfigure(1, weight=1)

        # Statistics frame
        stats_frame = ctk.CTkFrame(self.main_content, fg_color="#F1F5FA")
        stats_frame.grid(row=0, column=0, padx=(0, 15), sticky="ns")

        # Total Cameras counter
        total_frame = ctk.CTkFrame(stats_frame, fg_color="#E3F2FD")
        total_frame.grid(row=0, column=0, padx=(0, 10))

        total_label = ctk.CTkLabel(total_frame, text="Total Cameras", font=("", 16), text_color="#1976D2")
        total_label.grid(row=0, column=0, padx=10, pady=5)

        self.total_count = ctk.CTkLabel(
            total_frame, text="0", font=("", 18, "bold"), text_color="#1976D2",
            width=50, height=30, fg_color="#BBDEFB", corner_radius=6
        )
        self.total_count.grid(row=0, column=1, padx=10, pady=5)

        # Title
        title = ctk.CTkLabel(
            self.main_content, text="Camera Management", font=("", 23, "bold"),
            text_color="#000000"
        )
        title.grid(row=0, column=1, pady=(0, 10), padx=(200, 0), sticky="w")

    def create_main_content(self):
        print("Create main content area with form, filters, and cameras grid")
        self.content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        # Create form section
        self.create_form_section()

        # Create filters section
        self.create_filters_section()

        # Create cameras grid
        self.create_cameras_grid()

        # Create pagination controls
        self.create_pagination_controls()

    def create_form_section(self):
        print("Create form section for adding/editing cameras")
        self.form_frame = ctk.CTkFrame(self.content, fg_color="#F5F5F5", height=120)
        self.form_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.form_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.form_frame.grid_propagate(False)

        # Form title
        form_title = ctk.CTkLabel(self.form_frame, text="Camera Details:", font=("", 16, "bold"))
        form_title.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Camera Name
        name_label = ctk.CTkLabel(self.form_frame, text="Camera Name:", font=("", 12))
        name_label.grid(row=0, column=1, padx=(10, 5), pady=(5, 0), sticky="sw")
        self.name_var = tk.StringVar()
        self.name_entry = ctk.CTkEntry(self.form_frame, textvariable=self.name_var, width=200, height=28)
        self.name_entry.grid(row=0, column=1, padx=(10, 5), pady=(25, 10), sticky="nw")

        # Camera Direction
        direction_label = ctk.CTkLabel(self.form_frame, text="Direction:", font=("", 12))
        direction_label.grid(row=0, column=2, padx=5, pady=(5, 0), sticky="sw")
        self.direction_var = tk.StringVar()
        self.direction_entry = ctk.CTkEntry(self.form_frame, textvariable=self.direction_var, width=150, height=28)
        self.direction_entry.grid(row=0, column=2, padx=5, pady=(25, 10), sticky="nw")

        # URL
        url_label = ctk.CTkLabel(self.form_frame, text="URL:", font=("", 12))
        url_label.grid(row=0, column=3, padx=5, pady=(5, 0), sticky="sw")
        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(self.form_frame, textvariable=self.url_var, width=300, height=28)
        self.url_entry.grid(row=0, column=3, padx=5, pady=(25, 10), sticky="nw")

        # Buttons
        self.add_btn = ctk.CTkButton(
            self.form_frame, text="Add Camera", command=self.add_camera, width=100, height=35, font=("", 12, "bold")
        )
        self.add_btn.grid(row=0, column=4, padx=(10, 5), pady=20)

        self.edit_btn = ctk.CTkButton(
            self.form_frame, text="Edit Camera", command=self.edit_camera, width=100, height=35, font=("", 12, "bold"), state="disabled"
        )
        self.edit_btn.grid(row=0, column=5, padx=(5, 10), pady=20)

    def create_filters_section(self):
        print("Create filters section")
        filters_frame = ctk.CTkFrame(self.content, fg_color="#F5F5F5", height=80)
        filters_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        filters_frame.grid_columnconfigure((0, 1, 2), weight=1)
        filters_frame.grid_propagate(False)

        # Filter title
        filter_title = ctk.CTkLabel(filters_frame, text="Filters:", font=("", 16, "bold"))
        filter_title.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Direction filter
        direction_label = ctk.CTkLabel(filters_frame, text="Direction:", font=("", 12))
        direction_label.grid(row=0, column=1, padx=(10, 5), pady=(5, 0), sticky="sw")
        self.direction_combo = ctk.CTkComboBox(
            filters_frame, values=["All Directions"], variable=self.filter_direction,
            command=self.apply_filters, width=150, height=28
        )
        self.direction_combo.grid(row=0, column=1, padx=(10, 5), pady=(25, 10), sticky="nw")

        # Refresh button
        refresh_btn = ctk.CTkButton(
            filters_frame, text="🔄 Refresh", command=self.load_cameras,
            width=100, height=35, font=("", 12, "bold")
        )
        refresh_btn.grid(row=0, column=2, padx=(10, 10), pady=20, sticky="e")

    def create_cameras_grid(self):
        print("Create scrollable grid for cameras")
        self.cameras_container = ctk.CTkScrollableFrame(self.content, fg_color="#FFFFFF", corner_radius=5)
        self.cameras_container.grid(row=2, column=0, sticky="nsew", pady=(0, 10))

        # Configure grid for cameras (4 columns)
        for i in range(4):
            self.cameras_container.grid_columnconfigure(i, weight=1)

        self.camera_frames = []

    def create_camera_card(self, camera, row, col):
        print("Create individual camera card")
        card_frame = ctk.CTkFrame(
            self.cameras_container, fg_color="white", corner_radius=8,
            border_width=2, border_color="#E0E0E0", width=300, height=150
        )
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card_frame.grid_propagate(False)
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure((0, 1, 2), weight=0)

        # Camera Name
        name_label = ctk.CTkLabel(
            card_frame, text=f"Name: {camera['Camera_name']}", font=("", 12, "bold"), anchor="w"
        )
        name_label.grid(row=0, column=0, padx=8, pady=5, sticky="w")

        # Camera Direction
        direction_label = ctk.CTkLabel(
            card_frame, text=f"Direction: {camera['Camera_direction']}", font=("", 11), anchor="w"
        )
        direction_label.grid(row=1, column=0, padx=8, pady=5, sticky="w")

        # URL
        url_label = ctk.CTkLabel(
            card_frame, text=f"URL: {camera['URL']}", font=("", 11), anchor="w", wraplength=280
        )
        url_label.grid(row=2, column=0, padx=8, pady=5, sticky="w")

        # Delete button
        delete_btn = ctk.CTkButton(
            card_frame, text="Delete", command=lambda: self.delete_camera(camera['Camera_name']),
            width=80, height=28, font=("", 10, "bold"), fg_color="#F44336", hover_color="#D32F2F"
        )
        delete_btn.grid(row=0, column=1, padx=8, pady=5, sticky="ne")

        # Select for editing
        card_frame.bind("<Button-1>", lambda e: self.select_camera(camera))
        for widget in card_frame.winfo_children():
            widget.bind("<Button-1>", lambda e: self.select_camera(camera))

        return card_frame

    def create_pagination_controls(self):
        print("Create pagination controls")
        pagination_frame = ctk.CTkFrame(self.content, fg_color="#F5F5F5", height=60)
        pagination_frame.grid(row=3, column=0, sticky="ew")
        pagination_frame.grid_columnconfigure(1, weight=1)
        pagination_frame.grid_propagate(False)

        # Previous button
        self.prev_btn = ctk.CTkButton(
            pagination_frame, text="◀ Previous", command=self.previous_page,
            width=100, height=35, state="disabled"
        )
        self.prev_btn.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        # Page info
        self.page_info = ctk.CTkLabel(pagination_frame, text="Page 0 of 0", font=("", 14, "bold"))
        self.page_info.grid(row=0, column=1, pady=12)

        # Next button
        self.next_btn = ctk.CTkButton(
            pagination_frame, text="Next ▶", command=self.next_page,
            width=100, height=35, state="disabled"
        )
        self.next_btn.grid(row=0, column=2, padx=20, pady=12, sticky="e")

    def load_cameras(self):
        print("Load all cameras from database")
        try:
            cameras_data = self.obj_db.fetch_all_cameras(100)
            self.all_cameras = []

            if cameras_data:
                # Get unique directions for filter
                directions = set()

                for data in cameras_data:
                    camera = {
                        "Camera_name": data[0],
                        "Camera_direction": data[1],
                        "URL": data[2]
                    }
                    self.all_cameras.append(camera)
                    directions.add(data[1])

                # Update direction filter options
                direction_options = ["All Directions"] + sorted(list(directions))
                self.direction_combo.configure(values=direction_options)

                # Calculate statistics
                self.calculate_statistics()

                # Apply initial filters and display
                self.apply_filters()

        except Exception as e:
            print(f"Error loading cameras: {e}")
            messagebox.showerror("Database Error", f"Error loading cameras: {e}")

    def calculate_statistics(self):
        print("Calculate statistics from all cameras")
        self.total_cameras = len(self.all_cameras)
        self.ui_update_queue.put(lambda: self.update_statistics_display())

    def update_statistics_display(self):
        print("Update statistics display in header")
        try:
            self.total_count.configure(text=str(self.total_cameras))
        except Exception as e:
            print(f"Error updating statistics display: {e}")

    def apply_filters(self, *args):
        print("Apply filters to cameras")
        self.filtered_cameras = self.all_cameras.copy()

        # Apply direction filter
        if self.filter_direction.get() != "All Directions":
            self.filtered_cameras = [c for c in self.filtered_cameras
                                    if c['Camera_direction'] == self.filter_direction.get()]

        # Reset to first page
        self.current_page = 0
        self.update_cameras_display()

    def update_cameras_display(self):
        print("Update cameras display with current page")
        # Clear existing camera cards
        for widget in self.cameras_container.winfo_children():
            widget.destroy()

        # Calculate pagination
        total_filtered = len(self.filtered_cameras)
        self.total_pages = max(1, math.ceil(total_filtered / self.cameras_per_page))

        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)

        # Get cameras for current page
        start_idx = self.current_page * self.cameras_per_page
        end_idx = min(start_idx + self.cameras_per_page, total_filtered)
        current_cameras = self.filtered_cameras[start_idx:end_idx]

        # Display cameras in grid (4 columns)
        for i, camera in enumerate(current_cameras):
            row = i // 4
            col = i % 4
            self.create_camera_card(camera, row, col)

        # Update pagination controls
        self.update_pagination_controls()

    def update_pagination_controls(self):
        print("Update pagination control states")
        if self.total_pages > 0:
            self.page_info.configure(text=f"Page {self.current_page + 1} of {self.total_pages}")
        else:
            self.page_info.configure(text="No cameras found")

        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < self.total_pages - 1 else "disabled")

    def previous_page(self):
        print("Go to previous page")
        if self.current_page > 0:
            self.current_page -= 1
            self.update_cameras_display()

    def next_page(self):
        print("Go to next page")
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_cameras_display()

    def add_camera(self):
        print("Add new camera")
        name = self.name_var.get()
        direction = self.direction_var.get()
        url = self.url_var.get()

        if not all([name, direction, url]):
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            self.obj_db.add_camera(name, direction, url)
            self.load_cameras()
            self.clear_form()
            messagebox.showinfo("Success", "Camera added successfully!")
        except pyodbc.Error as e:
            messagebox.showerror("Database Error", f"Error adding camera: {e}")

    def edit_camera(self):
        print("Edit selected camera")
        if not self.selected_camera:
            messagebox.showerror("Error", "Please select a camera to edit!")
            return

        name = self.name_var.get()
        direction = self.direction_var.get()
        url = self.url_var.get()

        if not all([name, direction, url]):
            messagebox.showerror("Error", "All fields are required!")
            return

        try:
            self.obj_db.update_camera(name, direction, url)
            self.load_cameras()
            self.clear_form()
            messagebox.showinfo("Success", "Camera updated successfully!")
        except pyodbc.Error as e:
            messagebox.showerror("Database Error", f"Error updating camera: {e}")

    def delete_camera(self, camera_name):
        print(f"Delete camera: {camera_name}")
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete camera '{camera_name}'?"):
            try:
                self.obj_db.delete_camera(camera_name)
                self.load_cameras()
                self.clear_form()
                messagebox.showinfo("Success", "Camera deleted successfully!")
            except pyodbc.Error as e:
                messagebox.showerror("Database Error", f"Error deleting camera: {e}")

    def select_camera(self, camera):
        print(f"Select camera: {camera['Camera_name']}")
        self.selected_camera = camera
        self.name_var.set(camera['Camera_name'])
        self.direction_var.set(camera['Camera_direction'])
        self.url_var.set(camera['URL'])
        self.edit_btn.configure(state="normal")

    def clear_form(self):
        print("Clear form")
        self.name_var.set("")
        self.direction_var.set("")
        self.url_var.set("")
        self.selected_camera = None
        self.edit_btn.configure(state="disabled")

    def start_ui_update_thread(self):
        print("Start thread to handle UI updates from other threads")
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

    def start_camera_update_thread(self):
        print("Start separate thread for periodic camera updates")
    def camera_updater():
        pass
            # while True:
            #     try:-
            #         current_time = time.time()
            #         if current_time - self.last_camera_update >= self.camera_update_interval:
            #             self.ui_update_queue.put(lambda: self.load_cameras())
            #             self.last_camera_update = current_time
            #         time.sleep(1)
            #     except Exception as e:
            #         print(f"Camera update error: {e}")
            #         time.sleep(5)

        # camera_thread = threading.Thread(target=camera_updater, daemon=True)
        # camera_thread.start()

    def run(self):
        print("Run the application")
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Application error: {e}")

if __name__ == "__main__":
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    app = CameraManagementInterface(root)
    app.grid(row=0, column=0, sticky="nsew")
    app.run()