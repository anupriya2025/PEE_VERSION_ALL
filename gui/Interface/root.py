from customtkinter import CTk
from sympy import false


class RootInterface(CTk):

    def __init__(self):

        super().__init__()

        self.i_client_area_width = self.winfo_screenwidth()
        self.i_client_area_height = self.winfo_screenheight()

        self.i_root_interface_width = int(self.i_client_area_width * 1)
        self.i_root_interface_height = int(self.i_client_area_height * 1)

        self.i_initial_x_pos = (self.i_client_area_width // 2) - (self.i_root_interface_width // 2)
        self.i_initial_y_pos = (self.i_client_area_height // 2) - (self.i_root_interface_height // 2)

        self.configure(fg_color = "white")

        self.geometry(f"{self.i_root_interface_width}x{self.i_root_interface_height}+{self.i_initial_x_pos}+{self.i_initial_y_pos}")
        # self.resizable(False, False)
        # self.state("zoomed")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.title("ℤ𝕠𝕟𝕖 𝕀𝕟𝕥𝕣𝕦𝕤𝕚𝕠𝕟 𝕊𝕪𝕤𝕥𝕖𝕞")
        # self.resizable(False,False)