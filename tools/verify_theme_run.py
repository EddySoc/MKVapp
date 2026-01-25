import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import customtkinter as ct
import tkinter as tk
from shared_data import get_shared

# Create CTk root
root = ct.CTk()
root.title("Theme Verify Root")
root.geometry("200x100")

s = get_shared()
s.app = root
s.init_fonts()

# Import and create MenuDashboard
from actions.tb_debug.menu_dashboard import MenuDashboard
md = MenuDashboard(master=root)

# Import debug dashboard opener
from actions.tools.debug_dashboard import open_debug_dashboard

# Ensure binding_manager is available (may be None)
open_debug_dashboard(root, s, s.binding_manager)

# Collect widget configs
results = {}
try:
    results['menu_items_tb'] = (md.items_tb.cget('bg'), md.items_tb.cget('fg'))
except Exception as e:
    results['menu_items_tb'] = f'error: {e}'

# Find the dash window's text widget by scanning root's toplevels
for w in root.winfo_children():
    pass

# Try to find any Toplevel with a Text widget to inspect (bindings dashboard)
for top in root.winfo_toplevel().winfo_children():
    # look for Toplevels (CTkToplevel may be instance of tk.Toplevel)
    try:
        clsname = type(top).__name__
        if hasattr(top, 'winfo_children'):
            for child in top.winfo_children():
                if isinstance(child, tk.Text):
                    results['found_text_in_top_'+clsname] = (child.cget('bg'), child.cget('fg'))
    except Exception:
        pass

print('THEME_VERIFY_RESULTS:', results)

# Destroy windows after short delay
root.after(500, root.destroy)
root.mainloop()
