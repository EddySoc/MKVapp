"""
MKVApp Build GUI
Graphical interface for building portable executable with PyInstaller
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from threading import Thread
import queue

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BuildGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("🔨 MKVApp Build Creator")
        self.geometry("900x800")
        self.resizable(True, True)
        
        # Variables
        self.output_dir = ctk.StringVar(value="C:\\Python_W_new\\MKVApp_Portable")
        self.console_mode = ctk.BooleanVar(value=False)
        self.upx_compression = ctk.BooleanVar(value=True)
        self.clean_build = ctk.BooleanVar(value=True)
        self.icon_path = ctk.StringVar(value="")
        
        self.source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.is_building = False
        self.progress_dots = 0
        self.progress_animation_id = None
        
        # Queue for log messages from build thread
        self.log_queue = queue.Queue()
        
        # Build UI
        self.create_widgets()
        
        # Start queue processor
        self.process_log_queue()

    def create_widgets(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="🔨 MKVApp Portable Builder",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # === Output Location Section ===
        location_frame = ctk.CTkFrame(main_frame)
        location_frame.pack(fill="x", pady=(0, 15))
        
        location_label = ctk.CTkLabel(
            location_frame,
            text="📁 Output Location",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        location_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        dir_frame = ctk.CTkFrame(location_frame, fg_color="transparent")
        dir_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.dir_entry = ctk.CTkEntry(
            dir_frame,
            textvariable=self.output_dir,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            dir_frame,
            text="Browse...",
            command=self.browse_directory,
            width=100,
            height=35
        )
        browse_btn.pack(side="right")
        
        # === Build Options Section ===
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=(0, 15))
        
        options_label = ctk.CTkLabel(
            options_frame,
            text="⚙️ Build Options",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        options_label.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Console mode checkbox
        console_check = ctk.CTkCheckBox(
            options_frame,
            text="Console Mode - Show console window (useful for debugging)",
            variable=self.console_mode,
            font=ctk.CTkFont(size=12)
        )
        console_check.pack(anchor="w", padx=15, pady=5)
        
        # UPX compression checkbox
        upx_check = ctk.CTkCheckBox(
            options_frame,
            text="UPX Compression - Compress executable (smaller file size)",
            variable=self.upx_compression,
            font=ctk.CTkFont(size=12)
        )
        upx_check.pack(anchor="w", padx=15, pady=5)
        
        # Clean build checkbox
        clean_check = ctk.CTkCheckBox(
            options_frame,
            text="Clean Build - Remove previous build artifacts before building",
            variable=self.clean_build,
            font=ctk.CTkFont(size=12)
        )
        clean_check.pack(anchor="w", padx=15, pady=5)
        
        # Icon file (optional)
        icon_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        icon_frame.pack(fill="x", padx=15, pady=(10, 15))
        
        icon_label = ctk.CTkLabel(
            icon_frame,
            text="Icon (optional):",
            font=ctk.CTkFont(size=12)
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        self.icon_entry = ctk.CTkEntry(
            icon_frame,
            textvariable=self.icon_path,
            placeholder_text="No icon selected",
            height=30,
            font=ctk.CTkFont(size=11)
        )
        self.icon_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        icon_browse_btn = ctk.CTkButton(
            icon_frame,
            text="Browse...",
            command=self.browse_icon,
            width=80,
            height=30
        )
        icon_browse_btn.pack(side="right")
        
        # === Build Info ===
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=(0, 15))
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="📦 What Will Be Built",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        info_label.pack(anchor="w", padx=15, pady=(15, 10))
        
        build_info = """✅ Single-file executable (MKVApp.exe)
