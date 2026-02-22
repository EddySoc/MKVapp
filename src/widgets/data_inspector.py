#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     19/08/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk
import pprint
import inspect, types

class DataInspector(tk.Toplevel):
    def __init__(self, master=None, caller_frame=None, app_object=None):
        super().__init__(master)
        self.title("🧠 Data Inspector")
        self.geometry("700x500")
        self.caller_frame = caller_frame
        self.app_object = app_object

        # Variables
        self.scope_var = tk.StringVar(value="globals")
        self.source_var = tk.StringVar(value="frame")
        self.search_var = tk.StringVar()
        self.type_filter_var = tk.StringVar(value="All")

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Checkbox frame
        checkbox_frame = ttk.Frame(self)
        checkbox_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        self.scope_checkbox = ttk.Checkbutton(
            checkbox_frame, text="Use locals()", variable=self.scope_var,
            onvalue="locals", offvalue="globals", command=self.refresh_data_sources
        )
        self.scope_checkbox.grid(row=0, column=0, padx=(0, 10))

        self.source_checkbox = ttk.Checkbutton(
            checkbox_frame, text="Inspect app object", variable=self.source_var,
            onvalue="app", offvalue="frame", command=self.refresh_data_sources
        )
        self.source_checkbox.grid(row=0, column=1)

        # Search bar
        self.search_entry = ttk.Entry(self, textvariable=self.search_var)
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=(10, 5))
        self.search_var.trace_add("write", self.apply_filters)

        # Type filter dropdown
        self.type_filter = ttk.Combobox(
            self, textvariable=self.type_filter_var,
            values=["All", "Dicts", "Lists"], state="readonly"
        )
        self.type_filter.grid(row=1, column=1, sticky="ew", padx=(0, 10))
        self.type_filter_var.trace_add("write", self.apply_filters)

        # Variable selector
        self.var_selector = ttk.Combobox(self)
        self.var_selector.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10)
        self.var_selector.bind("<<ComboboxSelected>>", self.display_selected_data)

        # Preview label
        self.preview_label = ttk.Label(self, text="Select a variable to preview its value.")
        self.preview_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))

        # Text area
        self.text_area = tk.Text(self, wrap="word", bg="black", fg="white", insertbackground="white")
        self.text_area.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))

        scrollbar = ttk.Scrollbar(self, command=self.text_area.yview)
        scrollbar.grid(row=4, column=1, sticky="ns", pady=(0, 10))
        self.text_area.configure(yscrollcommand=scrollbar.set)

        # Load data
        self.refresh_data_sources()

    def refresh_data_sources(self):
        if self.source_var.get() == "app":
            data = self._flatten_object(self.app_object)
        else:
            scope = self.scope_var.get()
            frame_data = self.caller_frame.f_locals if scope == "locals" else self.caller_frame.f_globals
            data = self._flatten_object(frame_data)

        self.data_dict = {
            k: {"value": v, "type": type(v).__name__}
            for k, v in data.items()
        }

        self.apply_filters()
        self.var_selector.set("")
        self.text_area.delete("1.0", "end")

    def apply_filters(self, *args):
        selected_type = self.type_filter_var.get()
        search_text = self.search_var.get().lower()

        # Filter by type
        if selected_type == "Dicts":
            filtered = [k for k, v in self.data_dict.items() if v["type"] == "dict"]
        elif selected_type == "Lists":
            filtered = [k for k, v in self.data_dict.items() if v["type"] == "list"]
        else:
            filtered = list(self.data_dict.keys())

        # Filter by search text
        if search_text:
            filtered = [k for k in filtered if search_text in k.lower()]

        # Update dropdown values
        self.var_selector["values"] = filtered

        current_selection = self.var_selector.get()

        # Clear selection if it's no longer valid
        if current_selection not in filtered:
            self.var_selector.set("")
            self.text_area.delete("1.0", "end")

        # Update dropdown values
        self.var_selector["values"] = filtered

        # Always show the first item if available
        if filtered:
            self.var_selector.set(filtered[0])
            self.display_selected_data()
        else:
            self.var_selector.set("")
            self.text_area.delete("1.0", "end")
            self.text_area.insert("end", "⚠️ No matching variables found.")

    def display_selected_data(self, event=None):
        selected_name = self.var_selector.get()
        entry = self.data_dict.get(selected_name, None)

        self.text_area.delete("1.0", "end")
        if entry is not None:
            formatted = pprint.pformat(entry["value"], indent=2, width=80)
            self.text_area.insert("end", formatted)
        else:
            self.text_area.insert("end", "⚠️ No data found.")

    def _flatten_object(self, obj, prefix="", visited=None, depth=0, max_depth=10):
        if visited is None:
            visited = set()

        result = {}
        obj_id = id(obj)
        if obj_id in visited:
            result[prefix] = "<circular reference>"
            return result
        visited.add(obj_id)

        if depth > max_depth:
            result[prefix] = "<max depth reached>"
            return result

        if isinstance(obj, (types.FunctionType, types.ModuleType, type)):
            result[prefix] = f"<skipped: {type(obj).__name__}>"
            return result

        if isinstance(obj, dict):
            for k, v in obj.items():
                key = f"{prefix}.{k}" if prefix else k
                result.update(self._flatten_object(v, key, visited, depth + 1, max_depth))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                key = f"{prefix}[{i}]"
                result.update(self._flatten_object(item, key, visited, depth + 1, max_depth))
        elif hasattr(obj, "__dict__"):
            for k, v in vars(obj).items():
                key = f"{prefix}.{k}" if prefix else k
                result.update(self._flatten_object(v, key, visited, depth + 1, max_depth))
        else:
            result[prefix] = obj

        return result

# ✅ Standalone launcher
def show_data_inspector(app=None):
    root = tk._default_root or tk.Tk()
    root.withdraw()
    caller_frame = inspect.currentframe().f_back
    DataInspector(master=root, caller_frame=caller_frame, app_object=app)