import tkinter as tk
import customtkinter as ctk
# Toegevoegde imports voor batch_panel.py
import os
import json
from tkinter import messagebox


import tkinter.ttk as ttk

class PresetSaveDialog(tk.Toplevel):
    """Modal dialog: kies een bestaande preset uit de dropdown of typ een nieuwe naam."""
    def __init__(self, parent, existing_names, initial=""):
        # Gebruik de echte Toplevel als parent voor correcte modaliteit
        top = parent.winfo_toplevel()
        super().__init__(top)
        self.title("Preset opslaan")
        self.resizable(False, False)
        self.result = None
        self.transient(top)

        tk.Label(self, text="Kies een bestaande preset om te overschrijven,\nof typ een nieuwe naam:",
                 justify="left").pack(padx=12, pady=(10, 2), anchor="w")

        self._name_var = tk.StringVar(value=initial)
        self._combo = ttk.Combobox(self, textvariable=self._name_var, values=existing_names, width=36)
        self._combo.pack(padx=12, pady=4, fill="x")
        if initial:
            self._combo.set(initial)
        elif existing_names:
            self._combo.set(existing_names[0])
        self._combo.focus_set()
        self._combo.select_range(0, tk.END)
        self._combo.bind("<<ComboboxSelected>>", lambda _e: self._combo.focus_set())

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=(4, 10))
        tk.Button(btn_frame, text="Opslaan", default="active", width=10,
                  command=self._on_ok).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Annuleren", width=10,
                  command=self._on_cancel).pack(side="left", padx=6)

        self.bind("<Return>", lambda _e: self._on_ok())
        self.bind("<Escape>", lambda _e: self._on_cancel())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Centreer boven het hoofdvenster
        self.update_idletasks()
        px = top.winfo_rootx() + (top.winfo_width() - self.winfo_width()) // 2
        py = top.winfo_rooty() + (top.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        self.grab_set()
        self.lift()
        self.focus_force()
        self.wait_window(self)

    def _on_ok(self):
        self.result = self._combo.get().strip()
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()

# Placeholder voor BATCH_SOURCE_GROUPS als deze niet elders gedefinieerd is
# Voor de batch-panel willen we dezelfde acties gebruiken als in lb_files
# (videos en subtitles). Als mkvapp.core andere groepen definieert, gebruik die.
try:
    from mkvapp.core import BATCH_SOURCE_GROUPS
except ImportError:
    BATCH_SOURCE_GROUPS = ["videos", "subtitles"]
#-------------------------------------------------------------------------------
# Name:        batch_panel.py

class BatchPanel(ctk.CTkFrame):
    """Two-pane widget for building a batch queue from registry actions."""

    def _save_preset(self):
        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "Settings", "batch_sessions.json")
        )
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        existing = sorted(data.keys())
        # Pre-selecteer de actieve preset als er een geselecteerd is in de listbox
        sel = self._preset_lb.curselection()
        initial = self._preset_lb.get(sel[0]) if sel else (existing[0] if existing else "")
        dialog = PresetSaveDialog(self, existing, initial=initial)
        name = dialog.result
        if not name:
            self._info_var.set("Opslaan geannuleerd.")
            return

        if name in data:
            ok = messagebox.askyesno("Bevestig overschrijven", f"Preset '{name}' bestaat al. Overschrijven?")
            if not ok:
                self._info_var.set("Opslaan geannuleerd.")
                return

        from shared_data import get_shared
        s = get_shared()
        data[name] = list(s.batch_queue)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._load_presets_to_listbox()
            self._info_var.set(f"Preset '{name}' opgeslagen.")
        except Exception as e:
            messagebox.showerror("Opslaan mislukt", f"Kan preset niet opslaan:\n{e}")

    def _delete_preset(self):
        sel = self._preset_lb.curselection()
        if not sel:
            self._info_var.set("Geen preset geselecteerd.")
            return
        name = self._preset_lb.get(sel[0])
        ok = messagebox.askyesno("Bevestig verwijderen", f"Preset '{name}' verwijderen?")
        if not ok:
            return
        path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "Settings", "batch_sessions.json")
        )
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data.pop(name, None)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._load_presets_to_listbox()
            self._info_var.set(f"Preset '{name}' verwijderd.")
        except Exception as e:
            messagebox.showerror("Verwijderen mislukt", f"Kan preset niet verwijderen:\n{e}")

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(1, weight=1)

        pad = {"padx": 4, "pady": 2}
        listbox_height = 12

        ctk.CTkLabel(self, text="Beschikbare acties", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, **pad, sticky="w")
        ctk.CTkLabel(self, text="Batch wachtrij", font=("Segoe UI", 11, "bold")).grid(row=0, column=1, **pad, sticky="w")
        ctk.CTkLabel(self, text="Batch-presets", font=("Segoe UI", 11, "bold")).grid(row=0, column=2, **pad, sticky="w")

        avail_frame = ctk.CTkFrame(self, fg_color="transparent")
        avail_frame.grid(row=1, column=0, sticky="nsew", **pad)
        avail_frame.rowconfigure(0, weight=1)
        avail_frame.columnconfigure(0, weight=1)
        self._avail_lb = tk.Listbox(
            avail_frame,
            selectmode=tk.SINGLE,
            bg="#1a1a1a",
            fg="#eaeaea",
            selectbackground="#007acc",
            selectforeground="white",
            activestyle="none",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightcolor="#007acc",
            height=listbox_height
        )
        avail_scroll = tk.Scrollbar(avail_frame, orient="vertical", command=self._avail_lb.yview)
        self._avail_lb.configure(yscrollcommand=avail_scroll.set)
        self._avail_lb.grid(row=0, column=0, sticky="nsew")
        avail_scroll.grid(row=0, column=1, sticky="ns")
        self._avail_lb.bind("<Double-Button-1>", lambda _e: self._add_to_queue())

        queue_frame = ctk.CTkFrame(self, fg_color="transparent")
        queue_frame.grid(row=1, column=1, sticky="nsew", **pad)
        queue_frame.rowconfigure(0, weight=1)
        queue_frame.columnconfigure(0, weight=1)
        self._queue_lb = tk.Listbox(
            queue_frame,
            selectmode=tk.SINGLE,
            bg="#1a1a1a",
            fg="#eaeaea",
            selectbackground="#007acc",
            selectforeground="white",
            activestyle="none",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightcolor="#007acc",
            height=listbox_height
        )
        queue_scroll = tk.Scrollbar(queue_frame, orient="vertical", command=self._queue_lb.yview)
        self._queue_lb.configure(yscrollcommand=queue_scroll.set)
        self._queue_lb.grid(row=0, column=0, sticky="nsew")
        queue_scroll.grid(row=0, column=1, sticky="ns")

        preset_frame = ctk.CTkFrame(self, fg_color="transparent")
        preset_frame.grid(row=1, column=2, sticky="nsew", **pad)
        preset_frame.rowconfigure(0, weight=1)
        preset_frame.columnconfigure(0, weight=1)
        self._preset_lb = tk.Listbox(
            preset_frame,
            selectmode=tk.SINGLE,
            bg="#1a1a1a",
            fg="#eaeaea",
            selectbackground="#007acc",
            selectforeground="white",
            activestyle="none",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightcolor="#007acc",
            height=listbox_height
        )
        preset_scroll = tk.Scrollbar(preset_frame, orient="vertical", command=self._preset_lb.yview)
        self._preset_lb.configure(yscrollcommand=preset_scroll.set)
        self._preset_lb.grid(row=0, column=0, sticky="nsew")
        preset_scroll.grid(row=0, column=1, sticky="ns")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=2, column=0, columnspan=1, sticky="ew", pady=(8,0))
        ctk.CTkButton(btns, text="→ Toevoegen", width=90, command=self._add_to_queue).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="← Verwijderen", width=90, command=self._remove_from_queue).pack(side="left", padx=2)

        move_frame = ctk.CTkFrame(self, fg_color="transparent")
        move_frame.grid(row=2, column=1, sticky="ew", pady=(8,0))
        ctk.CTkButton(move_frame, text="↑ Omhoog", width=70, command=self._move_up).pack(side="left", padx=2)
        ctk.CTkButton(move_frame, text="↓ Omlaag", width=70, command=self._move_down).pack(side="left", padx=2)
        ctk.CTkButton(move_frame, text="🗑 Wachtrij wissen", width=110, command=self._clear_queue).pack(side="left", padx=2)

        preset_btns = ctk.CTkFrame(self, fg_color="transparent")
        preset_btns.grid(row=2, column=2, sticky="ew", pady=(8,0))
        ctk.CTkButton(preset_btns, text="Opslaan", width=70, command=self._save_preset).pack(side="left", padx=2)
        ctk.CTkButton(preset_btns, text="🗑 Verwijderen", width=100, command=self._delete_preset).pack(side="left", padx=2)

        self._preset_lb.bind("<<ListboxSelect>>", lambda e: self._load_preset())

        self._info_var = tk.StringVar(value="")
        ctk.CTkLabel(self, textvariable=self._info_var, text_color="gray").grid(row=3, column=0, columnspan=3, sticky="w", padx=8, pady=2)



        # Laad presets uit Settings/batch_sessions.json in de presets-listbox
        self._load_presets_to_listbox()

        # Vul direct de beschikbare acties
        self._populate_available()

    # Bewerken-knop is niet meer nodig: bewerken = laden, aanpassen, opslaan

    # ------------------------------------------------------------------
    # Populate available actions from registry
    # ------------------------------------------------------------------
    def _populate_available(self):
        try:
            from menus.menu_registry import global_menu_registry
            grouped = global_menu_registry.grouped()
            self._avail_lb.delete(0, tk.END)
            seen = set()
            for group in BATCH_SOURCE_GROUPS:
                labels = grouped.get(group, [])
                if labels:
                    self._avail_lb.insert(tk.END, f"── {group} ──")
                    # Mark section headers so they can't be added
                    self._avail_lb.itemconfig(tk.END, fg="#888888", selectbackground="#1a1a1a")
                    for label in labels:
                        if label not in seen:
                            seen.add(label)
                            self._avail_lb.insert(tk.END, f"  {label}")
        except Exception as exc:
            print(f"⚠️ BatchPanel: could not load actions: {exc}")

    # ------------------------------------------------------------------
    # Preset handling
    # ------------------------------------------------------------------
    def _load_presets_to_listbox(self):
        path = os.path.join(os.path.dirname(__file__), "..", "Settings", "batch_sessions.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        # Clear and populate
        self._preset_lb.delete(0, tk.END)
        for name in sorted(data.keys()):
            self._preset_lb.insert(tk.END, name)

    def _load_preset(self, event=None):
        sel = self._preset_lb.curselection()
        if not sel:
            return
        name = self._preset_lb.get(sel[0])
        path = os.path.join(os.path.dirname(__file__), "..", "Settings", "batch_sessions.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        preset = data.get(name, [])
        from shared_data import get_shared
        s = get_shared()
        s.batch_queue = list(preset)
        # refresh UI
        self.refresh_queue()

    # ------------------------------------------------------------------
    # Queue operations
    # ------------------------------------------------------------------
    def _selected_action_label(self) -> str | None:
        """Return the clean label of the currently selected available action, or None."""
        sel = self._avail_lb.curselection()
        if not sel:
            return None
        raw = self._avail_lb.get(sel[0]).strip()
        if raw.startswith("──"):   # section header
            return None
        return raw

    def _add_to_queue(self):
        print("[DEBUG] _add_to_queue called")
        label = self._selected_action_label()
        if not label:
            return
        from shared_data import get_shared
        s = get_shared()
        s.batch_queue.append(label)
        self._queue_lb.insert(tk.END, label)
        self._update_info()

    def _remove_from_queue(self):
        print("[DEBUG] _remove_from_queue called")
        sel = self._queue_lb.curselection()
        if not sel:
            return
        idx = sel[0]
        from shared_data import get_shared
        s = get_shared()
        if 0 <= idx < len(s.batch_queue):
            s.batch_queue.pop(idx)
        self._queue_lb.delete(idx)
        self._update_info()

    def _move_up(self):
        print("[DEBUG] _move_up called")
        sel = self._queue_lb.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        from shared_data import get_shared
        s = get_shared()
        s.batch_queue[idx - 1], s.batch_queue[idx] = s.batch_queue[idx], s.batch_queue[idx - 1]
        label = self._queue_lb.get(idx)
        self._queue_lb.delete(idx)
        self._queue_lb.insert(idx - 1, label)
        self._queue_lb.selection_set(idx - 1)

    def _move_down(self):
        print("[DEBUG] _move_down called")
        sel = self._queue_lb.curselection()
        if not sel:
            return
        idx = sel[0]
        from shared_data import get_shared
        s = get_shared()
        if idx >= len(s.batch_queue) - 1:
            return
        s.batch_queue[idx], s.batch_queue[idx + 1] = s.batch_queue[idx + 1], s.batch_queue[idx]
        label = self._queue_lb.get(idx)
        self._queue_lb.delete(idx)
        self._queue_lb.insert(idx + 1, label)
        self._queue_lb.selection_set(idx + 1)

    def _clear_queue(self):
        print("[DEBUG] _clear_queue called")
        from shared_data import get_shared
        s = get_shared()
        s.batch_queue.clear()
        self._queue_lb.delete(0, tk.END)
        self._update_info()

    def _update_info(self):
        from shared_data import get_shared
        n = len(get_shared().batch_queue)
        self._info_var.set(f"{n} actie{'s' if n != 1 else ''} in wachtrij")

    # ------------------------------------------------------------------
    # Public: refresh queue display (e.g. after external modification)
    # ------------------------------------------------------------------
    def refresh_queue(self):
        from shared_data import get_shared
        s = get_shared()
        self._queue_lb.delete(0, tk.END)
        for label in s.batch_queue:
            self._queue_lb.insert(tk.END, label)
        self._update_info()
