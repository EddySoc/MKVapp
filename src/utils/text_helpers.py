#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     01/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def update_tb(tb_name, msg, tag="normal"):
    """
    Generic function to update any textbox.
    
    Args:
        tb_name: Name of the textbox (e.g., 'tb_debug', 'tb_info', 'tb_folders')
        msg: Message to insert
        tag: Tag name for styling (default: 'normal')
    
    Examples:
        update_tb('tb_info', 'Hello', 'groen')
        update_tb('tb_debug', 'Error!', 'rood')
    """
    from shared_data import get_shared
    s = get_shared()
    
    if not hasattr(s, 'app') or s.app is None:
        print(f"⚠️ App not initialized yet: {msg}")
        return
    
    if not hasattr(s.app, tb_name):
        print(f"⚠️ {tb_name} not available on app: {msg}")
        return
    
    try:
        tb = getattr(s.app, tb_name)
        tb.textbox.configure(state="normal")
        tb.textbox.insert("end", msg + "\n", tag)
        tb.textbox.see("end")
        tb.textbox.configure(state="disabled")
    except Exception as e:
        print(f"❌ Failed to update {tb_name}: {e} - Message was: {msg}")

def clear_tb(tb_name):
    """
    Generic function to clear any textbox.
    
    Args:
        tb_name: Name of the textbox (e.g., 'tb_debug', 'tb_info', 'tb_folders')
    """
    from shared_data import get_shared
    s = get_shared()
    
    if not hasattr(s.app, tb_name):
        print(f"⚠️ {tb_name} not available")
        return
    
    try:
        tb = getattr(s.app, tb_name)
        tb.textbox.configure(state="normal")
        tb.textbox.delete("1.0", "end")
        tb.textbox.configure(state="disabled")
        print(f"✅ Cleared {tb_name}")
    except Exception as e:
        print(f"❌ Failed to clear {tb_name}: {e}")

def tb_update(tb_widget_or_name, msg, tag="normal"):
    """
    Generic function to update any textbox - flexible parameter handling.
    
    Args:
        tb_widget_or_name: Either a textbox widget object OR a string name (e.g., 'tb_info', 'tb_debug')
        msg: Message to insert
        tag: Tag name for styling (default: 'normal')
    
    Examples:
        tb_update(tb_info, "Processing...", "normal")
        tb_update('tb_debug', "Done!", "groen")
    """
    from shared_data import get_shared
    s = get_shared()
    
    # If it's a string, treat it as a textbox name
    if isinstance(tb_widget_or_name, str):
        if not hasattr(s.app, tb_widget_or_name):
            print(f"⚠️ {tb_widget_or_name} not available: {msg}")
            return
        tb = getattr(s.app, tb_widget_or_name)
    else:
        # It's a widget object
        tb = tb_widget_or_name
    
    # Ensure the widget has a textbox attribute
    if not hasattr(tb, 'textbox'):
        print(f"⚠️ Widget doesn't have a textbox: {msg}")
        return
    
    try:
        tb.textbox.configure(state="normal")
        tb.textbox.insert("end", msg + "\n", tag)
        tb.textbox.see("end")
        tb.textbox.configure(state="disabled")
    except Exception as e:
        print(f"⚠️ Failed to update textbox: {e} - {msg}")

# Convenience functions for backward compatibility
def update_tbdebug(msg, tag="normal"):
    """Update tb_debug textbox with a message"""
    update_tb('tb_debug', msg, tag)

def update_tbinfo(msg, tag="normal"):
    """Update tb_info textbox with a message"""
    update_tb('tb_info', msg, tag)

def update_tbsettings(msg, tag="normal"):
    """Update tb_settings textbox with a message"""
    update_tb('tb_settings', msg, tag)

def log_error(msg, tag="rood", print_also=True):
    """
    Log error/warning message to tb_info and optionally print to console.
    
    Args:
        msg: Error or warning message to display
        tag: Tag name for styling (default: 'rood' for red)
        print_also: Whether to also print to console (default: True)
    
    Examples:
        log_error("⚠️ No files selected.")
        log_error("❌ Failed to process file", tag="rood")
    """
    if print_also:
        print(msg)
    update_tbinfo(msg, tag)

def log_settings(msg, tag="normal", print_also=True):
    """
    Log settings change message to tb_settings and optionally print to console.
    
    Args:
        msg: Settings change message to display
        tag: Tag name for styling (default: 'normal' for white)
        print_also: Whether to also print to console (default: True)
    
    Examples:
        log_settings("✅ Language changed to English")
        log_settings("⚙️ Theme updated", tag="groen")
    """
    if print_also:
        print(msg)
    update_tbsettings(msg, tag)

def clear_tbdebug():
    """Clear tb_debug textbox"""
    clear_tb('tb_debug')

def show_message(self, msg, tag="normal", reset_delay=None):
    self.progress.grid_remove()
    self.label.configure(state="normal")
    current_tag = tag
    for word in msg.split():
        if word.startswith("[") and word.endswith("]") and word[1:-1] in self.tagcfg:
            current_tag = word[1:-1]
            continue
        self.label.insert("end", word + " ", current_tag)
    self.label.insert("end", "\n")
    self.label.see("end")
    self.label.configure(state="disabled")

    if reset_delay is not None:
        self.label.after(reset_delay, self.clear_message)

def clear_message(self):
    self.label.configure(state="normal")
    self.label.delete("1.0", "end")
    self.label.configure(state="disabled")

def show_tagged_message(self, tag, message):
    tags_cfg = config_mgr.get("tags_cfg", {})
    tag_style = tags_cfg.get(tag, {})
    icon = tag_style.get("icon", "")
    color = tag_style.get("text_color", None)

    self.show_message(f"{icon} {message}", color=color)


