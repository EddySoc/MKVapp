"""
MKVApp Backup GUI (moved to scripts)
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
"""
MKVApp Backup GUI
Graphical interface for creating source code backups
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
import zipfile
import shutil
from threading import Thread

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BackupGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("🔄 MKVApp Backup Creator")
        self.geometry("800x700")
        self.resizable(True, True)
        
        # Variables
        self.backup_dir = ctk.StringVar(value="C:\\Python_W_new\\Backups")
        self.include_venv = ctk.BooleanVar(value=False)
        self.include_pycache = ctk.BooleanVar(value=False)
        self.include_build = ctk.BooleanVar(value=False)
        self.source_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.is_backing_up = False
        self.progress_dots = 0
        self.progress_animation_id = None
        
        # Build UI
        self.create_widgets()
        
        # Load recent backups
        self.refresh_backup_list()
        
    def create_widgets(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="🔄 MKVApp Source Backup",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # === Backup Location Section ===
        location_frame = ctk.CTkFrame(main_frame)
        location_frame.pack(fill="x", pady=(0, 15))
        
        location_label = ctk.CTkLabel(
            location_frame,
            text="📁 Backup Location",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        location_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        dir_frame = ctk.CTkFrame(location_frame, fg_color="transparent")
        dir_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.dir_entry = ctk.CTkEntry(
            dir_frame,
            textvariable=self.backup_dir,
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
        
        # === Options Section ===
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=(0, 15))
        
        options_label = ctk.CTkLabel(
            options_frame,
            text="⚙️ Backup Options",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        options_label.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Virtual environment checkbox
        venv_check = ctk.CTkCheckBox(
            options_frame,
            text="Include Virtual Environment (.venv) - Increases backup size significantly",
            variable=self.include_venv,
            font=ctk.CTkFont(size=12)
        )
        venv_check.pack(anchor="w", padx=15, pady=5)
        
        # __pycache__ checkbox
        pycache_check = ctk.CTkCheckBox(
            options_frame,
            text="Include __pycache__ folders - Not recommended",
            variable=self.include_pycache,
            font=ctk.CTkFont(size=12)
        )
        pycache_check.pack(anchor="w", padx=15, pady=5)
        
        # Build artifacts checkbox
        build_check = ctk.CTkCheckBox(
            options_frame,
            text="Include build artifacts (dist, build folders) - Not recommended",
            variable=self.include_build,
            font=ctk.CTkFont(size=12)
        )
        build_check.pack(anchor="w", padx=15, pady=(5, 15))
        
        # === What will be backed up ===
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", pady=(0, 15))
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="📦 Always Included",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        info_label.pack(anchor="w", padx=15, pady=(15, 10))
        
        includes_text = """✅ All Python source code (.py files)
✅ PyInstaller spec file (MKVApp.spec)
✅ Build scripts (.bat, .sh)
✅ Settings folder with configurations
✅ Requirements.txt
✅ All modules: actions, binding, config, menus, mkvapp, utils, widgets"""
        
        includes_label = ctk.CTkLabel(
            info_frame,
            text=includes_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        includes_label.pack(anchor="w", padx=15, pady=(0, 15))
        
        # === Action Buttons ===
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 15))
        
        self.backup_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Create Backup",
            command=self.create_backup,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144870",
            text_color="#ffffff",
            text_color_disabled="#000000"  # Black text when disabled (during backup)
        )
        self.backup_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔃 Refresh List",
            command=self.refresh_backup_list,
            height=45,
            width=150
        )
        refresh_btn.pack(side="right")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_label.pack(pady=(0, 15))
        
        # === Recent Backups ===
        backups_frame = ctk.CTkFrame(main_frame)
        backups_frame.pack(fill="both", expand=True)
        
        backups_header = ctk.CTkFrame(backups_frame, fg_color="transparent")
        backups_header.pack(fill="x", padx=15, pady=(15, 10))
        
        backups_label = ctk.CTkLabel(
            backups_header,
            text="📋 Recent Backups",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        backups_label.pack(side="left")
        
        open_folder_btn = ctk.CTkButton(
            backups_header,
            text="📁 Open Folder",
            command=self.open_backup_folder,
            width=120,
            height=30
        )
        open_folder_btn.pack(side="right")
        
        # Scrollable backup list
        self.backup_list = ctk.CTkTextbox(
            backups_frame,
            height=150,
            font=ctk.CTkFont(size=11, family="Consolas")
        )
        self.backup_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
    def browse_directory(self):
        """Open folder browser dialog"""
        directory = filedialog.askdirectory(
            title="Select Backup Location",
            initialdir=self.backup_dir.get()
        )
        if directory:
            self.backup_dir.set(directory)
    
    def create_backup(self):
        """Create backup in separate thread"""
        if self.is_backing_up:
            messagebox.showwarning("Backup in Progress", "A backup is already being created!")
            return
        
        # Validate backup directory
        backup_path = self.backup_dir.get()
        if not backup_path:
            messagebox.showerror("Error", "Please select a backup location!")
            return
        
        # Start backup in thread
        self.is_backing_up = True
        self.progress_dots = 0
        self.backup_btn.configure(
            state="disabled", 
            fg_color="#d97706", 
            hover_color="#d97706"
        )
        
        # Start progress animation
        self._animate_progress()
        
        thread = Thread(target=self._backup_worker, daemon=True)
        thread.start()
    
    def _backup_worker(self):
        """Worker thread for backup creation"""
        try:
            backup_dir = self.backup_dir.get()
            
            # Create backup directory if needed
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup name with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            backup_name = f"MKVApp_Source_{timestamp}"
            zip_path = os.path.join(backup_dir, f"{backup_name}.zip")
            
            self.update_status(f"📦 Creating backup: {backup_name}")
            
            # Items to copy
            items_to_copy = [
                "*.py", "*.spec", "*.bat", "*.sh", "*.txt", "*.md",
                "actions", "binding", "config", "decorators", "docs",
                "menus", "mkvapp", "Settings", "tools", "utils", "widgets"
            ]
            
            # Add optional items
            if self.include_venv.get():
                items_to_copy.append(".venv")
            if self.include_build.get():
                items_to_copy.extend(["dist", "build"])
            
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item_pattern in items_to_copy:
                    self._add_to_zip(zipf, item_pattern, backup_name)
                
                # Add backup info file
                info_content = self._generate_backup_info()
                zipf.writestr(f"{backup_name}/BACKUP_INFO.txt", info_content)
            
            # Calculate size
            size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            
            self.after(0, lambda: self._backup_complete(zip_path, size_mb))
            
        except Exception as e:
            self.after(0, lambda: self._backup_error(str(e)))
    
    def _add_to_zip(self, zipf, pattern, backup_name):
        """Add files matching pattern to zip"""
        from glob import glob
        
        # Handle wildcards
        if '*' in pattern:
            matches = glob(os.path.join(self.source_dir, pattern))
            for match in matches:
                if os.path.isfile(match):
                    arcname = os.path.join(backup_name, "src", os.path.basename(match))
                    zipf.write(match, arcname)
        else:
            # Directory or specific file
            source_path = os.path.join(self.source_dir, pattern)
            if os.path.exists(source_path):
                if os.path.isfile(source_path):
                    arcname = os.path.join(backup_name, "src", pattern)
                    zipf.write(source_path, arcname)
                else:
                    # Directory - walk and add all files
                    for root, dirs, files in os.walk(source_path):
                        # Skip __pycache__ if not included
                        if not self.include_pycache.get():
                            dirs[:] = [d for d in dirs if d != '__pycache__']
                        
                        for file in files:
                            # Skip .pyc files if not including pycache
                            if not self.include_pycache.get() and file.endswith('.pyc'):
                                continue
                            
                            file_path = os.path.join(root, file)
                            arcname = os.path.join(
                                backup_name, 
                                "src",
                                os.path.relpath(file_path, self.source_dir)
                            )
                            zipf.write(file_path, arcname)
    
    def _generate_backup_info(self):
        """Generate backup info text"""
        info = f"""MKVApp Source Backup
====================
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Computer: {os.environ.get('COMPUTERNAME', 'Unknown')}
User: {os.environ.get('USERNAME', 'Unknown')}

Options:
--------
Virtual Environment: {'✅ Included' if self.include_venv.get() else '❌ Excluded'}
__pycache__ folders: {'✅ Included' if self.include_pycache.get() else '❌ Excluded'}
Build artifacts: {'✅ Included' if self.include_build.get() else '❌ Excluded'}

Contents:
---------
- Complete source code
- PyInstaller spec file (MKVApp.spec)
- Build scripts (create_portable.bat)
- Settings and configuration files
- Requirements (requirements.txt)
- Documentation

To restore:
-----------
1. Extract this backup to desired location
2. Navigate to src folder
3. Create virtual environment: python -m venv .venv
4. Activate: .venv\\Scripts\\Activate.ps1
5. Install dependencies: pip install -r requirements.txt
6. Run: python app_launcher.py

To build portable exe:
----------------------
1. Ensure all dependencies are installed
2. Run: .\\create_portable.bat
3. Portable app will be in: C:\\Python_W_new\\MKVApp_Portable

"""
        return info
    
    def _animate_progress(self):
        """Animate the backup button with progress dots"""
        if not self.is_backing_up:
            return
        
        dots = "." * (self.progress_dots % 4)
        self.backup_btn.configure(text=f"⏳ Creating Backup{dots:<3}")
        self.progress_dots += 1
        
        # Schedule next animation frame
        self.progress_animation_id = self.after(400, self._animate_progress)
    
    def _stop_progress_animation(self):
        """Stop the progress animation"""
        if self.progress_animation_id:
            self.after_cancel(self.progress_animation_id)
            self.progress_animation_id = None
    
    def _backup_complete(self, zip_path, size_mb):
        """Called when backup completes successfully"""
        self._stop_progress_animation()
        self.is_backing_up = False
        
        # Show success state briefly (enable button so text is white, not black)
        self.backup_btn.configure(
            state="normal",
            text="✅ Backup Complete!", 
            fg_color="#059669",
            hover_color="#059669"
        )
        
        # Reset button after 2 seconds
        self.after(2000, lambda: self.backup_btn.configure(
            text="🔄 Create Backup",
            fg_color="#1f6aa5",
            hover_color="#144870"
        ))
        
        self.update_status(f"✅ Backup created: {os.path.basename(zip_path)} ({size_mb:.2f} MB)")
        
        # Refresh list
        self.refresh_backup_list()
        
        # Show success message
        result = messagebox.askyesno(
            "Backup Complete",
            f"Backup created successfully!\n\n"
            f"Location: {zip_path}\n"
            f"Size: {size_mb:.2f} MB\n\n"
            f"Open backup folder?",
            icon='info'
        )
        
        if result:
            self.open_backup_folder()
    
    def _backup_error(self, error_msg):
        """Called when backup fails"""
        self._stop_progress_animation()
        self.is_backing_up = False
        
        # Show error state briefly (enable button so text is white, not black)
        self.backup_btn.configure(
            state="normal",
            text="❌ Backup Failed",
            fg_color="#dc2626",
            hover_color="#dc2626"
        )
        
        # Reset button after 3 seconds
        self.after(3000, lambda: self.backup_btn.configure(
            text="🔄 Create Backup",
            fg_color="#1f6aa5",
            hover_color="#144870"
        ))
        
        self.update_status(f"❌ Backup failed: {error_msg}")
        messagebox.showerror("Backup Failed", f"Error creating backup:\n\n{error_msg}")
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.configure(text=message)
    
    def refresh_backup_list(self):
        """Refresh the list of recent backups"""
        self.backup_list.delete("1.0", "end")
        
        backup_dir = self.backup_dir.get()
        if not os.path.exists(backup_dir):
            self.backup_list.insert("1.0", "No backups found. Backup directory doesn't exist yet.")
            return
        
        # Find all backup zip files
        backup_files = []
        try:
            for file in os.listdir(backup_dir):
                if file.startswith("MKVApp_Source_") and file.endswith(".zip"):
                    file_path = os.path.join(backup_dir, file)
                    stat = os.stat(file_path)
                    backup_files.append((file, stat.st_mtime, stat.st_size))
        except Exception as e:
            self.backup_list.insert("1.0", f"Error reading backups: {e}")
            return
        
        if not backup_files:
            self.backup_list.insert("1.0", "No backups found in selected directory.")
            return
        
        # Sort by date (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Display backups
        self.backup_list.insert("end", f"{'Backup Name':<50} {'Date':<20} {'Size':>10}\n")
        self.backup_list.insert("end", "=" * 85 + "\n")
        
        for filename, mtime, size in backup_files[:10]:  # Show last 10
            date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            size_mb = size / (1024 * 1024)
            
            # Color code by age
            age_days = (datetime.now().timestamp() - mtime) / 86400
            if age_days < 1:
                icon = "🟢"
            elif age_days < 7:
                icon = "🟡"
            else:
                icon = "⚪"
            
            line = f"{icon} {filename:<47} {date_str:<20} {size_mb:>8.1f} MB\n"
            self.backup_list.insert("end", line)
        
        if len(backup_files) > 10:
            self.backup_list.insert("end", f"\n... and {len(backup_files) - 10} more backups\n")
        
        # Show total size
        total_size_mb = sum(size for _, _, size in backup_files) / (1024 * 1024)
        self.backup_list.insert("end", f"\n📊 Total: {len(backup_files)} backups, {total_size_mb:.1f} MB")
    
    def open_backup_folder(self):
        """Open backup folder in file explorer"""
        backup_dir = self.backup_dir.get()
        if os.path.exists(backup_dir):
            os.startfile(backup_dir)
        else:
            messagebox.showwarning("Folder Not Found", "Backup directory doesn't exist yet!")
        
def main():
    """Run the backup GUI"""
    app = BackupGUI()
    app.mainloop()
    
if __name__ == "__main__":
    main()