✅ Settings folder with all configurations
✅ Start_MKVApp.bat launcher
✅ README.txt with instructions
✅ No external dependencies required"""
        
        info_text = ctk.CTkLabel(
            info_frame,
            text=build_info,
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        info_text.pack(anchor="w", padx=15, pady=(0, 15))
        
        # === Action Buttons ===
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 15))
        
        self.build_btn = ctk.CTkButton(
            button_frame,
            text="🔨 Build Portable EXE",
            command=self.start_build,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144870",
            text_color="#ffffff",
            text_color_disabled="#000000"
        )
        self.build_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.open_btn = ctk.CTkButton(
            button_frame,
            text="📁 Open Output",
            command=self.open_output_folder,
            height=45,
            width=150
        )
        self.open_btn.pack(side="right")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ready to build",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.pack(pady=(0, 10))
        
        # === Build Log ===
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True)
        
        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=15, pady=(15, 10))
        
        log_label = ctk.CTkLabel(
            log_header,
            text="📋 Build Log",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        log_label.pack(side="left")
        
        clear_btn = ctk.CTkButton(
            log_header,
            text="Clear Log",
            command=self.clear_log,
            width=100,
            height=30
        )
        clear_btn.pack(side="right")
        
        # Scrollable log
        self.log_text = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(size=10, family="Consolas"),
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
    def browse_directory(self):
        """Open folder browser dialog for output directory"""
        directory = filedialog.askdirectory(
            title="Select Output Location",
            initialdir=self.output_dir.get()
        )
        if directory:
            self.output_dir.set(directory)
    
    def browse_icon(self):
        """Open file browser for icon selection"""
        icon_file = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=[("Icon files", "*.ico"), ("All files", "*.*")],
            initialdir=self.source_dir
        )
        if icon_file:
            self.icon_path.set(icon_file)
    
    def log(self, message, tag="info"):
        """Add message to log via queue (thread-safe)"""
        self.log_queue.put((message, tag))
    
    def process_log_queue(self):
        """Process queued log messages (runs in main thread)"""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Add to log
                self.log_text.insert("end", f"[{timestamp}] {message}\n")
                self.log_text.see("end")
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.after(100, self.process_log_queue)
    
    def clear_log(self):
        """Clear the build log"""
        self.log_text.delete("1.0", "end")
    
    def start_build(self):
        """Start build in separate thread"""
        if self.is_building:
            messagebox.showwarning("Build in Progress", "A build is already running!")
            return
        
        # Validate output directory
        output_path = self.output_dir.get()
        if not output_path:
            messagebox.showerror("Error", "Please select an output location!")
            return
        
        # Clear log
        self.clear_log()
        self.log("🔨 Starting build process...", "info")
        
        # Start build in thread
        self.is_building = True
        self.progress_dots = 0
        self.build_btn.configure(
            state="disabled", 
            fg_color="#d97706", 
            hover_color="#d97706"
        )
        
        # Start progress animation
        self._animate_progress()
        
        thread = Thread(target=self._build_worker, daemon=True)
        thread.start()
    
    def _animate_progress(self):
        """Animate the build button with progress dots"""
        if not self.is_building:
            return
        
        dots = "." * (self.progress_dots % 4)
        self.build_btn.configure(text=f"🔨 Building{dots:<3}")
        self.progress_dots += 1
        
        # Schedule next animation frame
        self.progress_animation_id = self.after(400, self._animate_progress)
    
    def _stop_progress_animation(self):
        """Stop the progress animation"""
        if self.progress_animation_id:
            self.after_cancel(self.progress_animation_id)
            self.progress_animation_id = None
    
    def _build_worker(self):
        """Worker thread for build process"""
        try:
            # Step 1: PyInstaller build
            self.log("📦 Step 1/3: Building executable with PyInstaller...")
            self.update_status("Building executable...")
            
            # Build PyInstaller command
            cmd = ["pyinstaller"]
            
            if self.clean_build.get():
                cmd.append("--clean")
            
            # Use spec file
            spec_file = os.path.join(self.source_dir, "MKVApp.spec")
            cmd.append(spec_file)
            
            self.log(f"Running: {' '.join(cmd)}")
            
            # Run PyInstaller
            process = subprocess.Popen(
                cmd,
                cwd=self.source_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log(line)
            
            process.wait()
            
            if process.returncode != 0:
                raise Exception(f"PyInstaller failed with return code {process.returncode}")
            
            self.log("✅ Executable built successfully!")
            
            # Step 2: Create distribution folder
            self.log("\n📁 Step 2/3: Creating portable distribution...")
            self.update_status("Creating distribution...")
            
            output_dir = self.output_dir.get()
            
            # Create output directory
            if os.path.exists(output_dir):
                self.log(f"Removing existing directory: {output_dir}")
                import shutil
                shutil.rmtree(output_dir)
            
            os.makedirs(output_dir)
            self.log(f"Created directory: {output_dir}")
            
            # Copy executable
            exe_source = os.path.join(self.source_dir, "dist", "MKVApp.exe")
            exe_dest = os.path.join(output_dir, "MKVApp.exe")
            
            if not os.path.exists(exe_source):
                raise Exception(f"Executable not found: {exe_source}")
            
            import shutil
            shutil.copy2(exe_source, exe_dest)
            self.log(f"✅ Copied: MKVApp.exe")
            
            # Copy Settings folder
            settings_source = os.path.join(self.source_dir, "Settings")
            settings_dest = os.path.join(output_dir, "Settings")
            
            if os.path.exists(settings_source):
                shutil.copytree(settings_source, settings_dest)
                self.log(f"✅ Copied: Settings folder")
            
            # Step 3: Create launcher and README
            self.log("\n📝 Step 3/3: Creating launcher and documentation...")
            self.update_status("Finalizing...")
            
            # Create Start_MKVApp.bat
            launcher_path = os.path.join(output_dir, "Start_MKVApp.bat")
            with open(launcher_path, 'w') as f:
                f.write("@echo off\n")
                f.write("REM Portable MKVApp Launcher\n")
                f.write("echo Starting MKVApp...\n")
                f.write("MKVApp.exe\n")
                f.write("pause\n")
            self.log("✅ Created: Start_MKVApp.bat")
            
            # Create README.txt
            readme_path = os.path.join(output_dir, "README.txt")
            with open(readme_path, 'w') as f:
                f.write("MKVApp Portable Version\n")
                f.write("=====================\n\n")
                f.write("This is a portable version of MKVApp.\n\n")
                f.write("To run:\n")
                f.write("- Double-click Start_MKVApp.bat\n")
                f.write("- Or run MKVApp.exe directly\n\n")
                f.write("Requirements:\n")
                f.write("- Windows 10/11\n")
                f.write("- No additional installations needed\n\n")
                f.write(f"Built on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Console Mode: {'Yes' if self.console_mode.get() else 'No'}\n")
                f.write(f"UPX Compression: {'Yes' if self.upx_compression.get() else 'No'}\n")
            self.log("✅ Created: README.txt")
            
            # Calculate sizes
            exe_size = os.path.getsize(exe_dest) / (1024 * 1024)
            
            self.log(f"\n🎉 Build completed successfully!")
            self.log(f"📊 Executable size: {exe_size:.1f} MB")
            self.log(f"📁 Output location: {output_dir}")
            
            self.after(0, lambda: self._build_complete(output_dir, exe_size))
            
        except Exception as e:
            self.log(f"\n❌ Build failed: {str(e)}", "error")
            self.after(0, lambda: self._build_error(str(e)))
    
    def _build_complete(self, output_dir, exe_size):
        """Called when build completes successfully"""
        self._stop_progress_animation()
        self.is_building = False
        
        # Show success state briefly (enable button so text is white, not black)
        self.build_btn.configure(
            state="normal",
            text="✅ Build Complete!", 
            fg_color="#059669",
            hover_color="#059669"
        )
        
        # Reset button after 2 seconds
        self.after(2000, lambda: self.build_btn.configure(
            text="🔨 Build Portable EXE",
            fg_color="#1f6aa5",
            hover_color="#144870"
        ))
        
        self.update_status(f"✅ Build complete! Executable size: {exe_size:.1f} MB")
        
        # Show success message
        result = messagebox.askyesno(
            "Build Complete",
            f"Portable executable created successfully!\n\n"
            f"Location: {output_dir}\n"
            f"Size: {exe_size:.1f} MB\n\n"
            f"Open output folder?",
            icon='info'
        )
        
        if result:
            self.open_output_folder()
    
    def _build_error(self, error_msg):
        """Called when build fails"""
        self._stop_progress_animation()
        self.is_building = False
        
        # Show error state briefly (enable button so text is white, not black)
        self.build_btn.configure(
            state="normal",
            text="❌ Build Failed",
            fg_color="#dc2626",
            hover_color="#dc2626"
        )
        
        # Reset button after 3 seconds
        self.after(3000, lambda: self.build_btn.configure(
            text="🔨 Build Portable EXE",
            fg_color="#1f6aa5",
            hover_color="#144870"
        ))
        
        self.update_status(f"❌ Build failed: {error_msg}")
        messagebox.showerror("Build Failed", f"Error creating portable exe:\n\n{error_msg}")
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.configure(text=message)
    
    def open_output_folder(self):
        """Open output folder in file explorer"""
        output_dir = self.output_dir.get()
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            messagebox.showwarning("Folder Not Found", "Output directory doesn't exist yet!")


def main():
    """Run the build GUI"""
    app = BuildGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
