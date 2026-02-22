#-------------------------------------------------------------------------------
# Name:        statusslot.py
# Purpose:
#
# Author:      EddyS
#
# Created:     08/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import customtkinter as ct
# Lazy import to avoid circular dependency
# from shared_data import get_shared

class StatusSlot(ct.CTkFrame):
    def __init__(self, master, height=24, **kwargs):
        super().__init__(master, height=height, **kwargs)

        # Make sure the frame's grid allows expansion
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)  # progress bar gets most space
        self.grid_columnconfigure(1, weight=0)  # percentage label fixed width

        # 💬 Label fills entire frame (spans both columns)
        self.label = ct.CTkLabel(self, text="", anchor="w")
        self.label.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5)

        # 📊 Progress bar in left column
        self.progress = ct.CTkProgressBar(self, height=20)
        self.progress.grid(row=0, column=0, sticky="nsew", padx=(5, 2))
        self.progress.grid_remove()
        
        # 🔢 Percentage label in right column
        self.progress_label = ct.CTkLabel(
            self, 
            text="", 
            anchor="center", 
            font=("Arial", 11, "bold"),
            width=50
        )
        self.progress_label.grid(row=0, column=1, sticky="ns", padx=(2, 5))
        self.progress_label.grid_remove()

        self.mode = "label"  # keep track of current mode ("label" or "progress")

    def show_message(self, text, color=None):
        """Display a static text message"""
        self.progress.stop()
        self.progress.grid_remove()
        self.progress_label.grid_remove()
        self.label.configure(text=text)
        if color:
            self.label.configure(text_color=color)
        self.label.grid()
        self.mode = "label"

    def show_progress(self, mode="indeterminate"):
        """Show the progress bar"""
        self.label.grid_remove()
        self.progress.configure(mode=mode)
        self.progress.grid()
        self.progress_label.grid()
        
        if mode == "indeterminate":
            self.progress.start()
            self.progress_label.configure(text="")
        else:
            self.progress_label.configure(text="0%")
        self.mode = "progress"
    
    def update_progress(self, value, percentage_text=None):
        """Update progress bar and percentage label"""
        self.progress.set(value)
        if percentage_text is None:
            percentage_text = f"{int(value * 100)}%"
        self.progress_label.configure(text=percentage_text)

    def reset(self):
        """Reset both widgets and always show empty label"""
        self.label.configure(text="")
        self.label.grid()
        self.progress.stop()
        self.progress.set(0)
        self.progress_label.configure(text="")
        self.progress_label.grid_remove()
        self.progress.grid_remove()
        self.mode = "label"

    def show_tagged_message(self, message, tag):
        from shared_data import get_shared
        config = get_shared().config
        tags_cfg = config.get("tags_cfg", {})
        tag_style = tags_cfg.get(tag, {})
        icon = tag_style.get("icon", "")
        color = tag_style.get("fg", "#eeeeee")

        self.show_message(f"{icon} {message}", color=color)
