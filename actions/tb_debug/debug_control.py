#-------------------------------------------------------------------------------
# Name:        debug_actions.py
# Purpose:     Actions for controlling debug output
#
# Author:      EddyS
#
# Created:     11/01/2026
# Copyright:   (c) EddyS 2026
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from decorators.decorators import menu_tag

# Removed from menu - available in left panel
def toggle_debug():
    """Toggle debug output on/off"""
    from shared_data import get_shared
    from utils.debug_logger import set_debug_mode, debug_print
    
    s = get_shared()
    config = s.config if hasattr(s, 'config') else {}
    debug_settings = config.get("debug_cfg", {"enabled": True})
    
    # Toggle enabled state
    new_state = not debug_settings.get("enabled", True)
    set_debug_mode(enabled=new_state)
    
    status = "enabled" if new_state else "disabled"
    print(f"🐛 Debug output {status}")

# Removed from menu - available in left panel
def debug_to_console():
    """Send debug output to console"""
    from utils.debug_logger import set_debug_mode
    set_debug_mode(enabled=True, output="console")
    print("💻 Debug output → Console")

# Removed from menu - available in left panel
def debug_to_textbox():
    """Send debug output to debug textbox"""
    from utils.debug_logger import set_debug_mode
    set_debug_mode(enabled=True, output="textbox")
    print("📝 Debug output → TextBox")

# Removed from menu - available in left panel
def debug_to_both():
    """Send debug output to both console and textbox"""
    from utils.debug_logger import set_debug_mode
    set_debug_mode(enabled=True, output="both")
    print("🔀 Debug output → Both")

# Removed from menu - duplicate of "Clear Textbox"
def clear_debug_textbox():
    """Clear the debug textbox"""
    from shared_data import get_shared
    s = get_shared()
    
    if hasattr(s, 'app') and hasattr(s.app, 'tb_debug'):
        s.app.tb_debug.clear_textbox()
        print("🧹 Debug textbox cleared")
