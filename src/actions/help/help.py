#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     31/08/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import customtkinter as ctk
from decorators.decorators import menu_tag

@menu_tag(label="Show Help",icon="ℹ️",group=["help"])
def show_help_dialog():
    from shared_data import get_shared
    s = get_shared()
    app = s.app
    
    try:
        help_win = ctk.CTkToplevel(app)
        help_win.title("Help")
        help_win.geometry("400x300+200+200")
        help_win.attributes('-topmost', True)  # Bring to front

        ctk.CTkLabel(help_win, text="🆘 Help & Info", font=("Segoe UI", 20)).pack(pady=10)

        help_text = (
            "This app lets you interact with widgets via context menus.\n\n"
            "🔹 Right-click to access options.\n"
            "🔹 Use 'Clear Textbox' to reset fields.\n"
            "🔹 To add text: Click in a textbox and type or paste.\n"
            "🔹 Explore submenus for advanced actions.\n\n"
            "Need more help? Contact support or check the docs."
        )

        textbox = ctk.CTkTextbox(help_win, width=360, height=150)
        textbox.insert("0.0", help_text)
        textbox.pack(pady=10)
        ctk.CTkButton(help_win, text="Close", command=help_win.destroy).pack(pady=10)

    except Exception as ex:
        print(f"❌ Help dialog failed: {ex}")