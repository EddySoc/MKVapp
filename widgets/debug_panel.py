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
import utils.text_helpers as utils

class DebugPanel(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("🧪 Debug Panel")
        self.geometry("300x500")
        self.resizable(False, False)

        # Optional: keep it floating above
        self.lift()
        self.after(10, lambda: self.attributes("-topmost", False))

        # Create internal frame for layout
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self.arg_entries = {}
        self.create_widgets()

    def get_functions(self):
        return [(name, obj) for name, obj in inspect.getmembers(actions_test, inspect.isfunction)]

    def parse_arg(self, raw):
        raw = raw.strip()
        if raw.lower() == "true": return True
        if raw.lower() == "false": return False
        if raw == "app":
            from shared_data import get_shared
            return get_shared().app
        if raw == "show_config": return self.show_config_checkbox.get()
        try: return int(raw)
        except: pass
        try: return float(raw)
        except: pass

        from shared_data import get_shared
        s = get_shared()
        app = s.app
        if hasattr(app, raw):
            return getattr(app, raw)

        return raw.strip("'").strip('"')

    def update_function_details(self, *_):
        func_name = self.func_dropdown.get()
        func = dict(self.get_functions()).get(func_name)
        if not func:
            print(f"⚠️ Function '{func_name}' not found.")
            return

        sig = inspect.signature(func)
        self.sig_label.configure(text=str(sig))
        self.doc_label.configure(text=func.__doc__ or "No documentation.")

        for widget in self.arg_frame.winfo_children():
            widget.destroy()
        self.arg_entries.clear()

        for i, (param_name, param) in enumerate(sig.parameters.items()):
            if param_name == "show_config":
                continue

            lbl = ctk.CTkLabel(self.arg_frame, text=f"{param_name}:")
            lbl.grid(row=i, column=0, sticky="w", padx=5, pady=2)

            entry = ctk.CTkEntry(self.arg_frame, placeholder_text=f"{param_name}", width=240)
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="w")
            entry.bind("<Return>", lambda event: self.run_function())
            self.arg_entries[param_name] = entry

            if param.default != inspect.Parameter.empty:
                entry.insert(0, str(param.default))
                entry.configure(text_color="gray")

        self.arg_frame.grid_columnconfigure(1, weight=1)
        self.arg_frame.update_idletasks()

    def run_function(self):
        from shared_data import get_shared
        import ast
        import inspect

        func_name = self.func_dropdown.get().strip()
        func = dict(self.get_functions()).get(func_name)
        if not func:
            print(f"⚠️ Function '{func_name}' not found.")
            return

        debug_lines = [f"🛠️ Ran: {func_name}"]
        sig = inspect.signature(func)
        resolved_args = []
        resolved_kwargs = {}

        for param_name, entry_widget in self.arg_entries.items():
            raw = entry_widget.get().strip()
            if raw == "":
                continue

            if raw == "app":
                value = get_shared().app
            else:
                try:
                    value = ast.literal_eval(raw)
                except Exception:
                    value = raw

            if sig.parameters[param_name].default is inspect.Parameter.empty:
                resolved_args.append(value)
            else:
                resolved_kwargs[param_name] = value

        def fmt(v):
            return f"(tuple) {v}" if isinstance(v, tuple) else v

        debug_lines.append(
            f"🧪 Calling {func_name} with args={[fmt(v) for v in resolved_args]}, "
            f"kwargs={{k: fmt(v) for k, v in resolved_kwargs.items()}}"
        )

        try:
            result = func(*resolved_args, **resolved_kwargs)
            debug_lines.append(f"📤 Result: {result}")
        except Exception as e:
            debug_lines.append(f"🧨 Exception: {type(e).__name__} — {e}")

        debug_lines.append("-" * 40)

        app = get_shared().app
        output = "\n".join(debug_lines)
        if hasattr(app, "tb_debug") and hasattr(app.tb_debug, "append_text"):
            app.tb_debug.append_text(output)
        else:
            print(output)

    def create_widgets(self):
        from shared_data import get_shared
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

        if func_names:
            self.func_dropdown.set(func_names[0])
            self.after_idle(self.update_function_details)

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

        self.status_label = ctk.CTkLabel(self.container, text="", text_color="gray")
        self.status_label.grid(row=6, column=0, sticky="w", padx=10, pady=(5, 0))
        app.status_label = self.status_label

        self.show_config_checkbox = ctk.CTkCheckBox(self.container, text="Show Widget Config")
        self.show_config_checkbox.grid(row=7, column=0, sticky="w", padx=10, pady=(5, 0))
        self.show_config_checkbox.select()

        self.container.grid_columnconfigure(0, weight=1)
        self.func_dropdown.configure(command=self.update_function_details)