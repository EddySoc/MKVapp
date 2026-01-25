from decorators.decorators import menu_tag
#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     11/09/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# project_root/actions/actions/tools/popup_preview.py

import tkinter as tk
try:
    from customtkinter import get_appearance_mode
except Exception:
    def get_appearance_mode():
        return "Dark"

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from menus.menu_registry import global_menu_registry
from menus.popup import MENU_COMPOSITIONS

class PopupPreviewTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Popup Preview Tool")
        self.geometry("600x700")

        canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # expose canvas for wheel handling
        self.canvas = canvas

        # Mouse wheel scrolling: bind when pointer enters canvas, unbind on leave
        def _bind_wheel(event):
            if sys.platform.startswith("linux"):
                # X11 uses Button-4/5
                self.bind_all("<Button-4>", self._on_mousewheel)
                self.bind_all("<Button-5>", self._on_mousewheel)
            else:
                # Windows/Mac use MouseWheel (delta)
                self.bind_all("<MouseWheel>", self._on_mousewheel)

        def _unbind_wheel(event):
            if sys.platform.startswith("linux"):
                try:
                    self.unbind_all("<Button-4>")
                    self.unbind_all("<Button-5>")
                except Exception:
                    pass
            else:
                try:
                    self.unbind_all("<MouseWheel>")
                except Exception:
                    pass

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        theme = get_appearance_mode() or "Dark"
        is_dark = str(theme).lower().startswith("dark")
        frame = None
        for popup_key in sorted(MENU_COMPOSITIONS.keys()):
            frame = tk.LabelFrame(scroll_frame, text=f"Popup: {popup_key}", padx=10, pady=5)
            frame.pack(fill="x", padx=10, pady=5)

            menu = tk.Menu(frame, tearoff=0)
            self.build_menu(menu, popup_key)

            for i in range(menu.index("end") + 1 if menu.index("end") is not None else 0):
                entry_type = menu.type(i)
                # separators and some entry types don't support 'label' or 'state'
                if entry_type == "separator":
                    tk.Label(frame, text="—", anchor="w", fg="gray").pack(fill="x")
                    continue
                try:
                    label = menu.entrycget(i, "label")
                except Exception:
                    label = entry_type
                try:
                    state = menu.entrycget(i, "state")
                except Exception:
                    state = "normal"
                display = f"• {label}" if state != "disabled" else f"🔹 {label}"
                if is_dark:
                    fg_disabled = "gray"
                    fg_normal = "white"
                else:
                    fg_disabled = "gray"
                    fg_normal = "black"
                tk.Label(frame, text=display, anchor="w", fg=(fg_disabled if state == "disabled" else fg_normal)).pack(fill="x")

    def build_menu(self, menu, popup_key):
        registry = global_menu_registry

        def add_items_from_group(group_name):
            labels = registry.grouped().get(group_name, [])
            for label in labels:
                # Skip YAML/registry placeholders and explicitly-tagged placeholders
                if isinstance(label, str) and label.strip().lower().startswith("(placeholder"):
                    continue
                entry = registry.get(label)
                if not entry:
                    continue
                if entry.get("tag") == "placeholder":
                    continue
                func = entry.get("func")
                menu.add_command(label=label, command=func)

        for part in MENU_COMPOSITIONS[popup_key]:
            if part == "__title__":
                menu.add_command(label=popup_key, state="disabled")
            elif part == "__sep__":
                menu.add_separator()
            else:
                add_items_from_group(part)

    def _on_mousewheel(self, event):
        try:
            if sys.platform.startswith("linux"):
                # Button-4 = up, Button-5 = down
                if getattr(event, 'num', None) == 4:
                    delta = -1
                elif getattr(event, 'num', None) == 5:
                    delta = 1
                else:
                    return
            else:
                # On Windows event.delta is multiple of 120; invert for natural scroll
                delta = -1 * int(event.delta / 120)
            # Scroll the canvas
            self.canvas.yview_scroll(delta, "units")
        except Exception:
            pass

    @menu_tag(label="Popup Preview",icon="🔍",group=["tb_debug"])
    def popup_preview():
        PopupPreviewTool()

"""
if __name__ == "__main__":
    PopupPreviewTool().mainloop()
"""