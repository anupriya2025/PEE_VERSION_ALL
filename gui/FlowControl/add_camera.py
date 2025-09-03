from gui.Core.main import Core
from gui.Interface.main import Interface


class AddCameraController:
    def __init__(self, Core: Core, Interface: Interface):
        self.obj_Core = Core
        self.obj_Interface = Interface
        self.settings_interface = self.obj_Interface.dict_frames["settings"]

        # Bind both save and cancel buttons
        self.settings_interface.button_save.configure(command=self.onclick_save)
        self.settings_interface.button_cancel.configure(command=self.onclick_cancel)

    def onclick_save(self) -> None:
        """Handle save button click by collecting and saving camera settings"""
        # Get values from all entry fields
        Camera_Name = self.settings_interface.Entry_Camera_Name.get()
        camera_ip = self.settings_interface.Entry_IP.get()
        port = self.settings_interface.Entry_port.get()
        username = self.settings_interface.Entry_username.get()
        password = self.settings_interface.Entry_password.get()

        # Create settings dictionary
        camera_settings = {
            "name": Camera_Name,
            "ip": camera_ip,
            "port": port,
            "username": username,
            "password": password
        }

        # Save settings using Core method
        self.obj_Core.save_camera_settings(camera_settings)

        # Clear all input fields after saving
        self.settings_interface.Entry_Camera_Name.delete(0, 'end')
        self.settings_interface.Entry_IP.delete(0, 'end')
        self.settings_interface.Entry_port.delete(0, 'end')
        self.settings_interface.Entry_username.delete(0, 'end')
        self.settings_interface.Entry_password.delete(0, 'end')

    def onclick_cancel(self) -> None:
        print("Cancel button clicked")  # Debug
        self.settings_interface.Entry_Camera_Name.delete(0, 'end')
        self.settings_interface.Entry_IP.delete(0, 'end')
        self.settings_interface.Entry_port.delete(0, 'end')
        self.settings_interface.Entry_username.delete(0, 'end')
        self.settings_interface.Entry_password.delete(0, 'end')
        print("Fields cleared")  # Debug
