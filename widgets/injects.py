#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     06/08/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def inject_registry_toggle_button(self):
    # Create the toggle button on the last row, column 8
    btn_toggle = CTkButton(
        master=self.app.last_row,
        text="🔍 Widget Registry",
        command=self.toggle_registry_panel
    )
    btn_toggle.grid(row=0, column=8, padx=10, pady=5, sticky="ew")
    btn_toggle.bind("<Enter>", lambda e: print("View all registered widgets"))

    # Optional styling for clarity
    btn_toggle.configure(fg_color="lightgray", border_width=1)

def inject_grid_test_button(self):
    # Create a popup menu
    #self.test_menu = tk.Menu(self.app, tearoff=0)
    #self.test_menu.add_command(label="Hello!", command=lambda: print("Hi Eddy 👋"))

    # Inject into a known grid slot — for example, bottom row (last_row)
    btn = CTkButton(self.app.last_row, text="Right-Click Test")
    btn.custom_name="tb_debug"  # will show the tb_debug popup menu
    btn.grid(row=0, column=8, padx=10, pady=5, sticky="ew")  # adjust column as needed

    # Bind right-click event to the popup menu
    btn.bind("<Button-3>", lambda e: self.s.pop_menu.show_popup("tb_debug", e))

def inject_viewer_panel_button(self):
    from widgets.debug_frame import Debug_Frame
    from widgets.pop_button import FloatingPopupButton

    toggle_btn = FloatingPopupButton(
        master=self.app.last_row,
        popup_class=Debug_Frame,
        text="Toggle Viewer",
        offset_x=-310,
        offset_y=0,
        popup_size=(300, 500),

        on_open=lambda: print("Viewer opened"),
        on_close=lambda: print("Viewer closed")
    )

    toggle_btn.grid(row=0, column=9, padx=5, pady=5, sticky="ew")

