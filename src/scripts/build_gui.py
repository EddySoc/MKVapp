"""
MKVApp Build GUI
Graphical interface for building portable executable with PyInstaller
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import os
import shutil
import sys
import subprocess
import re
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
        self.build_mode = ctk.StringVar(value="Single EXE (portable)")
        self.icon_path = ctk.StringVar(value="")
        
        self.source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Load persistent settings
        self.settings_file = os.path.join(self.source_dir, "Settings", "build_backup_cfg.json")
        self.legacy_settings_file = os.path.join(self.source_dir, "Settings", "persistent_cfg.json")
        self.load_settings()
        self.is_building = False
        self.progress_dots = 0
        self.progress_animation_id = None
        
        # Queue for log messages from build thread
        self.log_queue = queue.Queue()
        self._session_log_lines = []
        self._build_log_file_path = None
        
        # Build UI
        self.create_widgets()
        
        # Start queue processor
        self.process_log_queue()

    def load_settings(self):
        """Load persistent settings"""
        try:
            settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            build_settings = settings.get('build', {}) if isinstance(settings, dict) else {}

            if not build_settings and os.path.exists(self.legacy_settings_file):
                with open(self.legacy_settings_file, 'r', encoding='utf-8') as f:
                    legacy = json.load(f)
                build_settings = {
                    'BuildIcon': legacy.get('BuildIcon', ''),
                    'BuildOutputDir': legacy.get('BuildOutputDir', self.output_dir.get()),
                    'BuildConsoleMode': legacy.get('BuildConsoleMode', self.console_mode.get()),
                    'BuildUpxCompression': legacy.get('BuildUpxCompression', self.upx_compression.get()),
                    'BuildCleanBuild': legacy.get('BuildCleanBuild', self.clean_build.get()),
                    'BuildMode': legacy.get('BuildMode', self.build_mode.get()),
                }

            if 'BuildIcon' in build_settings:
                self.icon_path.set(build_settings['BuildIcon'])
            if 'BuildOutputDir' in build_settings:
                self.output_dir.set(build_settings['BuildOutputDir'])
            if 'BuildConsoleMode' in build_settings:
                self.console_mode.set(bool(build_settings['BuildConsoleMode']))
            if 'BuildUpxCompression' in build_settings:
                self.upx_compression.set(bool(build_settings['BuildUpxCompression']))
            if 'BuildCleanBuild' in build_settings:
                self.clean_build.set(bool(build_settings['BuildCleanBuild']))
            if 'BuildMode' in build_settings and build_settings['BuildMode']:
                self.build_mode.set(build_settings['BuildMode'])
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        """Save persistent settings"""
        try:
            settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            if not isinstance(settings, dict):
                settings = {}

            settings.setdefault('backup', {})
            settings['build'] = {
                'BuildIcon': self.icon_path.get(),
                'BuildOutputDir': self.output_dir.get(),
                'BuildConsoleMode': self.console_mode.get(),
                'BuildUpxCompression': self.upx_compression.get(),
                'BuildCleanBuild': self.clean_build.get(),
                'BuildMode': self.build_mode.get(),
            }

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def _apply_spec_overrides(self, spec_file):
        """Apply temporary overrides to MKVApp.spec based on GUI options."""
        with open(spec_file, 'r', encoding='utf-8') as f:
            original = f.read()

        updated = original
        requested_upx = self.upx_compression.get()
        upx_path = shutil.which("upx")
        upx_available = bool(upx_path)
        effective_upx = requested_upx and upx_available

        if requested_upx and not upx_available:
            self.log("⚠️ UPX requested but 'upx' was not found in PATH. Building without UPX compression.")
        elif effective_upx:
            self.log(f"✅ UPX found: {upx_path}")

        self._effective_upx = effective_upx
        self._effective_console = self.console_mode.get()

        updated = re.sub(r"(?m)^\s*upx\s*=\s*(True|False)\s*,\s*$", f"    upx={effective_upx},", updated, count=1)
        updated = re.sub(r"(?m)^\s*console\s*=\s*(True|False)\s*,\s*$", f"    console={self.console_mode.get()},", updated, count=1)

        icon_file = self.icon_path.get().strip()
        has_valid_icon = bool(icon_file and os.path.isfile(icon_file))
        icon_line_re = r"(?m)^\s*icon\s*=.*?,\s*$"
        self._effective_icon = icon_file if has_valid_icon else "None"

        if icon_file and not has_valid_icon:
            self.log(f"⚠️ Icon file not found: {icon_file}. Building without custom icon.")

        if has_valid_icon:
            icon_line = f"    icon={repr(icon_file)},"
            if re.search(icon_line_re, updated):
                updated = re.sub(icon_line_re, icon_line, updated, count=1)
            else:
                updated = re.sub(r"(?m)^(\s*name\s*=\s*'MKVApp'\s*,\s*)$", r"\1\n" + icon_line, updated, count=1)
        else:
            updated = re.sub(icon_line_re + r"\n?", "", updated, count=1)

        if updated != original:
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(updated)

        return original

    def _restore_spec(self, spec_file, original_content):
        if original_content is None:
            return
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(original_content)

    def _is_onedir_mode(self):
        return self.build_mode.get().startswith("Fast Onedir")

    def _get_spec_file_path(self):
        spec_name = "MKVApp_onedir.spec" if self._is_onedir_mode() else "MKVApp.spec"
        return os.path.join(self.source_dir, spec_name)

    def _calculate_directory_size_mb(self, directory):
        total = 0
        for root, _, files in os.walk(directory):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                try:
                    total += os.path.getsize(file_path)
                except OSError:
                    pass
        return total / (1024 * 1024)

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

        # Build mode selector
        mode_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        mode_frame.pack(fill="x", padx=15, pady=(8, 5))

        mode_label = ctk.CTkLabel(
            mode_frame,
            text="Build Type:",
            font=ctk.CTkFont(size=12)
        )
        mode_label.pack(side="left", padx=(0, 10))

        mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            values=["Single EXE (portable)", "Fast Onedir (faster startup)"],
            variable=self.build_mode,
            width=260,
            height=30
        )
        mode_menu.pack(side="left")
        
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
        
        build_info = """✅ Selectable build mode (Single EXE or Fast Onedir)
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

    def _attach_build_log_file(self, build_dir):
        """Attach a logfile in build folder and write all accumulated session logs."""
        log_file_path = os.path.join(build_dir, "build_log.txt")
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.writelines(self._session_log_lines)
        self._build_log_file_path = log_file_path
    
    def process_log_queue(self):
        """Process queued log messages (runs in main thread)"""
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_line = f"[{timestamp}] {message}\n"
                
                # Add to log
                self.log_text.insert("end", log_line)
                self.log_text.see("end")

                # Keep an in-memory copy for this build session
                self._session_log_lines.append(log_line)

                # Mirror log lines to file when build output folder is known
                if self._build_log_file_path:
                    try:
                        with open(self._build_log_file_path, 'a', encoding='utf-8') as f:
                            f.write(log_line)
                    except Exception:
                        pass
                
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
        
        # Save settings
        self.save_settings()

        # Reset current build log storage
        self._session_log_lines = []
        self._build_log_file_path = None
        
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
        original_spec_content = None
        spec_file = self._get_spec_file_path()
        try:
            # Step 1: PyInstaller build
            self.log("📦 Step 1/3: Building executable with PyInstaller...")
            self.update_status("Building executable...")

            # Apply temporary spec overrides from GUI options
            original_spec_content = self._apply_spec_overrides(spec_file)

            self.log(
                f"⚙️ Effective options: console={self._effective_console} | upx={self._effective_upx} | icon={self._effective_icon}"
            )
            self.log(f"🧩 Build mode: {self.build_mode.get()} | spec={os.path.basename(spec_file)}")
            
            # Build PyInstaller command
            cmd = ["pyinstaller"]
            
            if self.clean_build.get():
                cmd.append("--clean")
            
            # Use spec file
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
<<<<<<< Updated upstream
            if os.path.exists(output_dir):
                self.log(f"Removing existing directory: {output_dir}")
                import shutil
                shutil.rmtree(output_dir)
