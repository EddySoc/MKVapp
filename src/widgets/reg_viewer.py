#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     29/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from .layout_primitives import MyFrame

class RegistryViewer(MyFrame):
    def __init__(self, master, name_map, **kwargs):
        super().__init__(master, **kwargs)
        self.name_map = name_map

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.search = CTkEntry(self, placeholder_text="Search registry...")
        self.search.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        self.listbox = CTkListBox(self)
        self.listbox.grid(row=1, column=0, sticky="nsew", padx=10)

        for name, path in self.name_map.items():
            self.listbox.insert("end", f"{name} → {path}")

        self.detail = CTkLabel(self, text="", anchor="w")
        self.detail.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

    def toggle(self):
        if self.winfo_ismapped():
            self.grid_remove()
        else:
            self.grid()