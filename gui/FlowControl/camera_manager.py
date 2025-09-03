import re
from tkinter import messagebox

from gui.Core.main import Core
# from gui.FlowControl.camera_roi import CameraRoiController
from gui.FlowControl.home import HomeController
from gui.Interface.main import Interface
# from share_queue import update_all_camera_list


class CameraManagerController:
    def __init__(self, Core: Core, Interface: Interface):
        
        self.obj_Core = Core
        self.obj_Interface = Interface
        self.obj_HomeInterface = self.obj_Interface.dict_frames["home"]
        # self.obj_event= Event(self.obj_Core.dict_db_details,self.obj_Core.dict_user_data)
        self.camera_manager_interface = self.obj_Interface.dict_frames["camera_manager"]
   
       
        # self.bind_buttons()
# 

        # self.camera_manager_interface = self.obj_Interface.dict_frames["camera_manager"]
        # self.obj_CameraRoiController = CameraRoiController(Core, Interface)
        # self.obj_Home_Controller = HomeController(Core, Interface)
        # self.camera_manager_interface.button_edit.configure(command=self.on_click_edit)
        # self.camera_manager_interface.on_form_ready = self.bind_events
        # self.camera_manager_interface.button_delete.configure(command=self.delete_camera)
        # # self.update_camera_data_list()
        # update_all_camera_list(self.camera_manager_interface.dummy_camera_details)
        # self.camera_manager_interface.update_table(self.camera_manager_interface.dummy_camera_details)
        # self.old_camera_data_during_edit={'direction':'', 'url': ''}


        # self.component = {
        #     "username": "",
        #     "password": "",
        #     "ip": "",
        #     "port": '',
        #     "path": ""
        # }


    # def bind_events(self):
    #     # Bind key release events for validation
    #     self.camera_manager_interface.entry_Camera_Name.bind("<KeyRelease>", self.validate_Camera_Name)
    #     self.camera_manager_interface.entry_username.bind("<KeyRelease>", self.validate_user_name)
    #     self.camera_manager_interface.entry_password.bind("<KeyRelease>", self.validate_password)
    #     self.camera_manager_interface.entry_port.bind("<KeyRelease>", self.validate_port)
    #     self.camera_manager_interface.entry_IPAddress.bind("<KeyRelease>", self.validate_ip)
    #     self.camera_manager_interface.entry_rtsp_url.bind("<KeyRelease>", self.validate_url)
    #     self.camera_manager_interface.entry_substream.bind("<KeyRelease>", self.validate_substream)
    #     self.camera_manager_interface.btn_cancel.configure(command=self.onclick_cancel)
    #     self.camera_manager_interface.btn_save.configure(command=self.onclick_save)
    #     self.camera_manager_interface.popup.bind("<Map>", lambda event: self.on_window_restored())

    #     if self.camera_manager_interface.btn_save.cget('text') == 'Save':
    #         print("Cache cleared for camera form .")
    #         self.component = {
    #             "username": "",
    #             "password": "",
    #             "ip": "",
    #             "port": '',
    #             "path": ""
    #         }
    #     else:
    #         self.old_camera_data_during_edit = {'direction': self.camera_manager_interface.entry_selected_direction.get(), 'url': self.camera_manager_interface.entry_rtsp_url.get()}


        # Bind both save and cancel buttons

    def on_click_edit(self):
        pass
        # if len(self.camera_manager_interface.selected_cameras) == 1:
        #     Camera_Name = next(iter(self.camera_manager_interface.selected_cameras))
        #     camera = next((cam for cam in self.camera_manager_interface.dummy_camera_details if cam['name'] == Camera_Name), None)
        #     if camera:
        #         self.camera_manager_interface.edit_camera(camera)
        #         self.handle_edit_form(camera['url'])
        #         ans=self.split_rtsp_url(camera['url'])
        #         self.component = {
        #             "username": ans['username'],
        #             "password": ans['password'],
        #             "ip": ans['ip'],
        #             "port": ans['port'],
        #             "path": ans['path']
        #         }

    def on_window_restored(self):
        pass
     
        # try:
        #     self.obj_HomeInterface = self.obj_Interface.dict_frames["home"]

        #     if 'camera_manager' in self.obj_Interface.dict_frames and hasattr(
        #             self.obj_Interface.dict_frames['camera_manager'], 'popup'):
        #         self.obj_Interface.obj_RootInterface.deiconify()
        # except Exception as e:
        #     print(e)

    def handle_edit_form(self,rtsp):
        pass
        # print("rtsp value is ",rtsp)
        # rtsp_pattern = re.compile(
        #     r"^rtsp://(?:[a-zA-Z0-9_.+@-]+(?::[a-zA-Z0-9_.+@-]+)?@)?(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?(?:/[a-zA-Z0-9_.@/-]+)?$"
        # )


        # if rtsp_pattern.match(rtsp):
        #     ans = self.split_rtsp_url(rtsp)
        #     self.camera_manager_interface.entry_username.delete(0, 'end')
        #     self.camera_manager_interface.entry_password.delete(0, 'end')
        #     self.camera_manager_interface.entry_port.delete(0, 'end')
        #     self.camera_manager_interface.entry_IPAddress.delete(0, 'end')
        #     self.camera_manager_interface.entry_substream.delete(0, 'end')


        #     self.camera_manager_interface.entry_username.insert(0, ans['username'])
        #     self.camera_manager_interface.entry_password.insert(0, ans['password'])


        #     port = ans.get('port', '')
        #     if not port:
        #         port = '554'
        #     self.camera_manager_interface.entry_port.insert(0, port)

        #     self.camera_manager_interface.entry_IPAddress.insert(0, ans['ip'])
        #     self.camera_manager_interface.entry_substream.insert(0, ans['path'])


    def onclick_cancel(self):
        pass
        # """Clears all input fields in the form and sets placeholders."""
        # button_text = self.camera_manager_interface.btn_cancel.cget("text")

        # if button_text=='cancel':


        #     self.camera_manager_interface.entry_rtsp_url.configure(border_color="#DEDEDE")

        #     self.camera_manager_interface.entry_Camera_Name.delete(0, 'end')
        #     self.camera_manager_interface.entry_Camera_Name.configure(placeholder_text="Enter camera name",
        #                                                               border_color="#DEDEDE")

        #     self.camera_manager_interface.entry_selected_direction.configure(state="normal", text_color="#828282")
        #     self.camera_manager_interface.entry_selected_direction.delete(0, 'end')
        #     self.camera_manager_interface.entry_selected_direction.insert(0, "Select direction")
        #     self.camera_manager_interface.entry_selected_direction.configure(state="disabled", border_color="#DEDEDE")

        #     self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
        #     self.camera_manager_interface.entry_rtsp_url.configure(placeholder_text="rtsp://", border_color="#DEDEDE")

        #     self.camera_manager_interface.entry_username.delete(0, 'end')
        #     self.camera_manager_interface.entry_username.configure(placeholder_text="Enter username",
        #                                                            border_color="#DEDEDE")

        #     self.camera_manager_interface.entry_IPAddress.delete(0, 'end')
        #     self.camera_manager_interface.entry_IPAddress.configure(placeholder_text="192.168.1.1", border_color="#DEDEDE")

        #     self.camera_manager_interface.entry_password.delete(0, 'end')
        #     self.camera_manager_interface.entry_password.configure(placeholder_text="Enter Password",
        #                                                            border_color="#DEDEDE")

        #     self.camera_manager_interface.entry_port.delete(0, 'end')
        #     self.camera_manager_interface.entry_port.configure(placeholder_text="", border_color="#DEDEDE")

        #     self.camera_manager_interface.entry_substream.delete(0, 'end')
        #     self.camera_manager_interface.entry_substream.configure(placeholder_text="Enter substream",
        #                                                             border_color="#DEDEDE")

        #     self.camera_manager_interface.label_camera_error.configure(text="")
        #     self.camera_manager_interface.label_connection_error.configure(text="")

        #     self.camera_manager_interface.frame_form.focus_set()

        #     self.component = {
        #         "username": "",
        #         "password": "",
        #         "ip": "",
        #         "port": '',
        #         "path": ""
        #     }
        # else:
        #     Camera_Name = next(iter(self.camera_manager_interface.selected_cameras))
        #     camera = next((cam for cam in self.camera_manager_interface.dummy_camera_details if cam['name'] == Camera_Name), None)
        #     if camera:
        #         print("edit camera details : ", camera)
        #         self.camera_manager_interface.entry_rtsp_url.configure(border_color="#DEDEDE")

        #         self.camera_manager_interface.entry_Camera_Name.delete(0, 'end')
        #         self.camera_manager_interface.entry_Camera_Name.insert(0, camera[
        #             'name'])

        #         self.camera_manager_interface.entry_selected_direction.configure(state="normal", text_color="#828282")
        #         self.camera_manager_interface.entry_selected_direction.delete(0, 'end')
        #         self.camera_manager_interface.entry_selected_direction.insert(0, camera['direction'])
        #         self.camera_manager_interface.entry_selected_direction.configure(state="disabled",
        #                                                                          border_color="#DEDEDE")

        #         self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
        #         self.camera_manager_interface.entry_rtsp_url.insert(0, camera['url'])  # Use insert instead of configure

        #         self.camera_manager_interface.entry_username.delete(0, 'end')
        #         self.camera_manager_interface.entry_username.configure(placeholder_text="Enter username",
        #                                                                border_color="#DEDEDE")

        #         self.camera_manager_interface.entry_IPAddress.delete(0, 'end')
        #         self.camera_manager_interface.entry_IPAddress.configure(placeholder_text="192.168.1.1",
        #                                                                 border_color="#DEDEDE")

        #         self.camera_manager_interface.entry_password.delete(0, 'end')
        #         self.camera_manager_interface.entry_password.configure(placeholder_text="Enter Password",
        #                                                                border_color="#DEDEDE")

        #         self.camera_manager_interface.entry_port.delete(0, 'end')
        #         self.camera_manager_interface.entry_port.configure(placeholder_text="", border_color="#DEDEDE")

        #         self.camera_manager_interface.entry_substream.delete(0, 'end')
        #         self.camera_manager_interface.entry_substream.configure(placeholder_text="Enter substream",
        #                                                                 border_color="#DEDEDE")

        #         self.camera_manager_interface.label_camera_error.configure(text="")
        #         self.camera_manager_interface.label_connection_error.configure(text="")

        #         self.handle_edit_form(camera['url'])

        #         self.camera_manager_interface.frame_form.focus_set()

        # return

    def onclick_save(self) -> None:
        pass
        # """Handle save button click by collecting, validating, and saving camera settings."""
        # eligible_to_save = True
        # Camera_Name = self.camera_manager_interface.entry_Camera_Name.get().strip()
        # direction = self.camera_manager_interface.entry_selected_direction.get().strip()
        # rtsp_url = self.camera_manager_interface.entry_rtsp_url.get().strip()
        # username = self.camera_manager_interface.entry_username.get().strip()
        # ip_address = self.camera_manager_interface.entry_IPAddress.get().strip()
        # password = self.camera_manager_interface.entry_password.get().strip()
        # port = self.camera_manager_interface.entry_port.get().strip()
        # substream = self.camera_manager_interface.entry_substream.get().strip()

        # errors = []
        # if not direction or direction == "Select direction":
        #     self.camera_manager_interface.entry_selected_direction.configure(border_color="red")
        #     self.camera_manager_interface.label_camera_error.configure(text="Camera direction is required.")
        #     eligible_to_save = False

        # if not Camera_Name:
        #     self.camera_manager_interface.entry_Camera_Name.configure(border_color="red")
        #     self.camera_manager_interface.label_camera_error.configure(text="Camera name is required.")
        #     eligible_to_save = False

        # if rtsp_url:
        #     if self.validate_url(rtsp_url) == False:
        #         self.camera_manager_interface.entry_rtsp_url.configure(border_color="red")
        #         self.camera_manager_interface.label_connection_error.configure(text="Invalid RTSP URL format.")
        #         eligible_to_save = False


        # elif not rtsp_url:

        #     if not substream:
        #         self.camera_manager_interface.entry_substream.configure(border_color="red")
        #         self.camera_manager_interface.label_connection_error.configure(text="The substream field is blank.")
        #         eligible_to_save = False

        #     if not port:
        #         self.camera_manager_interface.entry_port.configure(border_color="red")
        #         self.camera_manager_interface.label_connection_error.configure(text="Port is required.")
        #         eligible_to_save = False

        #     elif not port.isdigit() or not (0 <= int(port) <= 65535):
        #         self.camera_manager_interface.entry_port.configure(border_color="red")
        #         self.camera_manager_interface.label_connection_error.configure(text="Invalid port number.")
        #         eligible_to_save = False

        #     if not ip_address:
        #         self.camera_manager_interface.entry_IPAddress.configure(border_color="red")
        #         self.camera_manager_interface.label_connection_error.configure(text="IP address is required.")
        #         eligible_to_save = False

        #     elif not self.validate_ip(ip_address):
        #         self.camera_manager_interface.entry_IPAddress.configure(border_color="red")
        #         self.camera_manager_interface.label_connection_error.configure(text="Invalid IP address.")
        #         eligible_to_save = False

        #     if not password:
        #         self.camera_manager_interface.entry_password.configure(border_color="red")
        #         self.camera_manager_interface.label_connection_error.configure(text="Password is required.")
        #         eligible_to_save = False
        #     if not username:
        #         self.camera_manager_interface.entry_username.configure(border_color="red")
        #         self.camera_manager_interface.label_connection_error.configure(text="Username is required.")
        #         eligible_to_save = False

        #     if not username and not password and not ip_address and not port and not substream:
        #         self.camera_manager_interface.entry_rtsp_url.configure(border_color="red")
        #         self.camera_manager_interface.label_connection_error.configure(text="RTSP is required.")
        #         eligible_to_save = False

        # camera_settings = {
        #     "Camera_Name": Camera_Name,
        #     "Camera_direction": direction,
        #     "URL": rtsp_url
        # }
        # if eligible_to_save:

        #     if self.camera_manager_interface.btn_save.cget('text') == 'Save':
        #         check_sucess = self.obj_Core.obj_Camera.add_camera(camera_settings)
        #     else:
        #         camera_data = {
        #             "Camera_Name": list(self.camera_manager_interface.selected_cameras)[0],
        #             "URL": self.camera_manager_interface.entry_rtsp_url.get(),
        #             "Camera_direction": self.camera_manager_interface.entry_selected_direction.get(),
        #         }
        #         check_sucess = self.obj_Core.obj_Camera.update_camera(camera_data)
        #     if check_sucess:
        #         if self.camera_manager_interface.btn_save.cget('text') == "Save":
        #             self.obj_Interface.on_error(
        #                 "home",
        #                 "Data Added Successfully",
        #                 "New Camera is now available in camera manager.",
        #                 "#63CA6D"
        #             )
        #             self.onclick_cancel()

        #             # self.camera_manager_interface.selected_cameras.clear()
        #             self.camera_manager_interface.reset_interface()
        #             # self.update_camera_data_list()
        #             # update_all_camera_list(self.camera_manager_interface.dummy_camera_details)
        #             self.camera_manager_interface.update_table(self.camera_manager_interface.dummy_camera_details)

        #         else:
        #             if self.old_camera_data_during_edit.get('direction',
        #                                                     'N/A') == self.camera_manager_interface.entry_selected_direction.get() and self.old_camera_data_during_edit.get(
        #                 'url', 'N/A') == self.camera_manager_interface.entry_rtsp_url.get():
        #                 self.obj_Interface.on_error(
        #                     "home",
        #                     "Update Failed",
        #                     "All inputs is same as previous data.",
        #                     "#FF4B4B"
        #                 )
        #             else:
        #                 self.obj_Interface.on_error(
        #                     "home",
        #                     "Data Updated Successfully",
        #                     "Your new details are reflected now .",
        #                     "#63CA6D"
        #                 )
        #                 self.onclick_cancel()
        #                 # self.camera_manager_interface.selected_cameras.clear()
        #                 self.camera_manager_interface.reset_interface()
        #                 # self.update_camera_data_list()
        #                 # update_all_camera_list(self.camera_manager_interface.dummy_camera_details)
        #                 self.camera_manager_interface.update_table(self.camera_manager_interface.dummy_camera_details)

        #         self.obj_Home_Controller.set_Camera_Name()



        #     else:
        #         self.obj_Interface.on_error(
        #             "home",
        #             "Error! Invalid Data",
        #             "Check if the entered data fulfill the required conditions.",
        #             "#FF4B4B"
        #         )


        # else:
        #     self.obj_Interface.on_error(
        #         "home",
        #         "Error! All Field not filled !",
        #         "Fill the form completely for further process.",
        #         "#FF4B4B"
        #     )



    def validate_ipAddress(self, ip: str) -> bool:
        pass
        # """Validate an IP address (both IPv4 and IPv6)."""
        # self.camera_manager_interface.label_connection_error.configure(text="")
        # ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        # ipv6_pattern = r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"

        # if re.match(ipv4_pattern, ip):
        #     parts = ip.split(".")
        #     return all(0 <= int(part) <= 255 for part in parts)
        # elif re.match(ipv6_pattern, ip):
        #     return True

        # return False

    def validate_substream(self, event=None):
        pass
        # self.camera_manager_interface.label_connection_error.configure(text="")
        # substream = self.camera_manager_interface.entry_substream.get()
        # if substream:
        #     self.camera_manager_interface.entry_substream.configure(border_color="green")
        #     self.component["path"] = self.camera_manager_interface.entry_substream.get()
        #     rtsp = self.merge_rtsp_url(self.component)
        #     self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
        #     self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
        #     self.validate_url()
        # elif len(substream) == 0:
        #     self.component['path'] = ""
        #     self.camera_manager_interface.entry_substream.configure(border_color="#DEDEDE")
        #     rtsp = self.merge_rtsp_url(self.component)
        #     self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
        #     self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
        #     self.validate_url()


        # else:
        #     self.camera_manager_interface.entry_substream.configure(border_color="red")

    def show_error_message(self, message: str) -> None:
        pass
        # """Display an error message."""
        # from tkinter import messagebox
        # messagebox.showerror("Validation Error", message)

    def show_warning_message(self, message: str) -> bool:
        pass
        # """Display a warning message and return user's response (True for 'OK', False for 'Cancel')."""
        # from tkinter import messagebox
        # return messagebox.askokcancel("Warning", message)

    # def validate_Camera_Name(self, event=None):
    #     self.camera_manager_interface.label_camera_error.configure(text="")
    #     if len(self.camera_manager_interface.entry_Camera_Name.get()) > 0:
    #         self.camera_manager_interface.entry_Camera_Name.configure(border_color="green")
    #     else:
    #         self.camera_manager_interface.entry_Camera_Name.configure(border_color="red")



    # def validate_user_name(self, event=None):
    #     self.camera_manager_interface.label_connection_error.configure(text="")
    #     if len(self.camera_manager_interface.entry_username.get()) > 0:
    #         self.camera_manager_interface.entry_username.configure(border_color="green")
    #         self.component["username"] = self.camera_manager_interface.entry_username.get()
    #         rtsp = self.merge_rtsp_url(self.component)
    #         self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
    #         self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
    #         self.validate_url()
    #     elif len(self.camera_manager_interface.entry_username.get()) == 0:
    #         self.component['username'] = ""
    #         self.camera_manager_interface.entry_username.configure(border_color="#DEDEDE")
    #         rtsp = self.merge_rtsp_url(self.component)
    #         self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
    #         self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
    #         self.validate_url()
    #     else:
    #         self.camera_manager_interface.entry_username.configure(border_color="red")


    # def validate_password(self, event=None):
    #     self.camera_manager_interface.label_connection_error.configure(text="")
    #     if len(self.camera_manager_interface.entry_password.get()) > 0:
    #         self.camera_manager_interface.entry_password.configure(border_color="green")
    #         self.component["password"] = self.camera_manager_interface.entry_password.get()
    #         rtsp = self.merge_rtsp_url(self.component)
    #         self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
    #         self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
    #         self.validate_url()
    #     elif len(self.camera_manager_interface.entry_password.get()) == 0:
    #         self.component['password'] = ""
    #         self.camera_manager_interface.entry_password.configure(border_color="#DEDEDE")
    #         rtsp = self.merge_rtsp_url(self.component)
    #         self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
    #         self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
    #         self.validate_url()
    #     else:
    #         self.camera_manager_interface.entry_password.configure(border_color="red")



    # def validate_ip(self, event=None):
    #     self.camera_manager_interface.label_connection_error.configure(text="")
    #     result = self.validate_ipAddress(self.camera_manager_interface.entry_IPAddress.get())
    #     if result:
    #         self.camera_manager_interface.entry_IPAddress.configure(border_color="green")
    #         self.component["ip"] = self.camera_manager_interface.entry_IPAddress.get()
    #         rtsp = self.merge_rtsp_url(self.component)
    #         self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
    #         self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
    #     elif len(self.camera_manager_interface.entry_IPAddress.get()) == 0:
    #         self.component['ip'] = ""
    #         self.camera_manager_interface.entry_IPAddress.configure(border_color="#DEDEDE")
    #         rtsp = self.merge_rtsp_url(self.component)
    #         self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
    #         self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
    #         self.validate_url()
    #     else:
    #         self.camera_manager_interface.entry_IPAddress.configure(border_color="red")



    # def validate_url(self, event=None):
    #     self.camera_manager_interface.label_connection_error.configure(text="")
    #     result = self.camera_manager_interface.entry_rtsp_url.get()
    #     rtsp_pattern = re.compile(
    #         r"^rtsp://(?:[a-zA-Z0-9_.+@-]+(?::[a-zA-Z0-9_.+@-]+)?@)?(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?(?:/[a-zA-Z0-9_.@/-]+)?$"
    #     )

    #     if rtsp_pattern.match(result):
    #         ans = self.split_rtsp_url(result)

    #         self.camera_manager_interface.entry_username.delete(0, 'end')
    #         self.camera_manager_interface.entry_password.delete(0, 'end')
    #         self.camera_manager_interface.entry_port.delete(0, 'end')
    #         self.camera_manager_interface.entry_IPAddress.delete(0, 'end')
    #         self.camera_manager_interface.entry_substream.delete(0, 'end')

    #         self.camera_manager_interface.entry_username.insert(0, ans['username'])
    #         self.camera_manager_interface.entry_password.insert(0, ans['password'])

    #         port = ans.get('port', '')
    #         if not port:
    #             port = '554'
    #         self.camera_manager_interface.entry_port.insert(0, port)

    #         self.camera_manager_interface.entry_IPAddress.insert(0, ans['ip'])
    #         self.camera_manager_interface.entry_substream.insert(0, ans['path'])

    #         self.camera_manager_interface.entry_rtsp_url.configure(border_color="green")
    #         return True

    #     elif len(result) == 0:
    #         self.camera_manager_interface.entry_rtsp_url.configure(border_color="#DEDEDE")
    #         return False

    #     else:
    #         self.camera_manager_interface.entry_rtsp_url.configure(border_color="red")
    #         return False



    # def validate_port(self, event=None):
    #     self.camera_manager_interface.label_connection_error.configure(text="")
    #     port = self.camera_manager_interface.entry_port.get()
    #     if port.isdigit() and 0 < int(port)< 65500:
    #         self.camera_manager_interface.entry_port.configure(border_color="green")
    #         self.component["port"] = port
    #         rtsp = self.merge_rtsp_url(self.component)
    #         self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
    #         self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
    #         self.validate_url()
    #     elif len(self.camera_manager_interface.entry_port.get()) == 0:
    #         self.component['port'] = ''
    #         self.camera_manager_interface.entry_port.configure(border_color="#DEDEDE")
    #         rtsp = self.merge_rtsp_url(self.component)
    #         self.camera_manager_interface.entry_rtsp_url.delete(0, 'end')
    #         self.camera_manager_interface.entry_rtsp_url.insert(0, rtsp)
    #         self.validate_url()

    #     else:
    #         self.camera_manager_interface.entry_port.configure(border_color="red")



    # def split_rtsp_url(self, rtsp_url):

    #     rtsp_pattern = re.compile(
    #         r"^rtsp://(?:(?P<username>[a-zA-Z0-9_.+@-]+)(?::(?P<password>[a-zA-Z0-9_.+@-]+))?@)?(?P<ip>(?:\d{1,3}\.){3}\d{1,3})(?::(?P<port>\d{1,5}))?(/(?P<path>[a-zA-Z0-9_.@/-]+))?$"
    #     )


    #     match = rtsp_pattern.match(rtsp_url)

    #     if match:

    #         components = match.groupdict()


    #         username = components.get('username')
    #         password = components.get('password')
    #         ip = components.get('ip')
    #         port = components.get('port')
    #         path = components.get('path')


    #         return {
    #             "username": username if username else "",
    #             "password": password if password else "",
    #             "ip": ip,
    #             "port": int(port) if port else '',
    #             "path": path if path else ""
    #         }
    #     else:
    #         return {
    #             "username": "",
    #             "password": "",
    #             "ip": "",
    #             "port": '',
    #             "path": ""
    #         }

    # def merge_rtsp_url(self, components):
    #     username = components.get('username', '')
    #     password = components.get('password', '')
    #     ip = components.get('ip', '')
    #     port = components.get('port', 0)
    #     path = components.get('path', '')

    #     rtsp_url = "rtsp://"


    #     if username != "":
    #         rtsp_url += username
    #         if password != "":
    #             rtsp_url += f":{password}"
    #         rtsp_url += "@"

    #     if ip != "":
    #         rtsp_url += ip
    #         if port != 0:
    #             rtsp_url += f":{port}"

    #     # Add the path if available
    #     if path != "":
    #         rtsp_url += f"/{path}"

    #     return rtsp_url

    # def delete_camera(self):
    #     num = len(self.camera_manager_interface.selected_cameras)
    #     self.component = {
    #         "username": "",
    #         "password": "",
    #         "ip": "",
    #         "port": '',
    #         "path": ""
    #     }
    #     confirmation = messagebox.askyesno(
    #         "Confirm Deletion",
    #         f" You have seleccted {num} camera , Are you sure you want to delete the selected cameras?",
    #         icon='warning'
    #     )
    #     if confirmation:  # If user clicks "Yes"

    #         if self.obj_Core.obj_Camera.delete_cameras(list(self.camera_manager_interface.selected_cameras)):
    #             self.obj_Interface.on_error(
    #                 "home",
    #                 "Data Deleted Successfully",
    #                 "Camera no longer available in camera list.",
    #                 "#63CA6D"

    #             )

    #         else:
    #             self.obj_Interface.on_error(
    #                 "home",
    #                 "Error! Deletion failed",
    #                 "Either camera is not available or Some internal error occurred.",
    #                 "#FF4B4B"
    #             )
    #         self.update_camera_data_list()
    #         # update_all_camera_list(self.camera_manager_interface.dummy_camera_details)
    #         self.camera_manager_interface.selected_cameras.clear()
    #         self.camera_manager_interface.update_table(self.camera_manager_interface.dummy_camera_details)

    # def update_camera_data_list(self):
    #     datas = self.obj_Core.obj_Camera.fetch_all_Camera_data()
    #     self.camera_manager_interface.dummy_camera_details.clear()
    #     slno = 0
    #     for data in datas:
    #         slno = slno + 1
    #         new_camera_details = {
    #             'sl_no': slno,
    #             'name': data['Camera_name'],
    #             'url': data['URL'],
    #             'direction': data['Camera_direction']
    #         }
    #         # Append the new data to the list
    #         self.camera_manager_interface.dummy_camera_details.append(new_camera_details)