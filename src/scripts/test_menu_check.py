#!/usr/bin/env python
"""Quick check to see if videos group is registered

Moved to scripts/ — adjust sys.path to include project root.
"""

# Direct import to avoid circular dependencies
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import only what we need
from menus.menu_registry import MenuRegistry

registry = MenuRegistry()

print("=" * 60)
print("CHECKING MENU REGISTRY")
print("=" * 60)

# Try to load actions
try:
    from actions import lb_files
    print("✅ Successfully imported actions.lb_files")
except Exception as e:
    print(f"❌ Failed to import actions.lb_files: {e}")

print(f"\nTotal actions registered: {len(registry.all())}")
print(f"Total groups: {len(registry.grouped())}")
print(f"\nAll groups: {list(registry.grouped().keys())}")

if 'videos' in registry.grouped():
    print(f"\n✅ 'videos' group FOUND with {len(registry.grouped()['videos'])} actions:")
    for action in registry.grouped()['videos']:
        print(f"   - {action}")
else:
    print("\n❌ 'videos' group NOT FOUND")
    print("\n🔍 Searching for 'Remove All Subs' in other groups:")
    for group, actions in registry.grouped().items():
        if any('Remove' in str(a) or 'Subs' in str(a) for a in actions):
            print(f"   Found in group '{group}': {actions}")