=======
            if os.path.exists(dated_output):
                self.log(f"Removing existing directory: {dated_output}")
                shutil.rmtree(dated_output)
            os.makedirs(dated_output)

            # Attach file logger now that build output folder exists
            self._attach_build_log_file(dated_output)

            self.log(f"Created dated directory: {dated_output}")
>>>>>>> Stashed changes
            
            os.makedirs(output_dir)
            self.log(f"Created directory: {output_dir}")
            
<<<<<<< Updated upstream
            # Copy executable
            exe_source = os.path.join(self.source_dir, "dist", "MKVApp.exe")
            exe_dest = os.path.join(output_dir, "MKVApp.exe")
            
            if not os.path.exists(exe_source):
                raise Exception(f"Executable not found: {exe_source}")
            
            import shutil
            shutil.copy2(exe_source, exe_dest)
            self.log(f"✅ Copied: MKVApp.exe")
=======
            if os.path.exists(build_source):
                shutil.move(build_source, os.path.join(dated_output, "build"))
                self.log("✅ Moved: build folder")
            
            if os.path.exists(dist_source):
                shutil.move(dist_source, os.path.join(dated_output, "dist"))
                self.log("✅ Moved: dist folder")
            
            if self._is_onedir_mode():
                onedir_exe = os.path.join(dated_output, "dist", "MKVApp_onedir", "MKVApp.exe")
                if not os.path.exists(onedir_exe):
                    raise Exception(f"Onedir executable not found: {onedir_exe}")
                self.log("✅ Fast Onedir build detected")
            else:
                # Copy executable from moved dist
                exe_source = os.path.join(dated_output, "dist", "MKVApp.exe")
                exe_dest = os.path.join(dated_output, "MKVApp.exe")

                if not os.path.exists(exe_source):
                    raise Exception(f"Executable not found: {exe_source}")

                shutil.copy2(exe_source, exe_dest)
                self.log("✅ Copied: MKVApp.exe")
