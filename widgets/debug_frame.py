#-------------------------------------------------------------------------------
# Name:        config_frame.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import customtkinter as ctk
import actions.tests.test as actions_test
import inspect
import ast
import utils.text_helpers as utils
from shared_data import get_shared

class Debug_Frame(ctk.CTkFrame):
    def __init__(self, master=None):
        super().__init__(master)
        self.lift()
        self.container = ctk.CTkScrollableFrame(self)
        self.container.pack(fill="both", expand=True, padx=5, pady=5)

        self.arg_entries = {}
        self.current_func = None
        self.create_widgets()

    def get_functions(self):
        # Filter out imported utility functions and functions that write to other tabs
        exclude_names = {'menu_tag', 'get_shared', '_get_shared', 'diskinfo', 'show_disk_info'}
        return [(name, obj) for name, obj in inspect.getmembers(actions_test, inspect.isfunction) 
                if name not in exclude_names]

    def parse_arg(self, raw):
        raw = raw.strip()
        if raw.lower() == "true": return True
        if raw.lower() == "false": return False
        if raw == "app": return get_shared().app
        try: return int(raw)
        except: pass
        try: return float(raw)
        except: pass
        app = get_shared().app
        if hasattr(app, raw): return getattr(app, raw)
        try: return ast.literal_eval(raw)
        except: return raw.strip("'").strip('"')

    def update_function_details(self, *_):
        func_name = self.func_dropdown.get()
        func = dict(self.get_functions()).get(func_name)
        self.current_func = func
        if not func:
            print(f"⚠️ Function '{func_name}' not found.")
            return

        sig = inspect.signature(func)
        doc = func.__doc__
        if not isinstance(doc, str) or not doc.strip():
            doc = "No documentation."

        self.sig_label.configure(text=str(sig))
        self.doc_label.configure(text=doc)

        for widget in self.arg_frame.winfo_children():
            widget.destroy()
        self.arg_entries.clear()

        for i, (param_name, param) in enumerate(sig.parameters.items()):
            label_text = f"{param_name}:"
            if param.default == inspect.Parameter.empty:
                label_text += " *"  # Mark required
            lbl = ctk.CTkLabel(self.arg_frame, text=label_text)
            lbl.grid(row=i, column=0, sticky="w", padx=5, pady=2)

            entry = ctk.CTkEntry(self.arg_frame, placeholder_text=param_name, width=240)
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="w")
            entry.bind("<KeyRelease>", lambda e: self.preview_args())
            entry.bind("<Return>", lambda e: self.run_function())
            self.arg_entries[param_name] = entry

            if param.default != inspect.Parameter.empty:
                entry.insert(0, str(param.default))
                entry.configure(text_color="gray")

        self.arg_frame.grid_columnconfigure(1, weight=1)
        self.arg_frame.update_idletasks()
        self.preview_args()

    def preview_args(self):
        preview_lines = []
        for param_name, entry_widget in self.arg_entries.items():
            raw = entry_widget.get().strip()
            parsed = self.parse_arg(raw)
            preview_lines.append(f"{param_name} = {repr(parsed)}")
        self.args_preview.delete("1.0", "end")
        self.args_preview.insert("1.0", "\n".join(preview_lines))

    def reset_args(self):
        if not self.current_func:
            return
        sig = inspect.signature(self.current_func)
        for param_name, entry_widget in self.arg_entries.items():
            param = sig.parameters[param_name]
            entry_widget.delete(0, "end")
            if param.default != inspect.Parameter.empty:
                entry_widget.insert(0, str(param.default))
                entry_widget.configure(text_color="gray")
        self.preview_args()

    def run_function(self):
        func_name = self.func_dropdown.get().strip()
        func = dict(self.get_functions()).get(func_name)
        if not func:
            print(f"⚠️ Function '{func_name}' not found.")
            return

        sig = inspect.signature(func)
        resolved_args = []
        resolved_kwargs = []

        for param_name, entry_widget in self.arg_entries.items():
            raw = entry_widget.get().strip()
            if raw == "":
                continue
            value = self.parse_arg(raw)
            if sig.parameters[param_name].default == inspect.Parameter.empty:
                resolved_args.append(value)
            else:
                resolved_kwargs.append((param_name, value))

        debug_lines = [f"🛠️ Ran: {func_name}"]
        debug_lines.append("🔍 Parsed Arguments:")
        for i, v in enumerate(resolved_args):
            debug_lines.append(f"  [arg{i}] = {repr(v)}")
        for k, v in resolved_kwargs:
            debug_lines.append(f"  {k} = {repr(v)}")

        try:
            result = func(*resolved_args, **dict(resolved_kwargs))

            debug_lines.append("📤 Result:")
            
            if result is None:
                debug_lines.append("  None (function returned nothing)")
            elif isinstance(result, str):
                # Handle string results with escaped newlines
                if "\\n" in result:
                    result = result.encode().decode("unicode_escape")
                debug_lines.extend(f"  {line}" for line in result.split("\n"))
            elif isinstance(result, (int, float, bool)):
                debug_lines.append(f"  {result}")
            elif isinstance(result, (list, tuple, dict)):
                # For collections, use json formatting
                import json
                try:
                    formatted = json.dumps(result, indent=2, default=str)
                    debug_lines.extend(f"  {line}" for line in formatted.split("\n"))
                except:
                    debug_lines.append(f"  {repr(result)}")
            else:
                # For objects, show their attributes
                result_repr = repr(result)
                debug_lines.append(f"  {result_repr}")
                debug_lines.append(f"  (type: {type(result).__name__})")
                
                # Show object attributes if not too many
                try:
                    attrs = {k: v for k, v in vars(result).items() if not k.startswith('_')}
                    debug_lines.append(f"  [DEBUG: Found {len(attrs)} attributes]")
                    if attrs:
                        debug_lines.append("  Attributes:")
                        for key, value in list(attrs.items())[:10]:
                            value_repr = repr(value)
                            if len(value_repr) > 60:
                                value_repr = value_repr[:60] + "..."
                            debug_lines.append(f"    {key}: {value_repr}")
                        if len(attrs) > 10:
                            debug_lines.append(f"    ... and {len(attrs) - 10} more")
                except Exception as ex:
                    debug_lines.append(f"  [Error getting attributes: {ex}]")

        except Exception as e:
            debug_lines.append(f"🧨 Exception: {type(e).__name__} — {e}")

        debug_lines.append("-" * 40)
        output = "\n".join(debug_lines)

        app = get_shared().app
        if hasattr(app, "tb_debug") and hasattr(app.tb_debug, "append_text"):
            app.tb_debug.append_text(output)
        else:
            print(output)

    def toggle_debug_output(self):
        """Toggle debug output on/off"""
        from utils.debug_logger import set_debug_mode
        enabled = self.debug_enabled_var.get()
        set_debug_mode(enabled=enabled)
        status = "enabled" if enabled else "disabled"
        print(f"🐛 Debug output {status}")

    def update_output_mode(self):
        """Update where debug output goes"""
        from utils.debug_logger import set_debug_mode
        mode = self.output_mode_var.get()
        set_debug_mode(enabled=True, output=mode)
        print(f"📍 Debug output → {mode}")

    def create_widgets(self):
        s = get_shared()
        app = s.app

        self.func_label = ctk.CTkLabel(self.container, text="Select Function:")
        self.func_label.grid(row=0, column=0, sticky="w", padx=10, pady=(0, 5))

        func_names = [name for name, _ in self.get_functions()]
        self.func_dropdown = ctk.CTkComboBox(
            self.container,
            values=func_names,
            width=250,
            command=self.update_function_details
        )
        self.func_dropdown.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        app.func_dropdown = self.func_dropdown

        self.doc_label = ctk.CTkLabel(
            self.container,
            text="",
            text_color="gray",
            wraplength=240,
            anchor="w",
            width=240
        )
        self.doc_label.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 5))

        self.sig_label = ctk.CTkLabel(
            self.container,
            text="",
            text_color="gray",
            wraplength=240,
            width=240,
            anchor="w"
        )
        self.sig_label.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 10))

        self.arg_frame = ctk.CTkFrame(self.container)
        self.arg_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        self.run_button = ctk.CTkButton(self.container, text="Run Function", command=self.run_function)
        self.run_button.grid(row=5, column=0, padx=10, pady=10)

        self.args_preview = ctk.CTkTextbox(self.container, height=80)
        self.args_preview.grid(row=6, column=0, padx=10, pady=10, sticky="ew")

        self.reset_button = ctk.CTkButton(self.container, text="Reset Args", command=self.reset_args)
        self.reset_button.grid(row=7, column=0, padx=10, pady=(0, 10))

        # ─── Debug Output Controls ───────────────────────────────────────────
        separator = ctk.CTkLabel(self.container, text="━" * 30, text_color="gray")
        separator.grid(row=8, column=0, padx=10, pady=(20, 5))

        debug_controls_label = ctk.CTkLabel(self.container, text="Debug Output Controls:", font=("Arial", 12, "bold"))
        debug_controls_label.grid(row=9, column=0, sticky="w", padx=10, pady=(5, 5))

        # Toggle Debug On/Off
        self.debug_enabled_var = ctk.BooleanVar(value=True)
        self.debug_toggle = ctk.CTkSwitch(
            self.container, 
            text="Debug Enabled",
            variable=self.debug_enabled_var,
            command=self.toggle_debug_output
        )
        self.debug_toggle.grid(row=10, column=0, sticky="w", padx=10, pady=5)

        # Output mode radio buttons
        self.output_mode_var = ctk.StringVar(value="textbox")
        
        output_label = ctk.CTkLabel(self.container, text="Output to:", text_color="gray")
        output_label.grid(row=11, column=0, sticky="w", padx=10, pady=(10, 2))

        self.radio_console = ctk.CTkRadioButton(
            self.container,
            text="Console",
            variable=self.output_mode_var,
            value="console",
            command=self.update_output_mode
        )
        self.radio_console.grid(row=12, column=0, sticky="w", padx=20, pady=2)

        self.radio_textbox = ctk.CTkRadioButton(
            self.container,
            text="TextBox",
            variable=self.output_mode_var,
            value="textbox",
            command=self.update_output_mode
        )
        self.radio_textbox.grid(row=13, column=0, sticky="w", padx=20, pady=2)

        self.radio_both = ctk.CTkRadioButton(
            self.container,
            text="Both",
            variable=self.output_mode_var,
            value="both",
            command=self.update_output_mode
        )
        self.radio_both.grid(row=14, column=0, sticky="w", padx=20, pady=2)

        self.container.grid_columnconfigure(0, weight=1)

        if func_names:
            self.func_dropdown.set(func_names[0])
            self.after_idle(self.update_function_details)