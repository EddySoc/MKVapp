#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     02/09/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#project_root/actions/create_gui_menu.py

import tkinter as tk
import customtkinter as ctk

def create_gui_menu(tree, parent_menu):
    for category, items in tree.items():
        submenu = tk.Menu(parent_menu, tearoff=0)
        parent_menu.add_cascade(label=category, menu=submenu)

        for item in items:
            label = item.get("label", "Unnamed")
            action_name = item.get("action")
            entry = global_menu_registry.get(action_name)
            callback = entry["func"] if entry else None

            if callback:
                submenu.add_command(label=label, command=callback)
            else:
                submenu.add_command(label=label, state="disabled")

""" example
root = ctk.CTk()
menubar = tk.Menu(root)
create_gui_menu(build_menu_tree(global_menu_registry), menubar)
root.config(menu=menubar)
root.mainloop()
"""