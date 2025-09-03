from customtkinter import CTkFrame, CTkLabel, CTkEntry, CTkButton, CTkImage
from tkinter import Canvas
from PIL import Image, ImageTk

class SignInInterface(CTkFrame):

    def __init__(self, *args,root_width: int = 1920, root_height: int = 1080, **kwargs):
        super().__init__(*args, **kwargs)

        self.configure(fg_color="#FFFFFF")
        self.show_password = False


        show_password_icon_path ="E:/DEV_DRIVE/PPE_DEV_ANU/resource/video/show_password.png"
        hide_password_icon_path = "E:/DEV_DRIVE/PPE_DEV_ANU/resource/video/hide_password.png"
        # E:\DEV_DRIVE\PPE_DEV_ANU\resource\video\hide_password.png



        # Store both eye icons
        self.show_password_icon = CTkImage(Image.open(show_password_icon_path), size=(20, 20))
        self.hide_password_icon = CTkImage(Image.open(hide_password_icon_path), size=(25, 25))

        self.columnconfigure(0, weight=1, uniform='a')
        self.columnconfigure(1, weight=1, uniform='a')
        self.rowconfigure(0, weight=1)

        self.img_signin_bg_original = Image.open("resource/login_PPE.png")
        self.img_signin_bg_display = None

        self.cnv_image = Canvas(self, bd=0, highlightthickness=0, relief='ridge')
        self.cnv_image.grid(column=0, row=0, sticky="nsew")
        self.cnv_image.bind('<Configure>', self.update_background_image)

        i_form_width = int(root_width * 0.29)
        i_form_height = int(root_height * 0.5)

        # Main form frame
        self.frame_form = CTkFrame(
            self,
            height=i_form_height,
            width=i_form_width,
            fg_color="#FFFFFF"
        )
        self.frame_form.grid(column=1, row=0)

        # Welcome label
        self.label_welcome = CTkLabel(
            self.frame_form,
            text="Welcome Back!",
            text_color="#2c2c2c",
            font=("Segoe UI", 24, "bold")
        )
        self.label_welcome.grid(row=0, column=0, pady=(0, 20))

        # Email label and entry
        self.label_username = CTkLabel(
            self.frame_form,
            text="User Name",
            text_color="#2c2c2c",
            font=("", 14)
        )
        self.label_username.grid(row=1, column=0, sticky="w", pady=(20, 0))

        self.entry_username = CTkEntry(
            self.frame_form,
            width=i_form_width,
            height=45,
            corner_radius=35,
            border_width=2,
            border_color="#828282",
            fg_color="#FFFFFF",
            placeholder_text="Enter User Name",
            text_color="#414141",
            font=("", 13.5)
        )
        self.entry_username.grid(row=2, column=0)

        # Password label
        self.label_password = CTkLabel(
            self.frame_form,
            text="Password",
            text_color="#2c2c2c",
            font=("", 14)
        )
        self.label_password.grid(row=3, column=0, sticky="w", pady=(12, 0))

        # Container for password field and eye button
        self.password_container = CTkFrame(
            self.frame_form,
            fg_color="transparent",
            width=i_form_width
        )
        self.password_container.grid(row=4, column=0, sticky="ew")
        self.password_container.grid_columnconfigure(0, weight=1)

        # Password entry
        self.entry_password = CTkEntry(
            self.password_container,
            width=i_form_width,
            height=45,
            corner_radius=35,
            border_width=2,
            border_color="#828282",
            fg_color="#FFFFFF",
            placeholder_text="Enter Password",
            text_color="#414141",
            font=("", 13.5),
            show="●"
        )
        self.entry_password.grid(row=0, column=0, sticky="ew")

        # Eye button with initial hidden password icon
        self.eye_button = CTkButton(
            self.entry_password,
            width=30,
            height=30,
            corner_radius=20,
            border_width=0,
            fg_color="transparent",
            image=self.hide_password_icon,
            text="",
            cursor="hand2",
            command=self.toggle_password_visibility,
            hover=False
        )
        self.eye_button.place(relx=0.975, rely=0.5, anchor="e")

        # Sign in button
        self.button_signin = CTkButton(
            self.frame_form,
            width=i_form_width,
            height=40,
            corner_radius=35,
            border_color="#3A36F5",
            fg_color="#3A36F5",
            text="Sign In",
            text_color="#FFFFFF",
            font=("", 14),
            cursor="hand2",
            hover=False
        )
        self.button_signin.grid(row=5, column=0, pady=(28, 0))


    def toggle_password_visibility(self):
        """Toggle password visibility between shown and hidden"""
        self.show_password = not self.show_password
        self.entry_password.configure(show="" if self.show_password else "●")
        self.eye_button.configure(
            image=self.show_password_icon if self.show_password else self.hide_password_icon
        )

    def update_background_image(self, event) -> None:
        image_resized = self.img_signin_bg_original.resize((event.width, event.height))
        self.img_signin_bg_display = ImageTk.PhotoImage(image_resized)
        self.cnv_image.create_image(0, 0, image=self.img_signin_bg_display, anchor='nw')

    def update_Login_Button(self, button_text: str = None, button_state: str = None):
        if button_state is not None:
            self.button_signin.configure(text=button_text, state=button_state)
        self.update()

    def reset_interface(self):
        self.entry_username.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.entry_username.configure(placeholder_text="Enter Username")
        self.entry_password.configure(placeholder_text="Enter Password")
        self.show_password = False
        self.entry_password.configure(show="●")
        self.eye_button.configure(image=self.hide_password_icon)
        self.frame_form.focus()