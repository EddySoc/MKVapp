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
    from menus.menu_registry import global_menu_registry
    base_package = "actions"
    # Fix: Go up one level from menus/ to project_root/, then into actions/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    base_path = os.path.join(project_root, "actions")
    seen_modules = set()
    seen_files = set()

    print(f"🚀 Scanning actions package for tagged menu functions...")
    print(f"📂 Base path: {base_path}\n")

    module_function_map = {}


    def import_submodules_recursively(module_name, module_path):
        """Recursively import all submodules in a package."""
        for finder, sub_name, is_subpkg in pkgutil.iter_modules([module_path], prefix=module_name + "."):
            try:
                importlib.import_module(sub_name)
                sub_spec = importlib.util.find_spec(sub_name)
                if is_subpkg and sub_spec and sub_spec.submodule_search_locations:
                    import_submodules_recursively(sub_name, sub_spec.submodule_search_locations[0])
            except Exception as ex:
                print(f"⚠️ Failed to import submodule {sub_name}: {ex}")

    for finder, name, ispkg in pkgutil.walk_packages([base_path], prefix=f"{base_package}."):
        if name in seen_modules:
            continue

        try:
            spec = importlib.util.find_spec(name)
            if not spec or not spec.origin or spec.origin in seen_files:
                continue

            # 🧠 Skip __init__.py-only modules with no other .py files
            if spec.origin.endswith("__init__.py"):
                folder = os.path.dirname(spec.origin)
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
            print(f"⚠️ Failed to import {name}: {ex}")

    # Summary
    print("\n📦 Modules with registered actions:")
    for group, funcs in module_function_map.items():
        print(f" - {group}/")
        for func in funcs:
            print(f"    • {func}")

    print("\n✅ Dynamic action registry populated:")
    print(f" - Total actions: {len(global_menu_registry.all())}")
    print(f" - Menu groups: {len(global_menu_registry.grouped())}\n")

    #global_menu_registry.summary(view="tree")
    return global_menu_registry.all()