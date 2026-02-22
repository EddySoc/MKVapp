#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      EddyS
#
# Created:     05/09/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# project_root/actions/menu_yaml_exporter.py
import yaml
import os
from datetime import datetime
from .menu_registry import global_menu_registry, MenuRegistry

def generate_yaml_from_registry(filter_prefix=None):
    """
    Export the current MenuRegistry to a YAML string.

    - Deduplicates labels within each group
    - Optionally filters groups by a prefix
    - Preserves icon and tooltip metadata
    """
    menus = {}

    # Debug: show all group keys
    # for group in global_menu_registry.grouped().keys():
    #     print(f"Group key: {group} ({type(group)})")

    for group, labels in global_menu_registry.grouped().items():
        # Optional filtering by prefix
        if filter_prefix:
            if not isinstance(group, str):
                print(f"⚠️ Skipping non-string group key: {group} ({type(group)})")
                continue
            if not isinstance(filter_prefix, str):
                print(f"⚠️ Invalid filter_prefix type: {type(filter_prefix)} — skipping filtering")
            elif not group.startswith(filter_prefix):
                continue

        group_items = []
        seen_labels = set()

        for label in labels:
            if label in seen_labels:
                continue  # skip duplicates

            entry = global_menu_registry.get(label)
            if not entry:
                continue

            item = {
                "label": label,
                "action": entry["func"].__name__,
            }
            if "icon" in entry and entry["icon"] is not None:
                item["icon"] = entry["icon"]
            if "tooltip" in entry and entry["tooltip"] is not None:
                item["tooltip"] = entry["tooltip"]

            group_items.append(item)
            seen_labels.add(label)

        menus[group] = group_items

    yaml_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source": "menu_registry",
            "version": "2.0.0"
        },
        "Menus": menus
    }

    return yaml.dump(yaml_data, sort_keys=False, allow_unicode=True)
def write_yaml_to_settings(yaml_text: str):
    settings_dir = os.path.join(os.path.dirname(__file__), "..", "Settings")
    os.makedirs(settings_dir, exist_ok=True)

    yaml_path = os.path.join(settings_dir, "menus.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_text)

    print(f"✅ YAML written to: {yaml_path}")

def load_menus_from_yaml(action_lookup=None, reload=False):
    settings_dir = os.path.join(os.path.dirname(__file__), "..", "Settings")
    yaml_path = os.path.join(settings_dir, "menus.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    registry = MenuRegistry()

    if reload:
        # Clear everything consistently
        registry._registry.clear()
        registry._tag_groups.clear()
        registry._func_labels.clear()
        registry._action_cache.clear()

    # Rebuild registry properly from YAML
    menus_yaml = data.get("Menus", {})
    for group_name, actions in menus_yaml.items():
        for item in actions:
            label = item.get("label")
            func_name = item.get("action")
            icon = item.get("icon")

            func = None
            if action_lookup and func_name:
                # action_lookup should map function_name -> callable
                func = action_lookup.get(func_name)

            if func:
                # tag = function name, label = human label, group = YAML group
                registry.register(
                    func=func,
                    tag=func_name,
                    label=label,
                    icon=icon,
                    group=group_name
                )
            else:
                # No function? still register a disabled placeholder so menus render predictably
                registry.register(
                    func=(lambda: None),
                    tag=func_name or label,
                    label=label or func_name or "Unnamed",
                    icon=icon,
                    group=group_name
                )
    return registry

def parse_yaml_to_registry(menus_yaml, action_lookup):
    registry = {}

    for group_name, actions in menus_yaml.items():
        registry[group_name] = []

        for action in actions:
            func_name = action.get("action")
            entry = {
                "label": action.get("label"),
                "action": func_name,
                "icon": action.get("icon"),
                "func": action_lookup.get(func_name)  # 🔥 Inject actual function
            }
            registry[group_name].append(entry)

    return registry

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export menu registry to YAML.")
    parser.add_argument("--write", action="store_true", help="Write YAML to Settings/menus.yaml")
    parser.add_argument("--print", action="store_true", help="Print YAML to stdout")
    parser.add_argument("--filter", type=str, help="Only include groups starting with this prefix (e.g. TBox)")
    args = parser.parse_args()

    if args.filter:
        print(f"🔍 Filtering groups by prefix: {args.filter}")
        yaml_text = generate_yaml_from_registry(filter_prefix=args.filter)
    else:
        yaml_text = generate_yaml_from_registry()

    if args.print:
        print(yaml_text)

    if args.write:
        write_yaml_to_settings(yaml_text)