#!/usr/bin/env python
"""Regenerate menus.yaml from current action files

Moved to scripts/ — ensure project root is on sys.path so imports still work.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load all actions
from menus.init_loader import load_all_actions
from menus.menu_yaml_exporter import generate_yaml_from_registry, write_yaml_to_settings
from menus.menu_registry import global_menu_registry

print("=" * 60)
print("REGENERATING MENUS.YAML")
print("=" * 60)

# Load all actions
load_all_actions()

# Show what's registered
print(f"\nTotal actions registered: {len(global_menu_registry.all())}")
print(f"Total groups: {len(global_menu_registry.grouped())}")
print(f"\nAll groups: {list(global_menu_registry.grouped().keys())}")

# Show tb_info group
if 'tb_info' in global_menu_registry.grouped():
    print(f"\n✅ 'tb_info' group with {len(global_menu_registry.grouped()['tb_info'])} actions:")
    for action in global_menu_registry.grouped()['tb_info']:
        print(f"   - {action}")

# Show All group
if 'All' in global_menu_registry.grouped():
    print(f"\n✅ 'All' group with {len(global_menu_registry.grouped()['All'])} actions:")
    for action in global_menu_registry.grouped()['All']:
        print(f"   - {action}")

# Generate and write YAML
yaml_text = generate_yaml_from_registry()
write_yaml_to_settings(yaml_text)

print("\n" + "=" * 60)
print("✅ MENUS.YAML REGENERATED SUCCESSFULLY")
print("=" * 60)
