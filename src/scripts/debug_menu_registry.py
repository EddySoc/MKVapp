#!/usr/bin/env python3
"""
Debug script to check menu registry in portable executable
"""
import sys
import os

# Ensure project root (src) is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from menus.menu_registry import global_menu_registry
    registry = global_menu_registry

    print("=== MENU REGISTRY DEBUG (PORTABLE) ===")
    print("Available groups:", list(registry.grouped().keys()))
    print()

    print("tbox group items:")
    for item in registry.grouped().get('tbox', []):
        print(f"  - {item}")
    print()

    print("tb_info group items:")
    for item in registry.grouped().get('tb_info', []):
        print(f"  - {item}")
    print()

    print("All entries with 'clear' in label:")
    for label, entry in registry._registry.items():
        if 'clear' in label.lower():
            print(f"  {label}: {entry.get('groups', 'no groups')}")

    print()
    print("Total registry entries:", len(registry._registry))

except Exception as e:
    print(f"Error loading menu registry: {e}")
    import traceback
    traceback.print_exc()
