from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkScrollableFrame, CTkImage
from tkinter import StringVar
from PIL import Image


class ShowCameraInterface(CTkFrame):
    def __init__(self, *args, root_width: int = 1920, root_height: int = 1080, **kwargs):
        super().__init__(*args, **kwargs)

        self.configure(fg_color="#F1F5FA", corner_radius=0)
        self.current_frame = None
        self.loading = False
        self.camera_has_real_text = False
        self.bool_camera_dropdown_opened = False

        # Calculate dimensions
        self.i_form_width = int(root_width * 0.95)
        self.i_form_height = int(root_height * 0.95)

        # Initialize cameras list
        self.cameras = []

        # Create layout
        self.create_layout()

    def create_layout(self):
        # Left panel
        self.left_panel = CTkFrame(
            self,
            width=300,
            height=self.i_form_height,
            fg_color="#232E51",
            corner_radius=20
        )
        self.left_panel.pack(side="left", fill="y", padx=(20, 10), pady=20)
        self.left_panel.pack_propagate(False)

        # Header
        header_frame = CTkFrame(self.left_panel, fg_color="transparent")
        header_frame.pack(pady=(20, 30), padx=20, fill="x")

        CTkLabel(
            header_frame,
            text="Camera Settings",
            font=("Helvetica", 24, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        CTkLabel(
            header_frame,
            text="Select camera to view configuration",
            font=("Helvetica", 12),
            text_color="#8E9CB2"
        ).pack(anchor="w")

        # Custom Dropdown Frame
        self.frame_camera_dropdown = CTkFrame(
            self.left_panel,
            height=40,
            fg_color="#F6F6F6",
            corner_radius=5,
        )
        self.frame_camera_dropdown.pack(padx=20, pady=(0, 20), fill="x")
        self.frame_camera_dropdown.pack_propagate(False)

        # Entry for selected camera
        self.entry_selected_camera = CTkEntry(
            self.frame_camera_dropdown,
            height=40,
            fg_color="#F6F6F6",
            textvariable=StringVar(value="Select Camera"),
            text_color="#828282",
            border_color="#DEDEDE",
            border_width=2,
            corner_radius=5,
            font=("", 14),
        )
        self.entry_selected_camera.pack(side="left", fill="x", expand=True)
        self.entry_selected_camera.bind('<FocusIn>',
                                        lambda e: self.on_entry_focus_in(self.entry_selected_camera, "Select Camera"))
        self.entry_selected_camera.bind('<FocusOut>',
                                        lambda e: self.on_entry_focus_out(self.entry_selected_camera, "Select Camera"))

        # Bind click event to entry to show dropdown
        self.entry_selected_camera.bind('<Button-1>', lambda e: self.toggle_camera_dropdown())

        # Dropdown arrow button
        img_down_arrow = CTkImage(Image.open("resource/video/down_arrow_icon.png"), size=(22, 22))
        self.button_select_camera = CTkButton(
            self.frame_camera_dropdown,
            image=img_down_arrow,
            height=35,
            width=35,
            text="",
            fg_color="transparent",
            cursor="hand2",
            border_width=0,
            hover=False,
            command=self.toggle_camera_dropdown
        )
        self.button_select_camera.pack(side="right", padx=3, pady=1.5)

        # Dropdown window frame
        self.frame_dropdown_window = CTkFrame(
            self.left_panel,
            fg_color="#DEDEDE",
            height=200,  # Adjustable height for dropdown
            corner_radius=5
        )
        self.frame_dropdown_window.columnconfigure(0, weight=1)
        self.frame_dropdown_window.rowconfigure(0, weight=1)
        self.frame_dropdown_window.grid_propagate(False)

        # Bind click outside to close dropdown
        self.bind('<Button-1>', self.check_click_outside)

        # Right panel and other UI elements
        self.setup_right_panel()

    def check_click_outside(self, event):
        """Check if click is outside the dropdown area"""
        if self.bool_camera_dropdown_opened:
            # Get the widget under the mouse
            widget = event.widget
            # Check if click is outside dropdown area
            while widget is not None:
                if widget == self.frame_dropdown_window or widget == self.frame_camera_dropdown:
                    return
                widget = widget.master
            # If we get here, click was outside
            self.close_dropdown()

    def toggle_camera_dropdown(self):
        """Toggle the camera dropdown visibility"""
        if not self.bool_camera_dropdown_opened:
            self.show_camera_dropdown()
            self.bool_camera_dropdown_opened = True
        else:
            self.close_dropdown()
            self.bool_camera_dropdown_opened = False

    def show_camera_dropdown(self):
        """Display the camera dropdown with scrollable options"""
        # Close any existing dropdown first
        for child in self.frame_dropdown_window.winfo_children():
            child.destroy()

        frame_dropdown_table = CTkScrollableFrame(
            self.frame_dropdown_window,
            fg_color="#FFFFFF",
            height=40,
            corner_radius=5
        )
        frame_dropdown_table.columnconfigure(0, weight=1)
        frame_dropdown_table.grid(row=0, column=0, padx=(1, 5), pady=(1, 3), sticky="nsew")

        # Get camera names from self.cameras
        Camera_Names = []
        for camera in self.cameras:
            if isinstance(camera, tuple) and len(camera) > 0:
                Camera_Names.append(camera[0])
            elif isinstance(camera, dict) and "Camera_Name" in camera:
                Camera_Names.append(camera["Camera_Name"])

        for index, Camera_Name in enumerate(sorted(Camera_Names)):
            button_options = CTkButton(
                frame_dropdown_table,
                text=f"    {Camera_Name}",
                height=20,
                fg_color="transparent",
                text_color="#414141",
                font=("", 14),
                corner_radius=0,
                hover_color="#F6F6F6",
                anchor="w",
                command=lambda name=Camera_Name: self.select_camera(name)
            )
            button_options.grid(row=index, column=0, sticky="nsew")

        # Position the dropdown below the entry field
        self.frame_dropdown_window.pack(padx=20, pady=(0, 20), fill="x")
        self.frame_dropdown_window.lift()

    def select_camera(self, Camera_Name):
        """Handle camera selection from dropdown"""
        self.entry_selected_camera.configure(state="normal", text_color="#414141")
        self.entry_selected_camera.delete(0, "end")
        self.entry_selected_camera.insert(0, Camera_Name)
        self.camera_has_real_text = True
        self.close_dropdown()

        # Trigger the camera details update
        self.on_camera_select(Camera_Name)

    def close_dropdown(self, *args):
        """Close the dropdown window"""
        if hasattr(self, 'frame_dropdown_window'):
            self.frame_dropdown_window.pack_forget()
            for child in self.frame_dropdown_window.winfo_children():
                child.destroy()
        self.bool_camera_dropdown_opened = False

    def on_entry_focus_in(self, entry, placeholder):
        """Handle entry focus in"""
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.configure(text_color="#000000")

    def on_entry_focus_out(self, entry, placeholder):
        """Handle entry focus out"""
        if not entry.get().strip() or not self.camera_has_real_text:
            entry.delete(0, "end")
            entry.insert(0, placeholder)
            entry.configure(text_color="#828282")
            self.camera_has_real_text = False
        else:
            entry.configure(text_color="#000000")

    # Rest of the methods remain the same...
    def setup_right_panel(self):
        # Right panel
        self.right_panel = CTkFrame(
            self,
            fg_color="#FFFFFF",
            corner_radius=20
        )
        self.right_panel.pack(side="left", expand=True, fill="both", padx=(10, 20), pady=20)

        # Details container and labels setup
        self.create_detail_labels()

    def create_detail_labels(self):
        self.detail_widgets = {}
        detail_items = [
            "Camera Name", "IP Address", "Port", "Username",
            "Password", "RTSP URL"
        ]

        for item in detail_items:
            frame = CTkFrame(self.right_panel, fg_color="transparent")
            frame.pack(fill="x", padx=30, pady=10, anchor="center")  # Center the frame in the panel

            CTkLabel(
                frame,
                text=f"{item}:",
                font=("Helvetica", 20, "bold"),
                text_color="#232E51",
                width=150,
                anchor="w"
            ).pack(side="left")

            value_label = CTkLabel(
                frame,
                text="",
                font=("Helvetica", 18),
                text_color="#000000",
                anchor="w"
            )
            value_label.pack(side="left", padx=(10, 0))

            self.detail_widgets[item] = {
                "frame": frame,
                "value_label": value_label
            }

    def update_camera_list(self, camera_data):
        """Update the camera list data"""
        self.cameras = camera_data
        if self.bool_camera_dropdown_opened:
            self.show_camera_dropdown()  # Refresh dropdown if it's open

    def on_camera_select(self, choice):
        """Handle camera selection and update details"""
        selected_camera = None
        for camera in self.cameras:
            if isinstance(camera, tuple) and camera[0] == choice:
                selected_camera = {
                    "Camera Name": camera[0],
                    "IP Address": camera[1],
                    "Port": camera[2],
                    "Username": camera[3],
                    "Password": camera[4],
                    "RTSP URL": camera[5] if len(camera) > 5 else "N/A"
                }
                break
            elif isinstance(camera, dict) and camera.get("Camera_Name") == choice:
                selected_camera = {
                    "Camera Name": camera.get("Camera_Name"),
                    "IP Address": camera.get("IP_Address"),
                    "Port": camera.get("Port"),
                    "Username": camera.get("Username"),
                    "Password": camera.get("Password"),
                    "RTSP URL": camera.get("URL", "N/A")
                }
                break

        if selected_camera:
            for label, value in selected_camera.items():
                if value is None:
                    value = "N/A"
                self.detail_widgets[label]["value_label"].configure(text=str(value))
                self.detail_widgets[label]["frame"].pack(fill="x", padx=30, pady=10)