>>>>>>> Stashed changes
            
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
                if self._is_onedir_mode():
                    f.write("dist\\MKVApp_onedir\\MKVApp.exe\n")
                else:
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
                if self._is_onedir_mode():
                    f.write("- Or run dist\\MKVApp_onedir\\MKVApp.exe directly\n\n")
                else:
                    f.write("- Or run MKVApp.exe directly\n\n")
                f.write("Requirements:\n")
                f.write("- Windows 10/11\n")
                f.write("- No additional installations needed\n\n")
                f.write(f"Built on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Build Mode: {self.build_mode.get()}\n")
                f.write(f"Console Mode: {'Yes' if self.console_mode.get() else 'No'}\n")
                f.write(f"UPX Compression: {'Yes' if self.upx_compression.get() else 'No'}\n")
            self.log("✅ Created: README.txt")
            
            # Calculate sizes
            if self._is_onedir_mode():
                onedir_path = os.path.join(dated_output, "dist", "MKVApp_onedir")
                exe_size = self._calculate_directory_size_mb(onedir_path)
                self.log(f"📦 Onedir folder size: {exe_size:.1f} MB")
            else:
                exe_size = os.path.getsize(exe_dest) / (1024 * 1024)
            
            self.log(f"\n🎉 Build completed successfully!")
            self.log(f"📊 Executable size: {exe_size:.1f} MB")
            self.log(f"📁 Output location: {output_dir}")
            
            self.after(0, lambda: self._build_complete(output_dir, exe_size))
            
        except Exception as e:
            self.log(f"\n❌ Build failed: {str(e)}", "error")
            self.after(0, lambda: self._build_error(str(e)))
        finally:
            try:
                self._restore_spec(spec_file, original_spec_content)
            except Exception as restore_error:
                self.log(f"⚠️ Failed to restore spec: {restore_error}")
    
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
