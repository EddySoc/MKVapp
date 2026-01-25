#-------------------------------------------------------------------------------
# Name:        layout_primitives.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import customtkinter as ct

class MyFrame(ct.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.configure(
            border_color="cyan",
            border_width=2,
            bg_color="black"
        )