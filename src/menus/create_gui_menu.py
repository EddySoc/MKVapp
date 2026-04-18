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

        # Force custom order for 'videos' menu
        if category == "videos":
            desired_order = [
                "Play Video",
                "Transform -> MKV",
                "MKV -> 8 Bit HEVC",
                "Inspect Video Info",
                "Check Subs Language",
                "Extract Subs",
                "Download Sub",
                "Embed Sub",
                "Remove All Subs",
                "Speech to SRT (Whisper)"
            ]
            # Maak een dict van label → item
            item_map = {item.get("label", "Unnamed"): item for item in items}
            # Sorteer volgens gewenste volgorde, rest achteraan
            sorted_items = [item_map[label] for label in desired_order if label in item_map]
            # Voeg overige items toe die niet in desired_order staan
            sorted_items += [item for label, item in item_map.items() if label not in desired_order]
        else:
            sorted_items = items

        for item in sorted_items:
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