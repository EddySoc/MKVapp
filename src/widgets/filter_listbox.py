#-------------------------------------------------------------------------------
# Name:        filter_listbox.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import os
import tkinter as tk
import customtkinter as ct
from CTkListbox import CTkListbox
from shared_data import get_shared


class FilterListBox(ct.CTkFrame):
    def __init__(self, master=None, items=None, shared_data=None, popup_menu=None, **kwargs):
        super().__init__(master, **kwargs)

        self._on_ready_callback = None  # ✅ Callback placeholder

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.items = items or []
        self.current_items = self.items.copy()
        self.s = get_shared()
        self.popup_menu = popup_menu

        self.s.all_filterboxes.append(self)

        self._build_widgets()

    def set_ready_callback(self, callback):
        """Register a callback to be called when the widget is fully initialized."""
        self._on_ready_callback = callback

    def _build_widgets(self):
        self.configure(fg_color="black", bg_color="white")

        outer = ct.CTkFrame(self, border_width=2, border_color="cyan")
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        self.entry = ct.CTkEntry(outer)
        self.entry.grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        self.entry.bind("<KeyRelease>", lambda event: self.filter_listbox())
        self.entry.bind("<FocusIn>", lambda e: self._update_focus_styles(self.entry))
        self.entry.bind("<FocusOut>", lambda e: self._update_focus_styles(None))

        self.listbox = CTkListbox(outer, multiple_selection=True, fg_color="black", text_color="white")
        self.listbox.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
        self.listbox.bind("<FocusIn>", lambda e: self._update_focus_styles(self.listbox))
        self.listbox.bind("<FocusOut>", lambda e: self._update_focus_styles(None))

        self._patch_listbox_delete_all()

        self.initialized = True  # ✅ Widget is now ready

        # Setup popup bindings after widget is fully initialized
        self.after(100, self._setup_popup_bindings)

        if self._on_ready_callback:
            self._on_ready_callback()
            self._on_ready_callback = None  # Optional: clear after use

    def _setup_popup_bindings(self):
        """Setup right-click bindings for popup menu on frame and listbox"""
        from utils.debug_logger import debug_print
        
        def on_right_click(event):
            from shared_data import get_shared
            s = get_shared()
            if hasattr(s, 'pop_menu') and s.pop_menu:
                # Check if click was on an item or in empty space
                try:
                    # Try to get the index at the click position
                    clicked_index = event.widget.nearest(event.y)
                    
                    # Check if there's actually an item at that position
                    item_count = self.listbox.size()
                    if clicked_index < item_count:
                        # Click was on an actual item - select it
                        current_selection = list(self.listbox.curselection())
                        
                        # WORKAROUND: If index 0 is selected, deselect and reselect to reset state
                        if current_selection and 0 in current_selection:
                            # Index 0 is selected - reset it
                            self.listbox.selection_clear(0, 'end')
                            self.listbox.update()
                            self.listbox.selection_set(0)
                            self.listbox.activate(0)
                            self.listbox.update()
                    else:
                        # Click was in empty space - menu will still open but no selection
                        pass
                except:
                    # If we can't determine click position, continue anyway
                    pass
                
                # ALWAYS pass self (FilterListBox with custom_name="lb_files")
                # regardless of where the click happened (label or empty space)
                debug_print(f"🖱️ Right-click on lb_files - passing self with custom_name: lb_files", "binding")
                s.pop_menu.show_popup(self, event)
                return "break"  # Prevent event propagation to avoid duplicate popups
        
        debug_print(f"🔧 Setting up popup bindings for lb_files (custom_name: {getattr(self, 'custom_name', 'NONE')})", "binding")
        
        # Bind to all child widgets recursively
        def bind_to_all(widget):
            try:
                # Unbind any existing Button-3 bindings first to avoid conflicts
                widget.unbind("<Button-3>")
                # Bind our handler
                widget.bind("<Button-3>", on_right_click)
                # Recurse to children
                for child in widget.winfo_children():
                    bind_to_all(child)
            except Exception as e:
                debug_print(f"⚠️ Could not bind to {widget}: {e}", "binding")
        
        # Start binding from self
        bind_to_all(self)

    def _patch_listbox_delete_all(self):
        original_delete = self.listbox.delete

        def patched_delete(index, *args):
            if index == "all":
                # Safely destroy all buttons and clear references
                for key in list(self.listbox.buttons.keys()):
                    try:
                        btn = self.listbox.buttons[key]
                        # Clear command before destroying
                        if btn.winfo_exists():
                            btn.configure(command=lambda: None)
                            btn.destroy()
                    except Exception:
                        pass  # Button already destroyed
                self.listbox.buttons.clear()
            else:
                original_delete(index, *args)

        self.listbox.delete = patched_delete

    def set_items(self, full_paths):
        self.items = full_paths
        self.current_items = list(full_paths)
        self.update_listbox(full_paths)

    def update_listbox(self, items, color=None):
        if not getattr(self, "initialized", False):
            print("⚠️ FilterListBox not ready — skipping update")
            return

        # ✅ Clear selection first to prevent errors with destroyed widgets
        try:
            # Get all currently selected indices
            selected_indices = list(self.listbox.curselection())
            # Deselect them in reverse order to avoid index shifting issues
            for idx in reversed(selected_indices):
                try:
                    self.listbox.deactivate(idx)
                except:
                    pass
        except:
            pass

        self.listbox.delete("all")
        self.current_items = list(items)  # Store full paths

        # Clear button references
        if hasattr(self.listbox, "buttons"):
            self.listbox.buttons.clear()

        for i, full_path in enumerate(items):
            filename = os.path.basename(full_path)
            assigned_color = color or self._resolve_color(full_path)

            try:
                self.listbox.insert(i, filename)
                #print(f"✅ Inserted item {i}: {filename}")
            except Exception as e:
                print(f"⚠️ Failed to insert item {i}: {e}")
                continue

            # Safely configure button if it exists
            try:
                btn = self.listbox.buttons.get(i)
                if btn and str(btn) in btn.tk.call('winfo', 'children', str(btn.master)):
                    btn.configure(text_color=assigned_color)
                else:
                    print(f"⚠️ Skipped dead or missing button for '{filename}'")
            except Exception as e:
                print(f"⚠️ Couldn't apply color to item '{filename}': {e}")

    def _create_button_for(self, filename):
        from customtkinter import CTkButton
        return CTkButton(master=self.listbox, text=filename)

    def _resolve_color(self, path):
        video_exts = {".mp4", ".avi", ".mov", ".mkv", ".flv"}
        subtitle_exts = {".srt", ".sub", ".vtt"}
        ext = os.path.splitext(path)[-1].lower()

        if ext in video_exts:
            return "cyan"
        elif ext in subtitle_exts:
            return "yellow"
        else:
            return "white"

    def filter_listbox(self):
        search = self.entry.get().lower()
        filtered = [p for p in self.items if search in os.path.basename(p).lower()]
        self.current_items = filtered
        self.update_listbox(filtered)

    def get_selected_file_paths(self):
        return [
            self.current_items[i]
            for i in self.listbox.curselection()
            if i < len(self.current_items)
        ]

    def deselect_item_by_index(self, index):
        try:
            self.listbox.deactivate(index)
        except Exception as e:
            print(f"⚠️ Could not deselect index {index}: {e}")

    def apply_shared_font(self):
        if not hasattr(self, "listbox"):
            print("⚠️ apply_shared_font called too early — skipping")
            return
        if self.s and self.s.CTK_FONT:
            self.entry.configure(font=self.s.CTK_FONT)
            self.listbox.configure(font=self.s.CTK_FONT)

    def _update_focus_styles(self, focused_widget=None):
        entry_default = {"fg_color": "white", "border_color": "grey"}
        entry_highlight = {"fg_color": "#e0f7ff", "border_color": "#00aaff"}
        listbox_default = {"border_color": "grey"}
        listbox_highlight = {"border_color": "#00aaff"}

        self.entry.configure(**entry_default)
        self.listbox.configure(**listbox_default)

        if focused_widget == self.entry:
            self.entry.configure(**entry_highlight)
        elif focused_widget == self.listbox:
            self.listbox.configure(**listbox_highlight)
        entry_default = {"fg_color": "white", "border_color": "grey"}
        entry_highlight = {"fg_color": "#e0f7ff", "border_color": "#00aaff"}
        listbox_default = {"border_color": "grey"}
        listbox_highlight = {"border_color": "#00aaff"}

        self.entry.configure(**entry_default)
        self.listbox.configure(**listbox_default)

        if focused_widget == self.entry:
            self.entry.configure(**entry_highlight)
        elif focused_widget == self.listbox:
            self.listbox.configure(**listbox_highlight)

    def insert(self, index, item):
        self.listbox.insert(index, item)

    def delete(self, index):
        self.listbox.delete(index)

    def curselection(self):
        return self.listbox.curselection()

    def on_ready():
        print("✅ FilterListBox is ready — updating listbox")

