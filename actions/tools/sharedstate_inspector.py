#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     06/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import customtkinter as ct
from decorators.decorators import menu_tag
from shared_data import get_shared, get_config

class SharedStateInspact(ct.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        print("✅ SharedStateInspact init started")
        self.title("🛠️ SharedState Inspector")
        self.geometry("400x500+100+100")  # width x height + x-offset + y-offset
        # Make the toplevel resizeable and let contents expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.lift()  # Bring it to the top of the window stack
        #self.attributes("-topmost", True)  # Force it to appear above all
        self.after(10, lambda: self.attributes("-topmost", False))  # Let it behave normally afterward

        print("✅ Building UI...")
        self.build_ui()

    def build_ui(self):
        self.entries = {}

        self.scroll_frame = ct.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll_frame.grid_rowconfigure(0, weight=0)
        # Give label a small weight and entry column the bulk so entries expand
        self.scroll_frame.grid_columnconfigure(0, weight=1)  # Label
        self.scroll_frame.grid_columnconfigure(1, weight=10)  # Entry — this is what stretches

        row = 0

        # Config data section
        cfg = get_config().get("persistent_cfg", {})
        row = self.section_label("📦 config_mgr.data", row, parent=self.scroll_frame)
        for key, value in cfg.items():
            #print(f"key = {key}  value = {value}")
            row = self.add_row(key, value, row, config_target="config", parent=self.scroll_frame)

        # Shared state section
        s = get_shared()
        row = self.section_label("🔁 Shared State", row, parent=self.scroll_frame)
        for key, value in vars(s).items():
            if key in ("gui_queue", "log_queue", "update_queue"):
                continue
            try:
                val = value.get() if hasattr(value, "get") else str(value)
            except Exception as ex:
                val = f"<unreadable: {ex}>"
            row = self.add_row(key, val, row, config_target="shared", parent=self.scroll_frame)

        # Save button placed below the scrollable data area, full-width row
        btn_frame = ct.CTkFrame(self)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        btn_frame.grid_columnconfigure(0, weight=1)
        ct.CTkButton(btn_frame, text="Save", command=self.save).grid(row=0, column=0, sticky="e")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Ensure scroll_frame width follows toplevel width
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        try:
            # subtract some padding to avoid scrollbars popping unnecessarily
            new_w = max(200, self.winfo_width() - 40)
            self.scroll_frame.configure(width=new_w)
        except Exception:
            pass

    def add_row(self, key, value, row, config_target, parent):
        # Use a dedicated row frame so label+entry share the full width reliably
        row_frame = ct.CTkFrame(parent)
        row_frame.grid(row=row, column=0, columnspan=2, sticky="we", padx=2, pady=2)
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=10)

        ct.CTkLabel(row_frame, text=key).grid(row=0, column=0, sticky="e", padx=6)
        entry = ct.CTkEntry(row_frame)
        entry.grid(row=0, column=1, sticky="we", padx=6)
        entry.insert(0, str(value))  # 🛠️ This sets the initial content
        self.entries[(config_target, key)] = entry
        return row + 1

    def section_label(self, text, row, parent):
        ct.CTkLabel(parent, text=text, font=("Segoe UI", 12, "bold")).grid(
            row=row, column=0, columnspan=2, pady=(10, 5), sticky="we"
        )
        return row + 1

    def save(self):
        s = get_shared()
        config = get_config()
        for (target, key), entry in self.entries.items():
            value = entry.get()
            if target == "config":
                try:
                    config.setdefault("persistent_cfg", {})[key] = value
                except Exception:
                    pass
            elif target == "shared":
                try:
                    attr = getattr(s, key, None)
                    if hasattr(attr, "set"):
                        attr.set(value)
                    else:
                        # Attempt simple assignment if attribute exists
                        if hasattr(s, key):
                            setattr(s, key, value)
                except Exception:
                    pass
        self.destroy()

"""
def show_sharedstate_inpector(master=None):
    try:
        print("🛠️ Launching SharedStateInspact")
        SharedStateInspact(master).grab_set()
    except Exception as e:
        print(f"❌ Failed to launch inspector: {e}")

"""
@menu_tag(label="Inspect SharedState",icon="🔍",group=["tb_debug"])
def show_sharedstate_inpector(master=None):
    win = SharedStateInspact(master)
    win.deiconify()
    win.lift()
    win.grab_set()
    win.focus_force()
    print("✅ Popup should be visible")
