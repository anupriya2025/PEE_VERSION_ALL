from gui.Interface.main import Interface
from gui.Core.main import Core
# from .add_camera import AddCameraController
# from .camera_roi import CameraRoiController
from .live_feed import LiveEventController
# from .show_camera import ShowCameraController

from .signin import SignInController
# from .create_user import CreateUserController
from .home import HomeController
# from .vehicle_list import VehicleListController
# from .add_vehicle import AddVehicleController
# from .delete_vehicle import DeleteVehicleController
from .historical_event import HistoricalEventController
# from .edit_profile import EditProfileController
from  .camera_manager import CameraManagerController
# from .notification import NotificationController

class Controller:
    
    def __init__(self, Core : Core, Interface : Interface):

        self.obj_Core = Core
        self.obj_Interface = Interface

        self.obj_SignInController = SignInController(Core, Interface)
        # self.obj_CreateUserController = CreateUserController(Core, Interface)
        self.obj_HomeController = HomeController(Core, Interface)
        # self.obj_VehicleListController = VehicleListController(Core, Interface)
        # self.obj_AddVehicleController = AddVehicleController(Core, Interface)
        # self.obj_DeleteVehicleController = DeleteVehicleController(Core, Interface)
        self.obj_HistoricalEventController = HistoricalEventController(Core, Interface)
        # self.obj_EditProfileController = EditProfileController(Core, Interface)
        self.obj_LiveFeedController = LiveEventController(Core, Interface)
        # self.obj_AddCameraController = AddCameraController(Core, Interface)
        # self.obj_ShowCameraController = ShowCameraController(Core, Interface)
        # self.obj_CameraRoiController = CameraRoiController(Core, Interface)
        self.obj_CameraManagerController = CameraManagerController(Core, Interface)
        # self.obj_NotificationController =  NotificationController(Core, Interface)


    def start_application(self) -> None:
        self.obj_Interface.switch_frames("signin")
        # self.obj_Interface.switch_frames("historical_event")