import threading
import time
from tkinter import StringVar
from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkImage, CTkCanvas, CTkScrollableFrame
from PIL import Image
import cv2
from gui.Core.main import Core
# from src.utility.shared_queue import all_camera_data, current_camera_details, update_camera_details

class HomeInInterface(CTkFrame):

    def __init__(self, *args, root_width: int = 1920, root_height: int = 1080, **kwargs):
        super().__init__(*args, **kwargs)

        self.configure(fg_color="#F1F5FA")
        self.obj_Core = Core()
        self.root_height = root_height
        self.root_width = root_width

        i_lcol_width = int(root_width * 0.15)  # "lcol" is "left column"
        i_rcol_width = int(root_width * 0.75)  # "rcol" is "right column"
        i_trow_height = int(root_height * 0.07)  # "trow" is "top row"
        i_mrow_height = int(root_height * 0.88)  # "mrow" is "middle row"
        i_brow_height = int(root_height * 0.05)  # "brow" is "bottom row"
        x = int(i_lcol_width * 0.07952286282306163)

        self.button_old_selected = None
        self.bool_user_popup = False
        self.bool_toggle_menu_bar = True
        self.bool_dropdown_opened = False
        self.bool_settings_popup = False
        self.settings_submenu_buttons = []
        self.connecting_animation_active = False
        self.connection_Status = None

        self.frame_lcol = CTkFrame(
            self,
            fg_color="#232E51",
            width=i_lcol_width,
            corner_radius=0
        )
        self.frame_lcol.pack(side="left", fill="both", expand=False)
        self.frame_lcol.pack_propagate(False)
 
        self.frame_rcol = CTkFrame(
            self,
            fg_color="#F1F5FA",
            width=i_rcol_width,
            corner_radius=0
        )
        self.frame_rcol.pack(side="right", fill="both", expand=True)

        self.frame_lcol_trow = CTkFrame(
            self.frame_lcol,
            fg_color="#232E51",
            height=i_trow_height,
            corner_radius=0
        )
        self.frame_lcol_trow.pack(side="top", fill="both", expand=False)

        self.frame_lcol_mrow = CTkFrame(
            self.frame_lcol,
            fg_color="#232E51",
            height=i_mrow_height,
            corner_radius=0
        )
        self.frame_lcol_mrow.pack(side="top", fill="both", expand=True)
        self.frame_lcol_brow = CTkFrame(
            self.frame_lcol,
            fg_color="#2F3A5F",
            height=i_brow_height,
            corner_radius=0
        )
        self.frame_lcol_brow.pack(side="top", fill="both", expand=False)

        self.frame_rcol_trow = CTkFrame(
            self.frame_rcol,
            fg_color="#FFFFFF",
            height=i_trow_height,
            corner_radius=0
        )
        self.frame_rcol_trow.columnconfigure((0, 1, 2), weight=1)
        self.frame_rcol_trow.rowconfigure(0, weight=1)
        self.frame_rcol_trow.pack(side="top", fill="x", expand=False)

        self.frame_rcol_mrow = CTkFrame(
            self.frame_rcol,
            fg_color="#F1F5FA",
            height=i_mrow_height,
            corner_radius=0
        )
        self.frame_rcol_mrow.columnconfigure(0, weight=1, uniform="a")
        self.frame_rcol_mrow.rowconfigure(0, weight=1)
        self.frame_rcol_mrow.pack(side="top", fill="both", expand=True)

        self.frame_rcol_brow = CTkFrame(
            self.frame_rcol,
            fg_color="#FFFFFF",
            height=i_brow_height,
            corner_radius=0
        )
        self.frame_rcol_brow.pack(side="top", fill="both", expand=False)

        img_alpr_logo = CTkImage(Image.open(r"resource/video/alpr_collapsed_logo.png"), size=(80, 60))
        self.label_alpr_logo = CTkLabel(self.frame_lcol_trow, image=img_alpr_logo, text="")
        self.label_alpr_logo.place(relx=0.5, rely=0.5, anchor="center")

        self.button_live_event = self.create_menu_buttons(self.frame_lcol_mrow,
                                                         "resource/video/live_event_icon.png", "Live Event",
                                                         i_img_width=20, i_img_height=20)
        self.button_historical_event = self.create_menu_buttons(self.frame_lcol_mrow,
                                                               "resource/video/historical_event_icon.png",
                                                               "Historical Event", i_img_width=19, i_img_height=19)
        self.button_add_vehicle = self.create_menu_buttons(self.frame_lcol_mrow,
                                                          "resource/video/add_vehicle_icon.png", "Add Vehicle",
                                                          i_padx=(6, 5))
        self.button_delete_vehicle = self.create_menu_buttons(self.frame_lcol_mrow,
                                                             "resource/video/delete_vehicle_icon.png",
                                                             "Delete Vehicle", i_padx=(6, 5))

        self.button_settings = self.create_menu_buttons(
            self.frame_lcol_mrow,
            "resource/video/setting_icon.png",
            "Settings",
            i_img_width=20,
            i_img_height=20,
            command=self.toggle_settings_popup
        )

        self.button_camera_settings = self.create_menu_buttons(
            self.frame_lcol_mrow,
            "resource/video/camera_manager_icon.png",
            "Camera Manager",
            i_img_width=20,
            i_img_height=20,
            i_padx=(25, 5),
            command=lambda: self.update_menu_buttons_state(self.button_camera_settings)
        )
        self.button_camera_settings.pack_forget()  # Hide initially

        self.btn_vehicle_manager = self.create_menu_buttons(
            self.frame_lcol_mrow,
            "resource/video/vehicle_list_icon.png",
            "Object Manager",
            i_img_width=17,
            i_img_height=17,
            i_padx=(25, 5),
            command=lambda: self.update_menu_buttons_state(self.btn_vehicle_manager)
        )
        self.btn_vehicle_manager.pack_forget()  # Hide initially

        self.button_audio_settings = self.create_menu_buttons(
            self.frame_lcol_mrow,
            "resource/video/audio_manager_icon.png",
            "Audio Manager",
            i_img_width=20,
            i_img_height=20,
            i_padx=(25, 5),
            command=lambda: self.update_menu_buttons_state(self.button_audio_settings)
        )
        self.button_audio_settings.pack_forget()  # Hide initially

        # Store references to all submenu buttons
        self.settings_submenu_buttons = [
            self.button_camera_settings,
            self.btn_vehicle_manager,
            self.button_audio_settings
        ]

        # Initialize state variables
        self.button_old_selected = None
        self.bool_user_popup = False
        self.bool_toggle_menu_bar = True
        self.bool_dropdown_opened = False
        self.bool_settings_popup = False

        img_logout_icon_1 = CTkImage(Image.open("resource/video/logout_button.png"), size=(17, 17))
        self.button_signout_1 = CTkButton(
            self.frame_lcol_brow,
            image=img_logout_icon_1,
            text="Logout",
            width=i_lcol_width,
            fg_color="transparent",
            text_color="#FFFFFF",
            hover=False,
            font=("", 14),
            cursor="hand2",
            anchor="center"
        )
        self.button_signout_1.place(relx=0.5, rely=0.5, anchor="center")

        # Left column for camera selection
        self.frame_rcol_trow_col0 = CTkFrame(
            self.frame_rcol_trow,
            height=i_trow_height,
            fg_color="#FFFFFF",
            corner_radius=0
        )
        self.frame_rcol_trow_col0.grid(row=0, column=0, sticky="nsew")

        # Center column for the header - ALWAYS CENTERED
        self.frame_rcol_trow_col1 = CTkFrame(
            self.frame_rcol_trow,
            height=i_trow_height,
            fg_color="#FFFFFF",
            corner_radius=0
        )
        self.frame_rcol_trow_col1.grid(row=0, column=1, sticky="nsew")

        # Right column for user controls
        self.frame_rcol_trow_col2 = CTkFrame(
            self.frame_rcol_trow,
            height=i_trow_height,
            fg_color="#FFFFFF"
        )
        self.frame_rcol_trow_col2.grid(row=0, column=2, sticky="nsew")

        # Place the header in the CENTER column
        self.label_alpr_heading = CTkLabel(
            self.frame_rcol_trow_col1,
            height=i_trow_height,
            text="PPE SYSTEM",
            text_color="#2C2C2C",
            font=("Segoe UI", 22, "bold")
        )
        self.label_alpr_heading.pack(expand=True, fill="both")
        self.label_alpr_heading.configure(anchor="center")

        self.frame_camera = CTkFrame(
            self.frame_rcol_trow_col0,
            height=30,
            fg_color="white",
            corner_radius=10
        )

        self.label_select_camera = CTkLabel(
            self.frame_rcol_trow_col0,
            text="Selected Camera :",
            text_color="Black",
            font=("", 16, 'bold'),
        )
        self.label_select_camera.pack(side="left", padx=(10, 0))
        self.label_select_camera.pack_forget()

        self.label_camera = CTkLabel(
            self.frame_rcol_trow_col0,
            text="",
            text_color="#FF0000",
            font=("", 12),
        )
        self.label_camera.pack(side="left", padx=(10, 0))
        self.list_camera = []
        self.selected_camera = ''
        self.frame_maindropdown_window = CTkFrame(
            self.frame_rcol_mrow,
            fg_color="#DEDEDE",
            height=140,
            corner_radius=5
        )
        self.frame_maindropdown_window.grid_propagate(False)
        self.frame_maindropdown_window.columnconfigure(0, weight=1)
        self.frame_maindropdown_window.rowconfigure(0, weight=1)

        self.entry_selected_camera = CTkEntry(
            self.frame_camera,
            height=x,
            width=200,
            fg_color="transparent",
            textvariable=StringVar(value=self.selected_camera),
            text_color="black",
            border_color="#DEDEDE",
            border_width=2,
            corner_radius=5,
            font=("", 14),
            state="disabled"
        )
        self.entry_selected_camera.grid(row=0, column=0, sticky="nsew")

        img_down_arraow = CTkImage(Image.open("resource/video/down_arrow_icon.png"), size=(22, 22))
        self.button_select_camera = CTkButton(
            self.frame_camera,
            image=img_down_arraow,
            height=35,
            width=35,
            text="",
            fg_color="transparent",
            cursor="hand2",
            border_width=0,
            hover=False,
            command=lambda: self.popup_dropdown(self.list_camera, entry_destination=self.entry_selected_camera,
                                               i_row=2)
        )
        self.button_select_camera.grid(row=0, column=0, sticky="e", padx=3, pady=1.5)

        img_user_icon = CTkImage(Image.open("resource/video/user_icon2.png"), size=(27, 27))
        self.button_user = CTkButton(
            self.frame_rcol_trow_col2,
            image=img_user_icon,
            width=22,
            text="",
            fg_color="#FFFFFF",
            hover=False,
            cursor="hand2",
        )
        self.button_user.pack(side="right", padx=(0, 10))

        self.notification_button_frmae = CTkLabel(self.frame_rcol_trow_col2, text="")
        self.notification_button_frmae.pack(side="right")

        img_notification_icon = CTkImage(Image.open("resource/video/bell.png"), size=(30, 30))
        self.button_notification = CTkButton(
            self.notification_button_frmae,
            image=img_notification_icon,
            width=30,
            height=30,
            text="",
            fg_color="transparent",
            hover=False,
            cursor="hand2"
        )
        self.button_notification.grid(row=0, column=0, sticky="nw")

        self.dot_label = CTkLabel(
            self.notification_button_frmae,
            height=6,
            width=10,
            text="",
            font=("Arial", 18, "bold"),
            text_color="green",
            fg_color=self.notification_button_frmae.cget("fg_color"),
        )
        self.dot_label.grid(row=0, column=0, sticky="ne", padx=4, pady=0)

        self.frame_user_popup = CTkFrame(
            self.frame_rcol_mrow,
            width=190,
            height=200,
            fg_color="#232E51"
        )
        self.frame_user_popup.columnconfigure(0, weight=1)
        self.frame_user_popup.grid_propagate(False)

        self.label_popup_msg = CTkLabel(
            self.frame_user_popup,
            height=5,
            text="Logged in as",
            text_color="#87C665",
            font=("", 12.5, "bold"),
            anchor="center"
        )
        self.label_popup_msg.grid(column=0, row=0, pady=(15, 8))

        self.label_user_name = CTkLabel(
            self.frame_user_popup,
            height=5,
            text="",
            text_color="#FFFFFF",
            font=("", 16),
            anchor="center"
        )
        self.label_user_name.grid(column=0, row=1, pady=(0, 15))

        self.canvas_underline = CTkCanvas(
            self.frame_user_popup,
            height=1,
            bg="#FFFFFF",
            bd=0,
            highlightthickness=0
        )
        self.canvas_underline.grid(row=2, column=0, sticky="ew")

        img_edit_icon = CTkImage(Image.open("resource/video/popup_edit_icon.png"), size=(24, 24))
        self.button_edit = CTkButton(
            self.frame_user_popup,
            image=img_edit_icon,
            text="Edit Profile",
            fg_color="transparent",
            text_color="#94A8BF",
            hover=False,
            font=("", 14,),
            cursor="hand2",
            anchor="w"
        )
        self.button_edit.grid(column=0, row=3, sticky="ew", pady=(18, 0), padx=4)

        img_new_user_icon = CTkImage(Image.open("resource/video/new_user_icon.png"), size=(24, 24))
        self.button_create_user = CTkButton(
            self.frame_user_popup,
            image=img_new_user_icon,
            text="New User",
            fg_color="transparent",
            text_color="#94A8BF",
            hover=False,
            font=("", 14,),
            cursor="hand2",
            anchor="w"
        )
        self.button_create_user.grid(column=0, row=4, sticky="ew", pady=(0, 0), padx=4)

        img_logout_icon_2 = CTkImage(Image.open("resource/video/popup_logout_icon.png"), size=(24, 24))
        self.button_signout_2 = CTkButton(
            self.frame_user_popup,
            image=img_logout_icon_2,
            text="Logout",
            fg_color="transparent",
            text_color="#94A8BF",
            hover=False,
            font=("", 14,),
            cursor="hand2",
            anchor="w"
        )
        self.button_signout_2.grid(column=0, row=5, sticky="nsew", pady=(0, 0), padx=4)

    def _bind_mouse_wheel(self, event):
        self.frame_popup_table.bind_all("<MouseWheel>", self._on_mouse_wheel)

    def _unbind_mouse_wheel(self, event):
        self.frame_popup_table.unbind_all("<MouseWheel>")

    def _on_mouse_wheel(self, event):
        try:
            self.frame_popup_table._parent_canvas.yview_scroll(-1 * (event.delta // 120), "units")
        except AttributeError as e:
            print(f"Error: {e}")

    def create_menu_buttons(self, parent: CTkFrame, str_img_path: str, str_text: str,
                           i_img_width: int = 17, i_img_height: int = 17,
                           i_padx: int = 5, i_pady: int = 5, command=None) -> CTkButton:
        img_icon = CTkImage(Image.open(str_img_path), size=(i_img_width, i_img_height))
        button_menu = CTkButton(
            parent,
            image=img_icon,
            text=str_text,
            fg_color="transparent",
            text_color="#94A8BF",
            hover=False,
            font=("", 14,),
            cursor="hand2",
            anchor="w",
            command=command
        )
        if str_text != "Add Vehicle" and str_text != "Delete Vehicle":
            button_menu.pack(side="top", fill="x", anchor="nw", pady=i_pady, padx=i_padx)
        return button_menu

    def toggle_settings_popup(self):
        # Update the menu button state
        self.update_menu_buttons_state(self.button_settings)

        # First, hide all buttons to ensure clean state
        self.button_camera_settings.pack_forget()
        self.btn_vehicle_manager.pack_forget()
        self.button_audio_settings.pack_forget()

        if not self.bool_settings_popup:  # Popup is closed, need to open it
            # Pack submenu buttons
            self.button_camera_settings.pack(side="top", fill="x", anchor="nw", pady=5, padx=(25, 5))
            self.btn_vehicle_manager.pack(side="top", fill="x", anchor="nw", pady=5, padx=(25, 5))
            self.button_audio_settings.pack(side="top", fill="x", anchor="nw", pady=5, padx=(25, 5))

        self.bool_settings_popup = not self.bool_settings_popup

    def popup_dropdown(self, list_data: list = [], entry_destination: CTkEntry = None, i_row: int = None):
        if self.bool_dropdown_opened is False:
            print(" camera length is ", len(list_data))
            parent = None
            if len(list_data) > 3:
                frame_popup_table = CTkScrollableFrame(
                    self.frame_maindropdown_window,
                    fg_color="#FFFFFF",
                    height=40,
                    corner_radius=5
                )
                frame_popup_table.columnconfigure(0, weight=1)
                frame_popup_table.grid(row=0, column=0, padx=(1, 5), pady=(1, 3), sticky="nsew")
                parent = frame_popup_table
            else:
                frame_popup_table = CTkFrame(
                    self.frame_maindropdown_window,
                    fg_color="#FFFFFF",
                    height=40,
                    corner_radius=5
                )
                frame_popup_table.columnconfigure(0, weight=1)
                frame_popup_table.grid(row=0, column=0, padx=(1, 5), pady=(1, 3), sticky="nsew")
                parent = frame_popup_table

            for index, row_data in enumerate(list_data):
                button_options = CTkButton(
                    parent,
                    text=f"    {row_data}",
                    height=40,
                    fg_color="transparent",
                    text_color="#414141",
                    font=("", 16),
                    corner_radius=0,
                    hover_color="#F6F6F6",
                    anchor="w",
                    command=lambda selected_option=row_data: self.select_option(selected_option, entry_destination)
                )
                button_options.grid(row=index, column=0, sticky="nsew")

            self.frame_maindropdown_window.place(relx=0.164, rely=0.076, anchor="center")
            self.frame_maindropdown_window.tkraise()
        else:
            self.frame_maindropdown_window.place_forget()

        self.bool_dropdown_opened = not self.bool_dropdown_opened

    def close_dropdown(self, event):
        self.frame_maindropdown_window.place_forget()
        self.bool_dropdown_opened = False

    def select_option(self, selected_option: str, entry_destination: CTkEntry):
        self.update_on_input_changed(entry_input_field=entry_destination, str_border_color="#DEDEDE")
        entry_destination.configure(state="normal", text_color="#414141")
        entry_destination.delete(0, "end")
        entry_destination.insert(0, "Connecting")
        entry_destination.configure(state="disabled", border_color="#FFA500")

        # current_camera_details = next((cam for cam in all_camera_data if cam["Camera_Name"] == selected_option), None)
        # print("Selected camera details:", current_camera_details)
        # self.button_select_camera.configure(state="disabled")
        # self.connection_Status = None

        # def animate_connecting(dot_count=1, start_Time=None):
        #     if not self.connecting_animation_active or self.connection_Status is not None:
        #         return

        #     if start_Time is None:
        #         start_Time = time.time()

        #     elapsed_Time = time.time() - start_Time
        #     max_duration = 10  # Maximum animation duration in seconds
        #     # if elapsed_Time > max_duration:
        #     #     self.connecting_animation_active = False
        #     #     entry_destination.after(0, lambda: update_to_failed("Connection Timed Out"))
        #     #     return

        #     if dot_count > 3:
        #         dot_count = 1
        #     entry_destination.configure(state="normal")
        #     entry_destination.delete(0, "end")
        #     entry_destination.insert(0, f"Connecting{'.' * dot_count}")
        #     entry_destination.configure(state="disabled")

        #     entry_destination.after(500, lambda: animate_connecting(dot_count + 1, start_Time))

        # self.connecting_animation_active = True
        # animate_connecting()

        def check_connection():
            start_Time = time.time()
            max_attempts = 1
            attempt = 0
            cap = None

            while attempt < max_attempts:
                # rtsp_url = current_camera_details.get("rtsp_url", "N/A")
                # cap = cv2.VideoCapture(rtsp_url)
                ret, frame = cap.read()
                if ret and frame is not None:
                    cap.release()
                    self.connection_Status = True
                    self.connecting_animation_active = False
                    elapsed_Time = time.time() - start_Time
                    entry_destination.after(int(elapsed_Time * 1000), update_to_connected)
                    break
                cap.release()
                attempt += 1
                time.sleep(1)

            if not self.connection_Status:
                self.connecting_animation_active = False
                entry_destination.after(0, update_to_failed)

        def update_to_connected():
            entry_destination.configure(state="normal", text_color="#008000", border_color="#008000")
            entry_destination.delete(0, "end")
            entry_destination.insert(0, "Connected")
            entry_destination.configure(state="disabled")
            self.button_select_camera.configure(state="normal")
            entry_destination.after(1000, lambda: update_to_Camera_Name())

        def update_to_failed(error_message="Connection Failed"):
            entry_destination.configure(state="normal", text_color="#FF0000", border_color="#FF0000")
            entry_destination.delete(0, "end")
            entry_destination.insert(0, error_message)
            entry_destination.configure(state="disabled")
            self.button_select_camera.configure(state="normal")

        def update_to_Camera_Name():
            entry_destination.configure(state="normal", text_color="#414141", border_color="#DEDEDE")
            entry_destination.delete(0, "end")
            entry_destination.insert(0, selected_option)
            entry_destination.configure(state="disabled")

        threading.Thread(target=check_connection, daemon=True).start()

        # update_camera_details(current_camera_details['Camera_Name'], current_camera_details['rtsp_url'],
        #                      current_camera_details['roi_start'], current_camera_details['roi_end'],
        #                      current_camera_details['roi_start_width'], current_camera_details['roi_end_width'],
        #                      current_camera_details['Status'])

        self.frame_maindropdown_window.place_forget()
        self.bool_dropdown_opened = False

    def update_on_input_changed(self, entry_input_field: CTkEntry = None, label_error: CTkLabel = None,
                               str_error: str = "", str_border_color: str = None):
        if entry_input_field is not None:
            if str_border_color is not None:
                entry_input_field.configure(border_color=str_border_color)
            if label_error is None:
                if entry_input_field == self.entry_selected_camera:
                    label_error = self.label_camera
                elif entry_input_field == self.entry_selected_type:
                    label_error = self.label_type_error

        if label_error is not None:
            label_error.configure(text=str_error)
        self.update()

    def toggle_menu_bar(self):
        if self.bool_toggle_menu_bar:
            if self.bool_settings_popup:
                self.toggle_settings_popup()

            i_lcol_width = int(self.root_width * 0.05)

            img_alpr_logo_collapsed = CTkImage(Image.open("resource/video/alpr_collapsed_logo.png"),
                                               size=(42, 33))
            self.label_alpr_logo.configure(image=img_alpr_logo_collapsed)

            self.button_live_event.configure(text="", anchor="center")
            self.button_historical_event.configure(text="", anchor="center")
            self.button_add_vehicle.configure(text="", anchor="center")
        #     self.button_delete_vehicle.configure(text="", anchor="center")
        #     self.button_settings.configure(text="", anchor="center")

        #     self.button_signout_1.configure(text="", width=i_lcol_width)

        #     self.frame_lcol.configure(width=i_lcol_width)
        # else:
        #     i_lcol_width = int(self.root_width * 0.15)

            img_alpr_logo = CTkImage(Image.open("resource/video/alpr_logo.png"), size=(105, 32))
            self.label_alpr_logo.configure(image=img_alpr_logo)

            self.button_live_event.configure(text="Live Event", anchor="w")
            self.button_historical_event.configure(text="Historical Event", anchor="w")
            # self.button_add_vehicle.configure(text="Add Vehicle", anchor="w")
            # self.button_delete_vehicle.configure(text="Delete Vehicle", anchor="w")
            # self.button_settings.configure(text="Settings", anchor="w")

            # self.button_signout_1.configure(text="Logout", width=i_lcol_width)

            # self.frame_lcol.configure(width=i_lcol_width)

        self.bool_toggle_menu_bar = not self.bool_toggle_menu_bar

    def update_profile_icon_menu_button_state(self, option):
       
        profile_menu_buttons = {self.button_create_user, self.button_edit}
        if option == 'new_user':
            self.button_create_user.configure(text_color='#FFFFFF')
            self.button_edit.configure(text_color='#94A8BF')
        elif option == 'edit_user':
            self.button_create_user.configure(text_color='#94A8BF')
            self.button_edit.configure(text_color='#FFFFFF')
        else:
            self.button_create_user.configure(text_color='#94A8BF')
            self.button_edit.configure(text_color='#94A8BF')

    def toggle_user_popup(self):
      
        if not self.bool_user_popup:
            self.frame_user_popup.configure(width=170)
            self.frame_user_popup.grid_propagate(False)
            self.frame_user_popup.grid(column=0, row=0, sticky="ne")
            self.frame_user_popup.tkraise()
        else:
            self.frame_user_popup.grid_forget()
        self.bool_user_popup = not self.bool_user_popup

    def update_menu_buttons_state(self, button_menu: CTkButton):
        print("update_menu_buttons_state")
        settings_submenu = {
            self.button_camera_settings,
            self.btn_vehicle_manager,
            self.button_audio_settings
        }

        main_menu_buttons = {
            self.button_live_event,
            self.button_historical_event,
            self.button_add_vehicle,
            self.button_delete_vehicle,
            self.button_notification,
            self.button_user
        }

        if button_menu in main_menu_buttons:
            self.reset_settings_state()

        if self.button_old_selected is not None:
            self.button_old_selected.configure(
                fg_color="transparent",
                text_color="#94A8BF"
            )

        button_menu.configure(
            fg_color="#2F3A5F",
            text_color="#FFFFFF"
        )

        if button_menu in settings_submenu:
            self.button_settings.configure(
                fg_color="#2F3A5F",
                text_color="#FFFFFF"
            )

        self.button_old_selected = button_menu

    def reset_menu_highlight(self):
        if self.button_old_selected:
            self.button_old_selected.configure(
                fg_color="transparent",
                text_color="#94A8BF"
            )
            self.button_old_selected = None

        self.reset_settings_state()

    def reset_settings_state(self):
        if self.bool_settings_popup:
            self.bool_settings_popup = False

        self.button_settings.configure(
            fg_color="transparent",
            text_color="#94A8BF"
        )

        # self.button_camera_settings.pack_forget()
        # self.btn_vehicle_manager.pack_forget()
        # self.button_audio_settings.pack_forget()

    def update_user_popup_data(self, str_username: str):
        self.label_user_name.configure(text=str_username)

    def starting_home_screen(self):
        CTkFrame(
            self.frame_rcol_mrow,
            fg_color="transparent",
        ).grid(row=0, column=0, sticky="nsew")

    def show_frame_camera(self):
        self.label_select_camera.pack(side="left", padx=(10, 0))
        self.frame_camera.pack(side="left", padx=(10, 0))

    def hide_frame_camera(self):
        self.label_select_camera.pack_forget()
        self.frame_camera.forget()