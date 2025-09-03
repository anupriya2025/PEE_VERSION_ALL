import platform
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import messagebox

class LoginPage:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("SIGNIN")
        self.root.geometry("1900x1000")
        self.root.minsize(1000, 1000)

        if platform.system() == "Windows":
            self.root.state('zoomed')
        else:
            self.root.attributes('-zoomed', True)

        self.create_login_ui()

    def create_login_ui(self):
        # Load and place background image
        try:
            # E:\DEV_DRIVE\PPE_DEV_ANU\resource\video\7.png
            bg_image = Image.open("E:\\DEV_DRIVE\\PPE_DEV_ANU\\resource\\login.jpg")
            bg_image = bg_image.resize((1920, 1080), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg_image)  # FIXED

            bg_label = ctk.CTkLabel(self.root, image=self.bg_photo, text="")
            bg_label.place(relwidth=1, relheight=1)  # Full window
        except Exception as e:
            print("Background image not found:", e)

        # Login frame (centered, smaller size so background is visible)
        frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=20)
        frame.place(relx=0.5, rely=0.5, anchor="center")  # FIXED

        # Logo
        try:
            logo_img = ctk.CTkImage(Image.open("logo.png"), size=(300, 400))
            logo_label = ctk.CTkLabel(frame, image=logo_img, text="")
            logo_label.image = logo_img
            logo_label.pack(pady=(15, 5))
        except:
            pass

        title = ctk.CTkLabel(frame, text="Secure Login", font=("", 20, "bold"), corner_radius=10)
        title.pack(pady=(0, 10))

        self.username_entry = ctk.CTkEntry(frame, placeholder_text="Username", width=250)
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=250)
        self.password_entry.pack(pady=10)

        login_btn = ctk.CTkButton(frame, text="Login", command=self.validate_login, width=150)
        login_btn.pack(pady=20)

    def validate_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == "123" and password == "123":
            self.root.destroy()
            return True
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
            return False

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    login_app = LoginPage()
    login_app.run()
