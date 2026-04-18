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
# project_root/actions/init_loader.py

import os
import sys
import pkgutil
import importlib
import inspect
from pathlib import Path

# Core popup actions that must always be available in frozen builds.
CRITICAL_ACTION_MODULES = [
    "actions.lbox.common",   # Select All / Deselect All / Delete Files / Reveal Files
    "actions.tbox.common",   # Clear Textbox
    "actions.help.help",     # Show Help
]

def get_menu_group(filepath, base_path):
    """
    Resolves the menu group from a file path relative to the base actions folder.
    Example: actions/LBox/common/common.py → LBox/common
    """
    try:
        rel_path = Path(filepath).relative_to(base_path)
        folder = rel_path.parent
        return str(folder).replace("\\", "/")
    except Exception as e:
        print(f"⚠️ Failed to resolve group for {filepath}: {e}")
        return "default"

def load_all_actions():
    # Prevent multiple executions
    if hasattr(load_all_actions, '_executed'):
        return global_menu_registry.all()
    load_all_actions._executed = True

    from menus.menu_registry import global_menu_registry
    base_package = "actions"
    # Go up one level from menus/ to project_root/, then into actions/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    base_path = os.path.join(project_root, "actions")

    try:
        actions_pkg = importlib.import_module(base_package)
        scan_paths = list(getattr(actions_pkg, "__path__", [])) or [base_path]
    except Exception:
        scan_paths = [base_path]

    seen_modules = set()
    seen_files = set()

    module_function_map = {}

    # Ensure critical action modules are imported first.
    # This also helps PyInstaller pick them up via static import analysis.
    for mod_name in CRITICAL_ACTION_MODULES:
        try:
            importlib.import_module(mod_name)
        except Exception as ex:
            print(f"⚠️ Failed to import critical action module {mod_name}: {ex}")


    def import_submodules_recursively(module_name, module_path):
        """Recursively import all submodules in a package."""
        for finder, sub_name, is_subpkg in pkgutil.iter_modules([module_path], prefix=module_name + "."):
            try:
                importlib.import_module(sub_name)
                sub_spec = importlib.util.find_spec(sub_name)
                if is_subpkg and sub_spec and sub_spec.submodule_search_locations:
                    import_submodules_recursively(sub_name, sub_spec.submodule_search_locations[0])
            except Exception as ex:
                if isinstance(ex, ModuleNotFoundError):
                    missing_name = str(ex)
                    if "torch" in missing_name or "pyperclip" in missing_name:
                        continue
                if getattr(sys, 'frozen', False) and isinstance(ex, FileNotFoundError):
                    continue
                print(f"⚠️ Failed to import submodule {sub_name}: {ex}")

    for finder, name, ispkg in pkgutil.walk_packages(scan_paths, prefix=f"{base_package}."):
        if name in seen_modules:
            continue

        try:
            spec = importlib.util.find_spec(name)
            if not spec or not spec.origin or spec.origin in seen_files:
                continue

            # Skip __init__.py-only modules with no other .py files (filesystem only)
            if spec.origin.endswith("__init__.py"):
                folder = os.path.dirname(spec.origin)
                if os.path.isdir(folder):
                    py_files = [f for f in os.listdir(folder) if f.endswith(".py") and f != "__init__.py"]
                    if not py_files:
                        continue

            seen_modules.add(name)
            seen_files.add(spec.origin)

            group = get_menu_group(spec.origin, base_path)
            if not group:
                continue

            if name in sys.modules:
                module = sys.modules[name]
            else:
                module = importlib.import_module(name)

            # Recursief importeren van submodules als het een package is
            if ispkg and hasattr(spec, 'submodule_search_locations') and spec.submodule_search_locations:
                import_submodules_recursively(name, spec.submodule_search_locations[0])

            # 🧠 Respect __skip_menu_scan__ flag
            if getattr(module, "__skip_menu_scan__", False):
                continue

            tagged_funcs = []
            for _, func in inspect.getmembers(module, inspect.isfunction):
                if hasattr(func, "_menu_tags"):
                    tagged_funcs.append(func.__name__)
                    # Check if function already has _menu_meta from decorator
                    if hasattr(func, "_menu_meta"):
                        meta = func._menu_meta
                        for g in meta.get("groups", [group]):
                            if g not in module_function_map:
                                module_function_map[g] = []
                            module_function_map[g].append(func.__name__)
                        continue
                    tags = getattr(func, "_menu_tags", [])
                    symbol = getattr(func, "_menu_symbol", "")
                    for tag in tags:
                        label = f"{symbol} {tag}".strip()
                        global_menu_registry.register(
                            label=label,
                            func=func,
                            tag=tag,
                            group=group
                        )
            if tagged_funcs:
                if group not in module_function_map:
                    module_function_map[group] = []
                module_function_map[group].extend(tagged_funcs)
        except Exception as ex:
            if getattr(sys, 'frozen', False) and isinstance(ex, FileNotFoundError):
                continue
            if isinstance(ex, ModuleNotFoundError) and "torch" in str(ex):
                continue
            print(f"⚠️ Failed to import {name}: {ex}")

    # Summary
    # Write to log file instead of console - DISABLED
    # with open("startup_debug.log", "a", encoding="utf-8") as log_file:
    #     log_file.write("\n📦 Modules with registered actions:\n")
    #     for group, funcs in module_function_map.items():
    #         log_file.write(f" - {group}/\n")
    #         for func in funcs:
    #             log_file.write(f"    • {func}\n")

    from utils.debug_logger import debug_print
    debug_print("\n✅ Dynamic action registry populated:", "general")
    debug_print(f" - Total actions: {len(global_menu_registry.all())}", "general")
    debug_print(f" - Menu groups: {len(global_menu_registry.grouped())}\n", "general")

    #global_menu_registry.summary(view="tree")
    return global_menu_registry.all()