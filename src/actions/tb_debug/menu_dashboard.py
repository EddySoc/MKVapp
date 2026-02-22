#-------------------------------------------------------------------------------
# Name:        menu_dashboard.py
# Purpose:     Menu Dashboard UI for inspecting popup menus and triggers
# Author:      Copilot
# Created:     2026-01-17
#-------------------------------------------------------------------------------

import customtkinter as ct
import tkinter as tk
from decorators.decorators import menu_tag

class MenuDashboard(ct.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("📋 Menu Dashboard")
        self.geometry("1100x700+120+120")
        self.resizable(True, True)

        from shared_data import get_shared
        self.s = get_shared()

        # Imports for menu inspection
        from menus.popup import MENU_COMPOSITIONS, build_items_from_composition, MENU_COMPOSITIONS as MC
        from menus.menu_registry import global_menu_registry

        self.MENU_COMPOSITIONS = MENU_COMPOSITIONS
        self.build_items_from_composition = build_items_from_composition
        self.global_menu_registry = global_menu_registry

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        tabs = ct.CTkTabview(self)
        tabs.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        tabs.add("Menus")
        tabs.add("Scan")
        tabs.add("Preview")

        # --- Menus tab ---
        menu_frame = ct.CTkFrame(tabs.tab("Menus"))
        menu_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        tabs.tab("Menus").grid_columnconfigure(0, weight=1)
        tabs.tab("Menus").grid_columnconfigure(1, weight=2)

        # --- Preview tab ---
        preview_frame = ct.CTkFrame(tabs.tab("Preview"))
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        tabs.tab("Preview").grid_columnconfigure(0, weight=1)
        tabs.tab("Preview").grid_rowconfigure(0, weight=1)

        # Scrollable canvas setup
        canvas = tk.Canvas(preview_frame, borderwidth=0, background="#222")
        scroll_y = tk.Scrollbar(preview_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Frame in canvas
        inner_frame = ct.CTkFrame(canvas)
        window_id = canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(window_id, width=canvas.winfo_width())
        inner_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=canvas.winfo_width()))

        # Mouse wheel scroll support
        def _on_mousewheel(event):
            if event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")

        # Windows and MacOS
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # Linux (X11)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

        preview_title = ct.CTkLabel(inner_frame, text="Popup Menu Preview Loaded", font=("Segoe UI", 14, "bold"))
        preview_title.pack(pady=(0, 10), anchor="w")

        for popup_key, composition in self.MENU_COMPOSITIONS.items():
            group_label = ct.CTkLabel(inner_frame, text=f"▶ {popup_key}", text_color="#80aaff", font=("Segoe UI", 11, "bold"))
            group_label.pack(anchor="w", pady=(10, 0))

            for part in composition:
                if part == "__title__":
                    title = ct.CTkLabel(inner_frame, text=f"━━━ {popup_key.upper()} ━━━", text_color="#00BFFF", font=("Segoe UI", 10, "bold"))
                    title.pack(anchor="w", pady=(2, 2))
                elif part == "__sep__":
                    sep = ct.CTkLabel(inner_frame, text="─" * 30, text_color="#444", font=("Consolas", 10))
                    sep.pack(anchor="w", pady=(2, 2))
                elif part == "__dynamic_filter__":
                    for g in ["videos", "subtitles"]:
                        labels = self.global_menu_registry.grouped().get(g, [])
                        if labels:
                            sub_label = ct.CTkLabel(inner_frame, text=f"[{g}]", text_color="#80aaff", font=("Segoe UI", 10, "bold"))
                            sub_label.pack(anchor="w", pady=(2, 0))
                            for label in labels:
                                entry = self.global_menu_registry.get(label)
                                if entry:
                                    btn = ct.CTkButton(inner_frame, text=label, command=entry["func"], width=180)
                                    btn.pack(anchor="w", padx=24, pady=1)
                else:
                    labels = self.global_menu_registry.grouped().get(part, [])
                    if labels:
                        for label in labels:
                            entry = self.global_menu_registry.get(label)
                            if entry:
                                btn = ct.CTkButton(inner_frame, text=label, command=entry["func"], width=180)
                                btn.pack(anchor="w", padx=24, pady=1)

        # Dropdown van popup keys (widgets)
        keys = list(self.MENU_COMPOSITIONS.keys())
        self.menu_sel = ct.CTkComboBox(menu_frame, values=keys, width=260, command=self.on_menu_selected)
        self.menu_sel.grid(row=0, column=0, sticky="w", padx=8, pady=(6, 8))
        if keys:
            self.menu_sel.set(keys[0])

        # Left: items list
        left = ct.CTkFrame(menu_frame)
        left.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        menu_frame.grid_rowconfigure(1, weight=1)
        menu_frame.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        try:
            from customtkinter import get_appearance_mode
            theme = get_appearance_mode()
        except Exception:
            theme = "Dark"

        if str(theme).lower().startswith("dark"):
            it_bg, it_fg = "black", "white"
        else:
            it_bg, it_fg = "white", "black"

        self.items_tb = tk.Text(left, wrap="word", height=30, bg=it_bg, fg=it_fg)
        self.items_tb.grid(row=0, column=0, sticky="nsew")
        self.items_tb.configure(state="disabled")

        # Right: triggers list
        right = ct.CTkFrame(menu_frame)
        right.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
        menu_frame.grid_columnconfigure(1, weight=3)
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Use a Listbox for triggers so we can color items reliably
        self.triggers_list = tk.Listbox(right, height=30, bg=it_bg, fg=it_fg, selectbackground="blue", selectforeground="white")
        self.triggers_list.grid(row=0, column=0, sticky="nsew")
        self.triggers_scroll = tk.Scrollbar(right, orient="vertical", command=self.triggers_list.yview)
        self.triggers_scroll.grid(row=0, column=1, sticky="ns")
        self.triggers_list.configure(yscrollcommand=self.triggers_scroll.set)

        # Buttons
        btn_frame = ct.CTkFrame(menu_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8,0))
        ct.CTkButton(btn_frame, text="Refresh", command=self.refresh).pack(side="left", padx=6)
        ct.CTkButton(btn_frame, text="Show Popup Composition", command=self.show_composition).pack(side="left", padx=6)

        # --- Scan tab ---
        scan_frame = ct.CTkFrame(tabs.tab("Scan"))
        scan_frame.pack(fill="both", expand=True, padx=8, pady=8)
        if str(theme).lower().startswith("dark"):
            sc_bg, sc_fg = "black", "white"
        else:
            sc_bg, sc_fg = "white", "black"

        self.scan_tb = tk.Text(scan_frame, wrap="word", bg=sc_bg, fg=sc_fg)
        self.scan_tb.pack(fill="both", expand=True)
        self.scan_tb.configure(state="disabled")

        scan_btns = ct.CTkFrame(scan_frame)
        scan_btns.pack(fill="x", pady=(6,0))
        ct.CTkButton(scan_btns, text="Rescan Registry", command=self.do_scan).pack(side="left", padx=6)
        ct.CTkButton(scan_btns, text="Copy Output", command=self.copy_scan).pack(side="left", padx=6)

        # Initiale populatie
        self.on_menu_selected(self.menu_sel.get())
        self.do_scan()

    def on_menu_selected(self, key):
        # Toon items met de compositie zodat scheidingslijnen en titels zichtbaar zijn
        parts = self.MENU_COMPOSITIONS.get(key, [])
        reg = self.global_menu_registry

        self.items_tb.configure(state="normal")
        self.items_tb.delete("1.0", "end")
        if not parts:
            self.items_tb.insert("1.0", "(geen items)")
        else:
            for part in parts:
                if part == "__title__":
                    self.items_tb.insert("end", f"━━━ {key.upper()} ━━━\n")
                elif part == "__sep__":
                    self.items_tb.insert("end", "────────────\n")
                elif part == "__dynamic_filter__":
                    # fallback: toon videos/subtitles afhankelijk van segbut_var
                    current_mode = None
                    try:
                        current_mode = self.s.segbut_var.get() if hasattr(self.s, 'segbut_var') and self.s.segbut_var is not None else None
                    except Exception:
                        current_mode = None
                    # toon beide groepen als onbekend
                    groups = []
                    if current_mode is None or current_mode == "All":
                        groups = ["videos", "subtitles"]
                    elif current_mode.lower() == "videos":
                        groups = ["videos"]
                    elif current_mode.lower() == "subtitles":
                        groups = ["subtitles"]
                    else:
                        groups = ["videos", "subtitles"]
                    for g in groups:
                        labels = reg.grouped().get(g, [])
                        if labels:
                            self.items_tb.insert("end", f"[{g}]\n")
                            for label in labels:
                                if label and "placeholder" in label.lower():
                                    continue
                                entry = reg.get(label)
                                if not entry:
                                    continue
                                func = entry.get("func")
                                name = func.__name__ if callable(func) else str(func)
                                self.items_tb.insert("end", f"  • {label} → {name}\n")
                else:
                    # behandel als groepsnaam
                    labels = reg.grouped().get(part, [])
                    if not labels:
                        continue
                    self.items_tb.insert("end", f"[{part}]\n")
                    for label in labels:
                        # sla placeholder labels of acties over
                        if not label:
                            continue
                        if "placeholder" in label.lower() or label.strip().startswith("("):
                            continue
                        entry = reg.get(label)
                        if not entry:
                            continue
                        func = entry.get("func")
                        if callable(func):
                            name = func.__name__
                        else:
                            name = str(func)
                        # sla entries over die naar een placeholder actie verwijzen
                        if name == "_placeholder_action":
                            continue
                        self.items_tb.insert("end", f"  • {label} → {name}\n")
        self.items_tb.configure(state="disabled")

        # Toon triggers: scan app widget tree voor custom_name == key
        triggers = self.find_triggers_for_key(key)
        # Vul listbox met triggers (rode items)
        self.triggers_list.delete(0, tk.END)
        if not triggers:
            self.triggers_list.insert(tk.END, "(geen runtime triggers gevonden)")
        else:
            for wpath, w in triggers:
                try:
                    idx = self.triggers_list.size()
                    self.triggers_list.insert(tk.END, f"• {wpath} — {type(w).__name__}")
                    try:
                        # kleur het item rood
                        self.triggers_list.itemconfig(idx, foreground="#c62828")
                    except Exception:
                        pass
                except Exception:
                    pass

    def find_triggers_for_key(self, key):
        # Traverse the app widget tree to find widgets with custom_name == key
        app = getattr(self.s, 'app', None)
        results = []
        if not app:
            return results

        def visit(widget, path):
            # check attribute
            if hasattr(widget, 'custom_name') and getattr(widget, 'custom_name') == key:
                results.append((path, widget))
            # iterate children if available
            try:
                for child in widget.winfo_children():
                    visit(child, path + '/' + child.winfo_name())
            except Exception:
                pass

        try:
            visit(app, app.winfo_name())
        except Exception:
            pass
        return results

    def show_composition(self):
        key = self.menu_sel.get()
        parts = self.MENU_COMPOSITIONS.get(key, [])
        self.items_tb.configure(state="normal")
        self.items_tb.delete("1.0", "end")
        if not parts:
            self.items_tb.insert("1.0", "(geen compositie)")
        else:
            for p in parts:
                self.items_tb.insert("end", f"{p}\n")
        self.items_tb.configure(state="disabled")

    def refresh(self):
        self.on_menu_selected(self.menu_sel.get())
        self.do_scan()

    def do_scan(self):
        # Show registry grouped summary
        try:
            summary = self.global_menu_registry.summary_dict()
        except Exception:
            summary = {}

        self.scan_tb.configure(state="normal")
        self.scan_tb.delete("1.0", "end")
        self.scan_tb.insert("1.0", "🚀 Scanning actions package for tagged menu functions...\n\n")
        for group, items in summary.items():
            self.scan_tb.insert("end", f"Group: {group}\n")
            for it in items:
                self.scan_tb.insert("end", f"  • {it.get('label')} → {it.get('func')}\n")
            self.scan_tb.insert("end", "\n")
        self.scan_tb.configure(state="disabled")

    def copy_scan(self):
        try:
            self.clipboard_clear()
            txt = self.scan_tb.get("1.0", "end")
            self.clipboard_append(txt)
            print("✅ Scan output copied to clipboard")
        except Exception as e:
            print(f"⚠️ Copy failed: {e}")


@menu_tag(label="Menu Dashboard", icon="📋", group=["tb_debug"])
def launch_menu_dashboard(master=None):
    MenuDashboard(master).grab_set()
