#-------------------------------------------------------------------------------
# Name:        smart_entry.py
# Purpose:
#
# Author:      EddyS
#
# Created:     02/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from customtkinter import CTkEntry

class SmartEntry:
    registry = {}  # ?? Central registry of all named SmartEntry instances

    def __init__(self, widget, name=None, config_mgr=None,fg_color=None, text_color=None):
        self.widget = widget
        self.name = name
        self.custom_name = name or f"entry_{id(self)}"
        self.fg_color = fg_color
        self.text_color = text_color

        self.orig_fg_color = fg_color
        self.orig_text_color = text_color
        self.is_inverted = False
        self.widget_type = type(widget).__name__
        self.var = None  # store bound StringVar (optional)
        self.orig_border_color = widget.cget("border_color") if hasattr(widget, "cget") else "cyan"

        # ?? Automatically register upon creation if name is given
        if self.name:
            SmartEntry.registry[self.name] = self

    def configure(self, **kwargs):
        self.widget.configure(**kwargs)

    def get_widget(self):
        return self.widget

    @property
    def value(self):
        return self.var.get() if self.var else self.widget.get()

    def bind(self, sequence, func, add=None):
        return self.widget.bind(sequence, func, add)

    def focus(self):
        self.widget.focus_set()

    def highlight(self, color="orange"):
        try:
            #print(f"?? Highlighting '{self.custom_name}' with {color}")
            self.widget.configure(border_color=color)
        except Exception as e:
            print(f"?? Could not highlight '{self.custom_name}': {e}")

    def reset_highlight(self):
        try:
            self.widget.configure(border_color=self.orig_fg_color)
        except Exception as e:
            print(f"?? Could not reset highlight for '{self.custom_name}': {e}")

    def invert(self):
        self.widget.configure(
            fg_color=self.text_color,
            text_color=self.fg_color,
            border_width=2  # keep cyan intact
        )
        self.is_inverted = True

    def reset(self):
        try:
            if isinstance(self.widget, CTkEntry):
                #print(f"?? Reset '{self.custom_name}' ({self.widget_type}) to fg={self.orig_fg_color}, text={self.orig_text_color}")
                self.widget.configure(
                    fg_color=self.orig_fg_color,
                    text_color=self.orig_text_color,
                )
            elif self.widget.winfo_class() == "Entry":
                #print(f"?? Reset '{self.custom_name}' (Entry) to bg={self.orig_fg_color}, fg={self.orig_text_color}")
                self.widget.configure(
                    bg=self.orig_fg_color,
                    fg=self.orig_text_color,
                )
            else:
                print(f"?? Unknown widget type during reset: {self.widget}")
                return

            self.is_inverted = False
        except Exception as e:
            print(f"?? Reset failed for '{self.custom_name}': {e}")

    def toggle_inversion(self):
        if self.is_inverted:
            self.reset()
        else:
            self.invert()

    def sync_from_config(self):
        from config.smart_config_manager import get_config_manager
        config = get_config_manager()

        if not self.name:
            print(f"?? Can't sync — entry has no name")
            return

        new_value = config.get("persistent_cfg", self.name, "")
        try:
            # If the entry is bound to a StringVar, this should reflect instantly
            if hasattr(self.widget, "get") and hasattr(self.widget, "delete"):
                # Manually clear & set text if no StringVar is bound
                self.widget.delete(0, "end")
                self.widget.insert(0, new_value)
            #print(f"?? Synced '{self.name}' to: {new_value}")
        except Exception as e:
            print(f"?? Failed to sync '{self.name}': {e}")

    def set_value(self, value):
        # Always update the widget directly for reliability
        self.widget.delete(0, "end")
        self.widget.insert(0, value)
        # Also update var if present
        if self.var:
            self.var.set(value)
        # Ensure UI updates
        if hasattr(self.widget, 'update_idletasks'):
            self.widget.update_idletasks()

    def force_redraw(self):
        """Force visual sync from StringVar."""
        if self.var and self.widget:
            try:
                new_text = self.var.get()
                self.widget.configure(textvariable=self.var)  # ?? Rebind if needed
                self.widget.delete(0, "end")
                self.widget.insert(0, new_text)
                self.widget.update_idletasks()
                print(f"?? SmartEntry.force_redraw applied ? {self.name} = {new_text}")
            except Exception as e:
                print(f"?? Failed to force redraw on {self.name}: {e}")

    @classmethod
    def register(cls, name, smart_entry):
        cls.registry[name] = smart_entry

    @classmethod
    def get(cls, name):
        return cls.registry.get(name)

    @classmethod
    def reset_all(cls):
        for name, entry in cls.registry.items():
            print(f"?? Resetting '{name}'...")
            entry.reset()

    @classmethod
    def sync_all(cls):
        for name, smart in cls.registry.items():
            smart.sync_from_config()
