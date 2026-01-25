#-------------------------------------------------------------------------------
# Name:        module1als ik in
# Purpose:
#
# Author:      EddyS
#
# Created:     08/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys
print("[DEBUG] Python executable:", sys.executable)
# app_launcher.py

import customtkinter as ct
import tkinter as tk
import queue
import os

from utils.shared_utils import register_shared
print("[DEBUG] Python executable:", sys.executable)
from utils.utils import initialize_gui_vars
from mkvapp.lifecycle import update_on_start
from config import sync_config_to_state, smart_config_manager,get_config_manager
from config.smart_config_manager import config_mgr
from menus import Popup
from binding import BindingManager, WidgetNameResolver
from shared_data import get_shared
from customtkinter.windows.widgets.ctk_button import CTkButton
from widgets.smart_entry import SmartEntry
from logger_singleton import logger
from mkvapp import build_layout as ui_build_layout
from menus import menu_registry, write_yaml_to_settings, generate_yaml_from_registry
from menus.menu_registry import global_menu_registry

# Forceer import van actions.lb_files zodat alle menu-items (ook subtitles) worden geregistreerd
import actions.lb_files
from menus.init_loader import load_all_actions


# Monkey Patch CTkButton
_orig_draw = CTkButton._draw
def _safe_draw(self, no_color_updates=False):
    try:
        _orig_draw(self, no_color_updates=no_color_updates)
    except tk.TclError:
        return
CTkButton._draw = _safe_draw

def inject_config_into_shared():
    get_config_manager().load_config()  # Load config from file or source
    config = smart_config_manager.config_mgr.data  # ?? Access the loaded config directly

    if config is None:
        raise RuntimeError("Config failed to load. Check config_manager or config file integrity.")

    shared = get_shared()
    shared.config_manager = get_config_manager()
    shared.config = config  # ?? Now get_config() will work

    if shared.config is smart_config_manager.config_mgr.data:
        #logger.info("? shared.config and config_mgr.data are the same object.")
        pass
    else:
        logger.warning("?? shared.config and config_mgr.data are different objects.")

    return shared

