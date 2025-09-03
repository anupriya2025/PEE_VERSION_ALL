from gui.Core.main import Core
from gui.Interface.main import Interface
from gui.Core.camera import Camera


class ShowCameraController:

    def __init__(self, Core: Core, Interface: Interface):

        self.obj_Core = Core
        self.obj_Interface = Interface
        self.obj_Camera=Camera(self.obj_Core.dict_db_details,self.obj_Core.dict_user_data)
        self.obj_Show_camera_interface = self.obj_Interface.dict_frames["show_camera"]

        self.camera_data_load()





    def camera_data_load(self):
        camera_data = self.obj_Camera.fetch_all_Camera_data()
        print("Fetched camera data:", camera_data)  # Debugging step
        self.obj_Show_camera_interface.update_camera_list(camera_data)

    # def validate_password(self, event) -> bool:

    #     str_password = self.obj_EditUserInterface.entry_password.get()
    #     str_error_msg = self.obj_Core.obj_Authentication.validate_password(str_password)

    #     if  len(str_error_msg) == 0:
    #         return True
    #     else:
    #         return False