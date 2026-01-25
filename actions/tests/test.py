#-------------------------------------------------------------------------------
# Name:        actions_logs.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# logs.py

import os
import sys
import json
from decorators.decorators import menu_tag
from shared_data import get_shared as _get_shared

# Prevent menu_tag and get_shared from appearing in debug dropdown
# by prefixing _get_shared with underscore
get_shared = _get_shared

@menu_tag(label="DiskInfo",icon="🔍",group=["tb_info"])
def diskinfo():
    """Print disk info to tb_info textbox"""
    import shutil
    from shared_data import shared
    from utils.text_helpers import tb_update
    
    s = get_shared()
    config = shared.config
    disk = "c:"
    min_free = int(config["persistent_cfg"].get("Min_Freespace", 5))
    total, used, free = shutil.disk_usage(disk)
    
    gb_total = total // (2**30)
    gb_used = used // (2**30)
    gb_free = free // (2**30)

    tag = "rood" if gb_free < min_free else "groen"
    
    # Print detailed info to textbox
    tb_update('tb_info', f"━━━━━ Disk Information ━━━━━", "normal")
    tb_update('tb_info', f"Drive: {disk.upper()}", "normal")
    tb_update('tb_info', f"Total: {gb_total} GB", "normal")
    tb_update('tb_info', f"Used:  {gb_used} GB", "normal")
    tb_update('tb_info', f"Free:  {gb_free} GB", tag)
    tb_update('tb_info', f"Min Required: {min_free} GB", "normal")
    if gb_free < min_free:
        tb_update('tb_info', f"⚠️ WARNING: Low disk space!", "rood")
    tb_update('tb_info', "", "normal")

@menu_tag(label="Disk InfoBar",icon="🔍",group=["tb_info"])
def show_disk_info():
    """Show disk info in the bottom status bar"""
    import shutil
    from shared_data import shared
    
    s = get_shared()
    config = shared.config
    disk = "c:"
    min_free = int(config["persistent_cfg"].get("Min_Freespace", 5))
    total, used, free = shutil.disk_usage(disk)
    gb_free = free // (2**30)

    tag = "warning" if gb_free < min_free else "groen"
    msg = f"{'⚠️' if tag == 'warning' else '🟢'} Disk {disk} — Free: {gb_free} GB"

    try:
        s.bottomrow_label.show_tagged_message(msg, tag)
    except Exception as e:
        print(f"⚠️ Failed to update bottomrow label: {e}")

def inspect_all_menus():
    """Show all registered menu items with their properties"""
    from menus.menu_registry import global_menu_registry
    
    registry = global_menu_registry
    all_actions = registry.all()  # label → entry dict
    grouped = registry.grouped()  # group → [label, label, ...]
    
    output = []
    output.append("=" * 60)
    output.append("📋 MENU REGISTRY INSPECTION")
    output.append("=" * 60)
    output.append(f"\nTotal registered actions: {len(all_actions)}")
    output.append(f"Total groups: {len(grouped)}")
    output.append(f"\nGroups: {', '.join(sorted(grouped.keys()))}")
    output.append("\n" + "=" * 60)
    
    for group_name in sorted(grouped.keys()):
        labels = grouped[group_name]  # This is a list of label strings
        output.append(f"\n📁 Group: {group_name} ({len(labels)} items)")
        output.append("-" * 60)
        
        for label in labels:
            entry = all_actions.get(label)
            if not entry:
                continue
                
            output.append(f"\n  🏷️  Label: {label}")
            output.append(f"  🎯  Tag: {entry.get('tag', 'N/A')}")
            output.append(f"  🎨  Icon: {entry.get('icon') or '(none)'}")
            output.append(f"  📦  Function: {entry['func'].__name__ if entry.get('func') else 'N/A'}")
            
            func = entry.get('func')
            if func and hasattr(func, '__doc__') and func.__doc__:
                doc = func.__doc__.strip().split('\n')[0][:60]
                output.append(f"  📝  Doc: {doc}")
    
    output.append("\n" + "=" * 60)
    return "\n".join(output)

def find_menu_items(search_term):
    """Search for menu items by label, tag, or group
    
    Args:
        search_term: Text to search for (case-insensitive)
    """
    from menus.menu_registry import global_menu_registry
    
    registry = global_menu_registry
    all_actions = registry.all()  # label → entry dict
    grouped = registry.grouped()  # group → [label, ...]
    search_lower = search_term.lower()
    
    matches = []
    for label, entry in all_actions.items():
        # Search in label, tag, and check if label appears in any group
        match_groups = [g for g, labels in grouped.items() if label in labels and search_lower in g.lower()]
        
        if (search_lower in label.lower() or 
            search_lower in entry.get('tag', '').lower() or
            match_groups):
            matches.append((label, entry, match_groups))
    
    output = []
    output.append(f"🔍 Search results for: '{search_term}'")
    output.append(f"Found {len(matches)} match(es)\n")
    output.append("=" * 60)
    
    for label, entry, match_groups in matches:
        icon = entry.get('icon', '')
        output.append(f"\n🏷️  {label} {icon}")
        output.append(f"   Tag: {entry.get('tag', 'N/A')}")
        
        # Show all groups this item appears in
        all_groups = [g for g, labels in grouped.items() if label in labels]
        output.append(f"   Groups: {', '.join(all_groups)}")
        
        func = entry.get('func')
        if func and hasattr(func, '__doc__') and func.__doc__:
            doc = func.__doc__.strip().split('\n')[0][:80]
            output.append(f"   Doc: {doc}")
    
    output.append("\n" + "=" * 60)
    return "\n".join(output)
