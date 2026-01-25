#-------------------------------------------------------------------------------
# Name:        debug_logger.py
# Purpose:     Configurable debug logging system
#
# Author:      EddyS
#
# Created:     11/01/2026
# Copyright:   (c) EddyS 2026
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def debug_print(message, category="general"):
    """
    Print debug messages based on configuration settings.
    
    Args:
        message: The debug message to print
        category: Category of the debug message (general, menu, binding, etc.)
    """
    from shared_data import get_shared
    
    try:
        s = get_shared()
        config = s.config if hasattr(s, 'config') else {}
        
        # Get debug settings from config (default to console output, enabled)
        debug_settings = config.get("debug_cfg", {
            "enabled": True,
            "output": "console",  # "console", "textbox", or "both"
            "categories": {
                "general": True,
                "menu": True,
                "binding": True,
                "scan": True,
                "popup": True
            }
        })
        
        # Check if debug is enabled
        if not debug_settings.get("enabled", True):
            return
        
        # Check if this category is enabled
        categories = debug_settings.get("categories", {})
        if not categories.get(category, True):
            return
        
        output_mode = debug_settings.get("output", "console")
        
        # Output to console
        if output_mode in ["console", "both"]:
            print(message)
        
        # Output to debug textbox
        if output_mode in ["textbox", "both"]:
            try:
                from widgets.base_textbox import BaseTBox
                # Ensure tb_debug instance exists
                s = get_shared()
                if not hasattr(s, 'app') or not hasattr(s.app, 'tb_debug'):
                    # Try to create tb_debug if missing
                    import tkinter as tk
                    s.app = getattr(s, 'app', None) or tk.Tk()
                    s.app.tb_debug = BaseTBox(s.app, name="tb_debug")
                BaseTBox.update_text('tb_debug', message + "\n", tags="debug")
            except Exception as e:
                # Fallback to console if textbox fails
                print(f"⚠️ Debug textbox output failed: {e}")
                print(message)
                
    except Exception as e:
        # Fallback to regular print if something goes wrong
        print(f"⚠️ Debug system error: {e}")
        print(message)


def set_debug_mode(enabled=True, output="console", categories=None):
    """
    Configure debug settings.
    
    Args:
        enabled: Enable/disable debug output
        output: "console", "textbox", or "both"
        categories: Dict of category enabled states
    """
    from shared_data import get_shared
    
    try:
        s = get_shared()
        
        if not hasattr(s, 'config'):
            s.config = {}
        
        if "debug_cfg" not in s.config:
            s.config["debug_cfg"] = {}
        
        s.config["debug_cfg"]["enabled"] = enabled
        s.config["debug_cfg"]["output"] = output
        
        if categories:
            s.config["debug_cfg"]["categories"] = categories
        
        debug_print(f"✅ Debug mode configured: enabled={enabled}, output={output}", "general")
        
    except Exception as e:
        print(f"⚠️ Failed to set debug mode: {e}")
