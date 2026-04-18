#-------------------------------------------------------------------------------
# Name:        app_launcher.py 
# Purpose:     This module serves as the main entry point for the MKV App, responsible for
#
# Author:      EddyS
#
# Created:     08/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sys
import os

# Ultra-early debug logging: vang alles wat misgaat vóór GUI of prints
try:
    with open("startup_debug.log", "a", encoding="utf-8") as f:
        f.write("[START] app_launcher.py boot\n")
        f.write(f"sys.stdout={repr(sys.stdout)} sys.stderr={repr(sys.stderr)}\n")
except Exception as e:
    pass

# In no-console launches (e.g. pythonw/detached), sys.stdout/stderr kunnen None zijn.
try:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8', errors='replace')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w', encoding='utf-8', errors='replace')
except Exception as e:
    with open("startup_debug.log", "a", encoding="utf-8") as f:
        f.write(f"[ERROR] stdout/stderr fallback: {e}\n")

# Force UTF-8 output zodat emoji in print() niet crashen op Windows terminals.
try:
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception as e:
    with open("startup_debug.log", "a", encoding="utf-8") as f:
        f.write(f"[ERROR] reconfigure: {e}\n")
# print("[DEBUG] Python executable:", sys.executable)
# app_launcher.py

import customtkinter as ct
import tkinter as tk
import queue

def _ensure_app_workdir():
    """Use a stable working directory so relative Settings paths always resolve."""
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)

_ensure_app_workdir()




from utils.shared_utils import register_shared
# print("[DEBUG] Python executable:", sys.executable)
from utils.utils import initialize_gui_vars
from mkvapp.lifecycle import update_on_start
from config import sync_config_to_state, smart_config_manager,get_config_manager
from config.smart_config_manager import config_mgr
from menus import Popup
from binding import BindingManager, WidgetNameResolver
from shared_data import get_shared
from customtkinter.windows.widgets.ctk_button import CTkButton
from widgets.smart_entry import SmartEntry
from utils.logger_singleton import logger
from mkvapp import build_layout as ui_build_layout
from menus import menu_registry, write_yaml_to_settings, generate_yaml_from_registry
from menus.menu_registry import global_menu_registry

# Forceer import van actions.lb_files zodat alle menu-items (ook subtitles) worden geregistreerd
import actions.lb_files
from menus.init_loader import load_all_actions

