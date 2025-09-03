# from .add_camera import AddCameraInterface
from .root import RootInterface
# from .settings import SettingsInterface
# from .show_camera import ShowCameraInterface
from .signin import SignInInterface
from .home import HomeInInterface
from .historical_event import HistoricalEventInterface
from .error import ErrorInterface
from .live_feed import LiveEventInterface
from .camera_manager import  CameraManagementInterface
 

class Interface:
    
    def __init__(self):

        self.dict_framess = None
        self.obj_RootInterface = RootInterface()
        self.dict_frames = {}
        self.frame_currentFrame = None
        
        self.add_frame(self.obj_RootInterface, SignInInterface, "signin")

        self.add_frame(self.obj_RootInterface, HomeInInterface, "home")
        self.add_frame(self.dict_frames["home"].frame_rcol_mrow, HistoricalEventInterface, "historical_event")
        self.add_frame(self.dict_frames["home"].frame_rcol_mrow, LiveEventInterface, "live_feed")
        # self.add_frame(self.dict_frames["home"].frame_rcol_mrow, SettingsInterface, "settings")
        # self.add_frame(self.dict_frames["home"].frame_rcol_mrow, AddCameraInterface, "add_camera")
        # self.add_frame(self.dict_frames["home"].frame_rcol_mrow, ShowCameraInterface, "show_camera")
        self.add_frame(self.dict_frames["home"].frame_rcol_mrow, CameraManagementInterface, "camera_manager")
    

        

    def add_frame(self, parent, frame, str_name : str):
        self.dict_frames[str_name] = frame(
            parent, 
            root_width=self.obj_RootInterface.i_root_interface_width, 
            root_height=self.obj_RootInterface.i_root_interface_height
        )
        self.dict_frames[str_name].grid(row=0, column=0, sticky="nsew")


    def switch_frames(self, name : str) -> None:
        frame = self.dict_frames[name]
        frame.tkraise()


    def on_error(self, master: str, error_heading: str = "Error", error_msg: str = "Something went wrong", bg_color : str = "#FF4B4B", i_height : int = 90) -> None:
            ErrorInterface(self.dict_frames[master], error_heading, error_msg, bg_color, i_height)



    def start_mainloop(self) -> None:
        self.obj_RootInterface.mainloop()