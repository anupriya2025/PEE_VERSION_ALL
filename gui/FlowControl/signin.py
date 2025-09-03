from gui.Core.main import Core
from gui.FlowControl.home import HomeController
from gui.Interface.main import Interface
from time import sleep


class SignInController:

    def __init__(self, Core: Core, Interface: Interface):
        self.obj_Core = Core
        self.obj_Interface = Interface
        self.obj_SigninInterface = self.obj_Interface.dict_frames["signin"]
        self.obj_HomeController= HomeController(Core,Interface)

        self.bind_buttons()
        self.bind_enter_key()

    def bind_buttons(self) -> None:
        self.obj_SigninInterface.button_signin.configure(command=self.signin)
        self.obj_SigninInterface.entry_username.delete(0, 'end')
        self.obj_SigninInterface.entry_username.insert(0, "admin")
        self.obj_SigninInterface.entry_password.delete(0, 'end')
        self.obj_SigninInterface.entry_password.insert(0, "admin")

    def bind_enter_key(self) -> None:
        # Bind Enter key differently for each field
        self.obj_SigninInterface.entry_username.bind('<Return>', lambda event: self.focus_next_field(event))
        self.obj_SigninInterface.entry_password.bind('<Return>', lambda event: self.signin(event))


    def focus_next_field(self, event) -> None:
        # Move focus to password field when Enter is pressed in email field
        self.obj_SigninInterface.entry_password.focus()
        return "break"  # Prevents the default Enter behavior

    def signin(self, event=None) -> None:
      
        username = self.obj_SigninInterface.entry_username.get()
        password = self.obj_SigninInterface.entry_password.get()

        if (username == "" or password == ""):
            self.obj_Interface.on_error("signin", "Invalid Password",
                                        "The password that you've entered is incorrect. Please try again.", "#FF4B4B")

        else:
            self.obj_SigninInterface.update_Login_Button("Loading...", "disable")
            dict_Status = self.obj_Core.obj_Authentication.check_signin_credential(username, password)
            self.obj_SigninInterface.update_Login_Button("Signin", "normal")

            if dict_Status["str_error_msg_heading"] == "" and dict_Status["str_error_msg"] == "":
                self.obj_SigninInterface.reset_interface()
                self.obj_Interface.dict_frames["home"].update_user_popup_data(
                    self.obj_Core.dict_user_data["str_user_name"])

                self.obj_Interface.switch_frames("home")
                # self.obj_Interface.switch_frames("live_feed")
                

                


                # # i_camera_count = self.obj_Core.obj_Camera.get_camera_count()
                # # print(i_camera_count,"***************************************************************************************** mkskdk")
                # i_camera_count = 1
                # if (i_camera_count > 0):
                #  print(i_camera_count,"****************************************************")
                #  self.obj_Interface.switch_frames("live_feed")
                # #     self.obj_Interface.dict_frames['home'].update_menu_buttons_state(
                # #         self.obj_Interface.dict_frames['home'].button_live_event)
                # #     self.obj_Interface.dict_frames["home"].show_frame_camera()
                # else:
                #     print("else factoreeeee is here ")
                #     self.obj_Interface.switch_frames("live_feed")
                #     # self.obj_HomeController.onclick_settings_button()
                #     # self.obj_Interface.dict_frames['home'].button_camera_settings.invoke()

            else:
                self.obj_Interface.on_error("signin", dict_Status["str_error_msg_heading"],
                                            dict_Status["str_error_msg"], "#FF4B4B")