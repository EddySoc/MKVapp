import os, json, subprocess, threading, queue, csv, tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
from decorators.decorators import menu_tag
import shutil

def get_ffprobe_cmd():
    """Get ffprobe executable path from config or PATH"""
    # First check if it's in PATH
    if shutil.which("ffprobe"):
        return "ffprobe"
    
    # Check config file for custom path
    try:
        config_path = os.path.join("Settings", "tools_cfg.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                tool_path = config.get("ffprobe_path", "")
                
                if tool_path:
                    # Check if it's a directory or full path
                    if os.path.isdir(tool_path):
                        tool_exe = os.path.join(tool_path, "ffprobe.exe")
                        if os.path.exists(tool_exe):
                            return tool_exe
                    elif os.path.exists(tool_path):
                        return tool_path
    except Exception as e:
        print(f"⚠️ Error reading tools config: {e}")
    
    return "ffprobe"  # Fallback

VIDEO_EXTS=(".mkv",".mp4",".avi",".mov",".wmv",".ts",".m2ts",".webm")

COLUMNS=[
 "path","container","duration","video_codec","width","height","pix_fmt","bit_depth","hdr",
 "audio_tracks","audio_codecs","audio_languages","subtitle_tracks","subtitle_languages"
]

def run_ffprobe(path):
    ffprobe_cmd = get_ffprobe_cmd()
    cmd=[ffprobe_cmd,"-v","error","-print_format","json","-show_format","-show_streams",path]
    try:
        out=subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return json.loads(out.decode("utf-8","ignore"))
    except Exception as e:
        return {"error":str(e)}

def bitdepth_from_pixfmt(pix):
    if not pix:
        return ""

    # typische formaten:
    # yuv420p -> 8 bit
    # yuv420p10le -> 10 bit
    # yuv422p12le -> 12 bit

    import re
    m = re.search(r'p(\d{2})', pix)
    if m:
        return m.group(1)

    if pix.endswith("p"):
        return "8"

    return ""


def detect_hdr(v):
    trc=str(v.get("color_transfer","")).lower()
    if "smpte2084" in trc: return "HDR10"
    if "arib-std-b67" in trc: return "HLG"
    return ""

def parse_info(path,data):
    row={k:"" for k in COLUMNS}
    row["path"]=os.path.basename(path)
    if "error" in data:
        row["container"]="ERROR"
        return row

    fmt=data.get("format",{})
    row["container"]=fmt.get("format_name","")
    row["duration"]=fmt.get("duration","")

    streams=data.get("streams",[])
    v=[s for s in streams if s.get("codec_type")=="video"]
    a=[s for s in streams if s.get("codec_type")=="audio"]
    s=[s for s in streams if s.get("codec_type")=="subtitle"]

    if v:
        v=v[0]
        row["video_codec"]=v.get("codec_name","")
        row["width"]=v.get("width","")
        row["height"]=v.get("height","")
        row["pix_fmt"]=v.get("pix_fmt","")
        row["bit_depth"]=v.get("bits_per_raw_sample","") or bitdepth_from_pixfmt(row["pix_fmt"])
        row["hdr"]=detect_hdr(v)

    row["audio_tracks"]=len(a)
    row["subtitle_tracks"]=len(s)
    
    # Audio codecs
    audio_codecs = set()
    for aud in a:
        codec = aud.get("codec_name")
        if codec:
            audio_codecs.add(codec)
    row["audio_codecs"] = ",".join(sorted(audio_codecs))
    
    # Audio languages
    audio_langs = set()
    for aud in a:
        lang = aud.get("tags", {}).get("language")
        if lang:
            audio_langs.add(lang)
    row["audio_languages"] = ",".join(sorted(audio_langs))

    # Subtitle languages
    langs=set()
    for sub in s:
        lang=sub.get("tags",{}).get("language")
        if not lang:
            lang="und"   # undefined
        langs.add(lang)

    row["subtitle_languages"]=",".join(sorted(langs)) 
    return row

def iter_video_files(path):
    if os.path.isfile(path):
        yield path
    else:
        for root,_,files in os.walk(path):
            for f in files:
                if f.lower().endswith(VIDEO_EXTS):
                    yield os.path.join(root,f)

class App(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Video Inspector PRO")
        self.geometry("1700x800")
        
        # Keep window on top
        self.attributes("-topmost", True)
        self.lift()

        # Top frame with export button
        top = ctk.CTkFrame(self)
        top.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(top, text="📄 Export CSV", command=self.export_csv).pack(side="left", padx=10)

        # Progress bar
        self.pb = ctk.CTkProgressBar(self, mode="determinate")
        self.pb.pack(fill="x", padx=10, pady=5)
        self.pb.set(0)

        # Treeview frame
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Apply dark theme BEFORE creating treeview
        self.configure_dark_theme()

        # Treeview with scrollbars
        self.tree = ttk.Treeview(tree_frame, columns=COLUMNS, show="headings", style="Treeview")
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        for c in COLUMNS:
            self.tree.heading(c,text=c, command=lambda col=c:self.sort_column(col,False))
            self.tree.column(c,width=120)

        self.rows=[]
        self.q=queue.Queue()
    
    def configure_dark_theme(self):
        """Configure dark theme for treeview widget"""
        style = ttk.Style(self)
        
        # Dark theme colors matching customtkinter
        bg_color = "#2b2b2b"  # Dark background
        fg_color = "#ffffff"  # White text
        selected_bg = "#1f538d"  # Blue selection
        selected_fg = "#ffffff"  # White selected text
        header_bg = "#1a1a1a"  # Darker header
        
        # Try to use clam or alt theme which allows more customization
        available_themes = style.theme_names()
        if "clam" in available_themes:
            style.theme_use("clam")
        elif "alt" in available_themes:
            style.theme_use("alt")
        
        # Configure Treeview style
        style.configure("Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=bg_color,
            borderwidth=0
        )
        style.configure("Treeview.Heading",
            background=header_bg,
            foreground=fg_color,
            borderwidth=1
        )
        style.map("Treeview",
            background=[("selected", selected_bg)],
            foreground=[("selected", selected_fg)]
        )
        style.map("Treeview.Heading",
            background=[("active", "#404040")],
            foreground=[("active", fg_color)]
        )
        
        # Configure scrollbars
        style.configure("Vertical.TScrollbar",
            background=bg_color,
            troughcolor=header_bg,
            borderwidth=0,
            arrowcolor=fg_color
        )
        style.configure("Horizontal.TScrollbar",
            background=bg_color,
            troughcolor=header_bg,
            borderwidth=0,
            arrowcolor=fg_color
        )

    def load_files(self, file_paths):
        """Load and scan provided file paths automatically"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.rows=[]
        files = file_paths
        self.total_files = len(files)
        self.pb.set(0)
        threading.Thread(target=self.worker,args=(files,),daemon=True).start()
        self.after(100,self.process_queue)

    def autosize(self):
        for col in COLUMNS:
            max_len=len(col)
            for r in self.rows:
                val=str(r.get(col,""))
                if len(val)>max_len:
                    max_len=len(val)
            self.tree.column(col,width=max(80,min(600,max_len*7)))

    def worker(self,files):
        for f in files:
            data=run_ffprobe(f)
            self.q.put(parse_info(f,data))
        self.q.put(None)

    def process_queue(self):
        try:
            while True:
                item=self.q.get_nowait()
                if item is None:
                    self.autosize()
                    self.pb.set(1.0)  # Complete
                    return
                self.rows.append(item)
                self.tree.insert("", "end", values=[item[c] for c in COLUMNS])
                # Update progress
                if self.total_files > 0:
                    self.pb.set(len(self.rows) / self.total_files)
        except queue.Empty:
            self.after(100,self.process_queue)

    def export_csv(self):
        if not self.rows:
            return
        path=filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return
        with open(path,"w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(self.rows)

    def sort_column(self,col,reverse):
        data=[(self.tree.set(k,col),k) for k in self.tree.get_children("")]
        data.sort(reverse=reverse)
        for i,(val,k) in enumerate(data):
            self.tree.move(k,"",i)
        self.tree.heading(col, command=lambda:self.sort_column(col,not reverse))

@menu_tag(label="Inspect Video Info", icon="🔍", group="videos")
def inspect_video_info():
    """Inspect detailed video information for all selected files"""
    from shared_data import get_shared
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    if not selected:
        from utils import update_tbinfo
        update_tbinfo("⚠️ No files selected for inspection.", "geel")
        print("⚠️ No video files selected")
        return
    
    # Filter to only video files
    video_files = [f for f in selected if f.lower().endswith(VIDEO_EXTS)]
    
    if not video_files:
        from utils import update_tbinfo
        update_tbinfo(f"⚠️ No video files in selection. Selected: {len(selected)} file(s)", "geel")
        print("⚠️ No video files in selection")
        return
    
    # Launch inspector window with selected files
    app = App(s.app)
    app.load_files(video_files)
    
    from utils import update_tbinfo
    update_tbinfo(f"🔍 Inspecting {len(video_files)} video file(s)...", "groen")
    print(f"🔍 Launching video inspector for {len(video_files)} file(s)")

if __name__=="__main__":
    # Standalone mode for testing
    root = ctk.CTk()
    root.withdraw()  # Hide main window
    app = App(root)
    root.mainloop()
