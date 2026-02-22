#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     08/08/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from customtkinter import CTkButton, CTkToplevel

class FloatingPopupButton(CTkButton):
    def __init__(
        self,
        master,
        popup_class,
        popup_kwargs=None,
        text="Toggle Popup",
        offset_x=-310,
        offset_y=0,
        popup_size=(300, 500),
        on_open=None,
        on_close=None,
        **button_kwargs
    ):
        """
        master: parent widget for the button (e.g. a frame)
        popup_class: class that inherits from CTkToplevel
        popup_kwargs: optional kwargs to pass to popup_class
        offset_x / offset_y: position offset from app window
        popup_size: (width, height) of the popup
        on_open / on_close: optional callbacks
        """
        super().__init__(master, text=text, command=self.toggle_popup, **button_kwargs)

        self.popup_class = popup_class
        self.popup_kwargs = popup_kwargs or {}
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.popup_width, self.popup_height = popup_size
        self.on_open = on_open
        self.on_close = on_close
        self.popup_instance = None

    def toggle_popup(self):
        if self.popup_instance is None or not self.popup_instance.winfo_exists():
            self.show_popup()
        else:
            self.hide_popup()

    def show_popup(self):
        # Use the top-level window as master
        root_window = self.master.winfo_toplevel()
        self.popup_instance = self.popup_class(master=root_window, **self.popup_kwargs)

        # Position the popup outside the app window
        app_x = root_window.winfo_rootx()
        app_y = root_window.winfo_rooty()
        self.popup_instance.geometry(
            f"{self.popup_width}x{self.popup_height}+{app_x + self.offset_x}+{app_y + self.offset_y}"
        )

        self.popup_instance.protocol("WM_DELETE_WINDOW", self.on_popup_closed)
        self.popup_instance.lift()
        self.popup_instance.focus_force()

        if self.on_open:
            self.on_open()

    def hide_popup(self):
        if self.popup_instance and self.popup_instance.winfo_exists():
            self.popup_instance.destroy()
            self.popup_instance = None
            if self.on_close:
                self.on_close()

    def on_popup_closed(self):
        self.popup_instance = None
        if self.on_close:
            self.on_close()