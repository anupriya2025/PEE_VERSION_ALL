from customtkinter import CTkFrame, CTkLabel
from PIL import Image


class ErrorInterface(CTkFrame):
    def __init__(self, master, error_heading: str, error_msg: str, bg_color: str, i_height: int):
        self.expanded_width = 350
        self.initial_width = 0

        super().__init__(
            master,
            width=self.initial_width,
            height=i_height,
            corner_radius=1,
            fg_color=bg_color
        )
        self.pack_propagate(False)
        self.place(relx=1.001, rely=0.99, x=-13, anchor="se")  # Add 13-pixel gap from right

        self.label_error_heading = CTkLabel(
            self,
            text=error_heading,
            text_color="white",
            font=("Segoe UI", 20, "bold"),
            anchor="center"
        )
        self.label_error_heading.pack(side="top", fill="x", expand=True, pady=(5, 0))

        self.label_error_msg = CTkLabel(
            self,
            text=error_msg,
            text_color="white",
            font=("", 14),
            wraplength=250
        )
        self.label_error_msg.pack(side="top", fill="x", expand=True, pady=(0, 5))

        self.animate_frame(expanding=True)

    def animate_frame(self, expanding=True, step=20):
        current_width = self.cget("width")
        target_width = self.expanded_width if expanding else self.initial_width

        if (expanding and current_width < target_width) or (not expanding and current_width > target_width):
            new_width = current_width + step if expanding else current_width - step
            self.configure(width=new_width)
            self.after(10, self.animate_frame, expanding, step)
        elif expanding:
            self.after(5000, self.animate_frame, False, step)
        elif not expanding and current_width <= self.initial_width:
            self.destroy()