class AppLauncher:
    def __init__(self):
        print("Booting...")

        # ? First: inject config and get shared state
        self.s = inject_config_into_shared()

        # ? Now it's safe to use self.s
        # config = self.s.config

        # immediately grab the config manager singleton
        self.config_mgr = get_config_manager()
        self.config_mgr.load_config()

        # GUI setup
        self.app = ct.CTk()
        self.app.geometry("1250x685")
        self.app.title("MKV App (Refactored)")
        self.app.grid_rowconfigure(0, weight=1)
        self.app.grid_columnconfigure(0, weight=1)

        # Menu and resolver setup
        self.menus = smart_config_manager.config_mgr.data.get("popmenu_cfg", {}).copy()
        self.widget_name_map = {}

        self.resolver = WidgetNameResolver(
            root_widget=self.app,
            config_data = config_mgr.data,
            scan_mode="all",
            widget_name_map=self.widget_name_map,
        )

        sys.stdout.flush()
    """
    def launch(self):
        self.resolver.auto_register_from(self.app)       # ? populate registry
        self.setup_shared_state()                        # ? now it's safe
    """

    def setup_shared_state(self):
        # 🔁 Get shared singleton
        self.s = get_shared()

        # ⚙️ Load config via SmartConfigManager
        from config.smart_config_manager import get_config_manager
        self.config_mgr = get_config_manager(shared=self.s)
        config = self.config_mgr.get_all()

        # 🧠 Store config in shared state
        self.s.config_data = config
        self.s.config = config

        # 🎨 Initialize GUI variables and fonts
        initialize_gui_vars()
        self.s.init_fonts()
        self.s.gui_queue = queue.Queue()
        self.s.inc_subs_var = tk.BooleanVar(value=True)
        self.s.segbut_var = tk.StringVar(value="Videos")

        # 📋 Initialize popup menu manager
        self.s.pop_menu = Popup(self.app, resolver=self.resolver, shared_state=self.s, action_lookup=menu_registry)

        # 🗂️ Organize menu entries by tag
        registry = global_menu_registry
        for label, entry in registry.all().items():
            group = entry.get("tag", "default")
            self.s.pop_menu.menus.setdefault(group, []).append(label)

        # 🧱 Build actual tk.Menu objects
        self.s.pop_menu.menu_objects = {}  # Optional: store built menus

        #print(f"📦 menu_registry keys: {list(menu_registry.get_keys())}")
        #print(f"🧠 Dynamic actions available: {list(menu_registry.get_keys())}")

        for group_name, entries in self.s.pop_menu.menus.items():
            menu = tk.Menu(self.app, tearoff=0)
            resolved_key = "default"
            self.s.pop_menu.current_menu_group = resolved_key
            self.s.pop_menu.build_menu_entries(menu, entries, self.s.pop_menu.action_lookup)
            self.s.pop_menu.menu_objects[group_name] = menu

        # 🔗 Register shared components
        register_shared(
            app=self.app,
            entry_data={},
            last_entry=None,
            segbut_var=self.s.segbut_var,
            inc_subs_var=self.s.inc_subs_var,
            TK_FONT=self.s.TK_FONT,
            CTK_FONT=self.s.CTK_FONT,
            gui_queue=self.s.gui_queue,
            manager=None,
            pop_menu=self.s.pop_menu,
            dirtree_lst=[],
            files_lst=[],
            vids_lst=[],
            subs_lst=[],
            upd_lst=[],
        )

        yaml_path = os.path.join(self.config_mgr.basedir if hasattr(self.config_mgr, 'basedir') else os.path.dirname(os.path.abspath(__file__)), "Settings", "menus.yaml")
        if not os.path.exists(yaml_path):
            print("⚠️ menus.yaml not found — generating from registry...")
            yaml_data = generate_yaml_from_registry()
            write_yaml_to_settings(yaml_data)
        else:
            print("✅ menu_config.yaml already exists — skipping generation.")

        # 🎨 Apply theme from config
        theme = config.get("persistent_cfg", {}).get("Theme", "dark")
        ct.set_appearance_mode(theme)

    def build_layout(self, config):
        try:
            # ✅ Hand off to UI layout builder
            ui_build_layout(
                self.app,
                self.s.config_data,
                self.config_mgr
            )
            print("✅ ui_build_layout completed")
        except Exception as e:
            import traceback
            print(f"💥 ui_build_layout crash: {e}")
            traceback.print_exc()

        root_widget = self.app

        try:
            # ✅ Sync SmartEntry instances
            SmartEntry.sync_all()

            # ✅ Debug entry states
            for label in ["source", "target", "backup"]:
                smart = self.s.entry_data[label]["entry"]
                var = self.s.entry_data[label]["var"]
                # print(f"?? {label}: SmartEntry.value = '{smart.value}', StringVar = '{var.get()}'")

            # ✅ Update entry styles
            from utils.scan_helpers import update_entry_styles
            update_entry_styles(self.s)

            # ✅ Build widget path → name map
            self.widget_path_map = self.resolver.build_path_to_name_map()

            # ✅ Collect named widgets
            self.named = self.resolver.collect_named_widgets()

        except Exception as e:
            import traceback
            print(f"?? Layout post-processing crash: {e}")
            traceback.print_exc()

    def bind_events(self):
        manager = BindingManager(self.app, self.s.pop_menu)
        self.s.binding_manager = manager
        self.s.app = self.app
        self.s.pop_menu.load_menus()

        manager._bind_events()  # ?? trigger the actual binding here

    def process_gui_queue(self):
        try:
            while True:
                task = self.s.gui_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        finally:
            self.process_id = self.app.after(100, self.process_gui_queue)

    def post_layout_tasks(self):
        self.shared = self.s  # self.s is already the shared state object

        # ✅ Ensure config_data is present before syncing
        if not hasattr(self.shared, "config_data") or self.shared.config_data is None:
            raise RuntimeError("Shared state is missing config_data. Cannot sync configuration.")

        # ✅ Sync configuration into shared state
        sync_config_to_state(
            self.shared.config_data,
            config_mgr=self.config_mgr,
            shared=self.shared
        )

        # ✅ Perform startup updates
        update_on_start(self.app)

        # Optional: open debug dashboards automatically when testing
        try:
            if os.environ.get("OPEN_DEBUG_DASHES", "0") == "1":
                from actions.tb_debug.menu_dashboard import launch_menu_dashboard
                from actions.tools.debug_dashboard import open_debug_dashboard
                from actions.tools.popup_preview import PopupPreviewTool

                # schedule shortly after startup so all bindings exist
                self.app.after(300, lambda: launch_menu_dashboard(master=self.app))
                self.app.after(500, lambda: open_debug_dashboard(self.app, self.s, getattr(self.s, 'binding_manager', None)))
                # PopupPreviewTool creates its own window; schedule separately
                self.app.after(700, lambda: PopupPreviewTool())
        except Exception as ex:
            print(f"⚠️ Failed to auto-open debug dashboards: {ex}")

        # ✅ Start GUI queue processing loop
        self.app.after(0, self.process_gui_queue)



    def on_close(self, event=None):
        self.app.after_cancel(self.process_id)
        self.app.destroy()
        self.app.quit()


    def launch(self):
        # 1) Import all action modules => runs @menu_tag and registers
        load_all_actions()

        from menus.menu_registry import global_menu_registry
        from menus.popup import MENU_COMPOSITIONS, audit_menu_compositions

        from menus.popup import global_menu_registry  # adjust path if needed

        # Note: previously placeholder menu entries were auto-registered here
        # for groups with no actions. That behavior produced clutter in the
        # debug menus; placeholders are now removed to keep menus clean.

        audit_menu_compositions(MENU_COMPOSITIONS, global_menu_registry, fail_on_error=False)

        self.resolver.auto_register_from(self.app)
        self.setup_shared_state()

        yaml_text = generate_yaml_from_registry()
        write_yaml_to_settings(yaml_text)

        self.build_layout(self.s.config_data)

        self.app.protocol("WM_DELETE_WINDOW", self.on_close)
        self.app.after(0, self.bind_events)
        self.app.after(200, self.post_layout_tasks)
        self.app.mainloop()


if __name__ == "__main__":
    launcher = AppLauncher()
    launcher.launch()