# Write debug info to file - DISABLED
# with open("early_menu_debug.log", "w", encoding="utf-8") as f:
#     f.write("=== EARLY MENU REGISTRY DEBUG ===\n")
#     f.write(f"Available groups: {list(registry.grouped().keys())}\n")
#     f.write(f"tbox group items: {registry.grouped().get('tbox', [])}\n")
#     f.write(f"tb_info group items: {registry.grouped().get('tb_info', [])}\n")
#     f.write("All entries with 'clear' in label:\n")
#     for label, entry in registry._registry.items():
#         if 'clear' in label.lower():
#             f.write(f"  {label}: groups={entry.get('groups', 'no groups')}\n")
#     f.write(f"Total registry entries: {len(registry._registry)}\n")
#     f.write("==================================\n")


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

        # Show full tracebacks for errors in after() callbacks and event bindings
        import traceback as _tb
        def _report_callback_exception(exc, val, tb):
            # Suppress harmless "invalid command name" errors that occur when
            # after() callbacks fire during/after window destruction on close.
            import tkinter as _tk
            if issubclass(exc, _tk.TclError) and "invalid command name" in str(val):
                return
            print("\n🔥 Tkinter callback error:")
            _tb.print_exception(exc, val, tb)
        self.app.report_callback_exception = _report_callback_exception

        # Menu and resolver setup
        self.menus = smart_config_manager.config_mgr.data.get("popmenu_cfg", {}).copy()
        self.widget_name_map = {}

        self.resolver = WidgetNameResolver(
            root_widget=self.app,
            config_data = config_mgr.data,
            scan_mode="all",
            widget_name_map=self.widget_name_map,
        )

        # Only flush stdout if it exists (PyInstaller compatibility)
        if sys.stdout:
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

        # 🗂️ Organize menu entries by their declared group (not tag)
        registry = global_menu_registry
        for label, entry in registry.all().items():
            group = entry.get("group", entry.get("tag", "default"))
            self.s.pop_menu.menus.setdefault(group, []).append(label)

        # Write debug info to file - DISABLED
        # with open("menu_debug.log", "w", encoding="utf-8") as f:
        #     f.write("=== MENU REGISTRY DEBUG (PORTABLE) ===\n")
        #     f.write(f"Available groups: {list(registry.grouped().keys())}\n")
        #     f.write(f"tbox group items: {registry.grouped().get('tbox', [])}\n")
        #     f.write(f"tb_info group items: {registry.grouped().get('tb_info', [])}\n")
        #     f.write("All entries with 'clear' in label:\n")
        #     for label, entry in registry._registry.items():
        #         if 'clear' in label.lower():
        #             f.write(f"  {label}: groups={entry.get('groups', 'no groups')}\n")
        #     f.write(f"Total registry entries: {len(registry._registry)}\n")
        #     f.write("=====================================\n")

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
        try:
            manager = BindingManager(self.app, self.s.pop_menu)
            self.s.binding_manager = manager
            self.s.app = self.app
            self.s.pop_menu.load_menus()
            # Note: BindingManager.__init__ already calls _bind_events() internally.
            # Do NOT call it again here — doubles registration causes stale Tcl commands.
        except Exception as e:
            import traceback
            print(f"💥 bind_events crash: {e}")
            traceback.print_exc()

    def process_gui_queue(self):
        if getattr(self, '_closing', False):
            return
        try:
            while True:
                task = self.s.gui_queue.get_nowait()
                try:
                    task()
                except Exception as e:
                    print(f"💥 GUI queue task error: {e}")
        except queue.Empty:
            pass
        finally:
            try:
                if not getattr(self, '_closing', False) and self.app.winfo_exists():
                    self.process_id = self.app.after(100, self.process_gui_queue)
            except Exception:
                pass

    def post_layout_tasks(self):
        try:
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

                    # schedule shortly after startup so all bindings exist
                    self.app.after(300, lambda: launch_menu_dashboard(master=self.app))
                    self.app.after(500, lambda: open_debug_dashboard(self.app, self.s, getattr(self.s, 'binding_manager', None)))
            except Exception as ex:
                print(f"⚠️ Failed to auto-open debug dashboards: {ex}")

            # ✅ Start GUI queue processing loop
            self.app.after(0, self.process_gui_queue)

        except Exception as e:
            import traceback
            print(f"💥 post_layout_tasks crash: {e}")
            traceback.print_exc()



    def on_close(self, event=None):
        if getattr(self, '_closing', False):
            return
        self._closing = True
        # Cancel every pending after() callback so no lambda fires on a dead window
        try:
            for after_id in self.app.tk.call('after', 'info'):
                try:
                    self.app.after_cancel(after_id)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            # Stop mainloop first, then destroy on idle to avoid Tk deadlocks.
            self.app.quit()
        except Exception:
            pass

        def _destroy_root():
            try:
                if self.app.winfo_exists():
                    self.app.destroy()
            except Exception:
                pass

        try:
            self.app.after_idle(_destroy_root)
            self.app.after(200, _destroy_root)
            # Last-resort guard: if Tk remains hung, force process exit.
            self.app.after(2500, lambda: os._exit(0))
        except Exception:
            _destroy_root()


    def launch(self):
        # 1) Import all action modules => runs @menu_tag and registers
        load_all_actions()
        from menus.menu_registry import global_menu_registry
        print("[DEBUG] Menu groups after load_all_actions:", global_menu_registry.grouped())
        from menus.popup import MENU_COMPOSITIONS, audit_menu_compositions
        # ...existing code...

        self.resolver.auto_register_from(self.app)
        self.setup_shared_state()

        yaml_text = generate_yaml_from_registry()
        write_yaml_to_settings(yaml_text)

        self.build_layout(self.s.config_data)

        self.app.protocol("WM_DELETE_WINDOW", self.on_close)
        self.app.after(0, self.bind_events)
        self.app.after(200, self.post_layout_tasks)
        try:
            self.app.mainloop()
        except KeyboardInterrupt:
            pass  # Ignore Ctrl+C — window close handles cleanup via on_close




if __name__ == "__main__":
    launcher = AppLauncher()
    launcher.launch()


