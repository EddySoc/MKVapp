#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     11/08/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from decorators.decorators import menu_tag
import os
import subprocess
import shutil
import re
import json
from pathlib import Path
from utils.text_helpers import tb_update

print("🎬 Loading videos/vids_mgr.py - registering Remove All Subs")

@menu_tag(label="Play Video", icon="▶️", group="videos")
def play_video():
    """Play selected video file with configured video player"""
    from shared_data import get_shared
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    if not selected:
        from utils import update_tbinfo
        update_tbinfo("⚠️ No file selected for this action.", "geel")
        print("⚠️ No video file selected")
        return
    
    video_path = selected[0]
    # Controleer of het een SRT-bestand is
    if video_path.lower().endswith('.srt'):
        from utils import update_tbinfo
        update_tbinfo(f"⚠️ Error: You tried to play an SRT file as video: '{os.path.basename(video_path)}'. Please select a valid video file.", "geel")
        return

    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    # Get video player path from config
    try:
        config_path = os.path.join("Settings", "tools_cfg.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                player_path = config.get("videoplayer_path", "")
                
                if not player_path:
                    print("❌ No video player configured. Please set the video player path in Settings.")
                    return
                
                if not os.path.exists(player_path):
                    print(f"❌ Video player not found at: {player_path}")
                    return
                
                # Start everything in a background thread immediately
                import threading
                
                def launch_player():
                    """Launch player in background"""
                    # Launch video player
                    process = subprocess.Popen([player_path, video_path], shell=False)
                    
                    # Wait for player to close
                    process.wait()
                    
                    # Bring app to front when done
                    s.app.after(0, lambda: (s.app.lift(), s.app.focus_force()))
                
                # Start immediately and return (menu can close)
                thread = threading.Thread(target=launch_player, daemon=True)
                thread.start()
                
                message = f"▶️ Playing: {os.path.basename(video_path)}"
                print(message)
                from utils.text_helpers import update_tb
                update_tb('tb_info', message)
        else:
            print("❌ tools_cfg.json not found. Please configure video player in Settings.")
    except Exception as e:
        print(f"❌ Error reading config: {e}")

def get_tool_path(tool_name):
    """Get tool executable path from config or PATH"""
    # First check if it's in PATH
    if shutil.which(tool_name):
        return tool_name
    
    # Check config file for custom path
    try:
        config_path = os.path.join("Settings", "tools_cfg.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                
                # Map tool names to config keys
                config_key_map = {
                    "ffmpeg": "ffmpeg_path",
                    "ffprobe": "ffprobe_path",
                    "mkvextract": "mkvtoolnix_path"
                }
                
                config_key = config_key_map.get(tool_name)
                if config_key:
                    tool_path = config.get(config_key, "")
                    
                    if tool_path:
                        # For mkvextract, it's in a directory
                        if tool_name == "mkvextract":
                            tool_exe = os.path.join(tool_path, "mkvextract.exe")
                            if os.path.exists(tool_exe):
                                return tool_exe
                        # For ffmpeg/ffprobe, check if it's a directory or full path
                        elif os.path.isdir(tool_path):
                            tool_exe = os.path.join(tool_path, f"{tool_name}.exe")
                            if os.path.exists(tool_exe):
                                return tool_exe
                        elif os.path.exists(tool_path):
                            return tool_path
    except Exception as e:
        print(f"⚠️ Error reading tools config: {e}")
    
    return None

def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe"""
    ffprobe_path = get_tool_path("ffprobe")
    if not ffprobe_path:
        return None
    
    cmd = [
        ffprobe_path,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except:
        pass
    return None

def parse_ffmpeg_progress(line):
    """Parse ffmpeg progress line to extract current time in seconds"""
    # ffmpeg outputs: time=00:01:23.45
    match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
    if match:
        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return None

@menu_tag(label="Remove All Subs", icon="🗑️", group="videos")
def remove_all_subtitles():
    """Remove all embedded subtitles from selected video files."""
    from shared_data import get_shared
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    if not selected:
        from utils import update_tbinfo
        update_tbinfo("⚠️ No file selected for this action.", "geel")
        print("⚠️ No files selected.")
        return
    
    # Check if ffmpeg is available
    ffmpeg_path = get_tool_path("ffmpeg")
    if not ffmpeg_path:
        from utils import log_error
        log_error("❌ ffmpeg not found. Please install ffmpeg or set path in Settings/tools_cfg.json")
        return
    
    video_exts = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
    
    from utils.text_helpers import tb_update
    tb_update('tb_info', f"🗑️ Remove All Subs - {len(selected)} file(s)", "normal")
    
    for idx, video_path in enumerate(selected):
        # Add dotted line between files (not before first)
        if idx > 0:
            tb_update('tb_info', "· " * 25, "normal")
        ext = os.path.splitext(video_path)[1].lower()
        if ext == '.srt':
            from utils import update_tbinfo
            update_tbinfo(f"⚠️ Error: You tried to use an SRT file for a video action: '{os.path.basename(video_path)}'. Please select a valid video file.", "geel")
            continue
        if ext not in video_exts:
            print(f"⏭️ Skipping non-video: {os.path.basename(video_path)}")
            tb_update('tb_info', f"⏭️ Skipping: {os.path.basename(video_path)}", "normal")
            continue
        
        # Create output filename with _nosubs suffix
        dir_name = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(dir_name, f"{base_name}_nosubs{ext}")
        
        print(f"🎬 Removing subtitles from: {os.path.basename(video_path)}")
        tb_update('tb_info', f"🎬 Processing: {os.path.basename(video_path)}", "normal")
        print(f"📂 Input: {video_path}")
        print(f"📂 Output: {output_path}")
        
        # Use ffmpeg to copy video without subtitle tracks
        # -map 0 copies all streams, -map -0:s removes all subtitle streams
        cmd = [
            ffmpeg_path, "-i", video_path,
            "-map", "0", "-map", "-0:s",
            "-c", "copy",
            "-y",  # Overwrite output file if exists
            output_path
        ]
        
        print(f"🔧 Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ FFmpeg failed with return code {result.returncode}")
                print(f"stderr: {result.stderr}")
                tb_update('tb_info', f"❌ FFmpeg error on {os.path.basename(video_path)}", "normal")
                if os.path.exists(output_path):
                    os.remove(output_path)
                continue
            
            print(f"✅ FFmpeg completed successfully")
            
            # Check if output file was created
            if not os.path.exists(output_path):
                print(f"❌ Output file was not created: {output_path}")
                tb_update('tb_info', f"❌ Output not created for {os.path.basename(video_path)}", "normal")
                continue
            
            # Replace original file with the new one
            print(f"🔄 Replacing original with no-subs version...")
            os.remove(video_path)
            os.rename(output_path, video_path)
            
            print(f"✅ Removed subtitles: {os.path.basename(video_path)}")
            tb_update('tb_info', f"✅ Removed subs: {os.path.basename(video_path)}", "normal")
            
        except Exception as e:
            print(f"❌ Error processing {os.path.basename(video_path)}: {e}")
            tb_update('tb_info', f"❌ Error: {str(e)}", "normal")
            if os.path.exists(output_path):
                os.remove(output_path)
    
    tb_update('tb_info', "· " * 25, "normal")
    tb_update('tb_info', "✅ Remove All Subs complete", "normal")
    tb_update('tb_info', "─" * 50, "normal")

@menu_tag(label="Transform -> MKV", group="videos")
def transform_2_mkv():
    """Transform video files to MKV format"""
    from shared_data import get_shared
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    if not selected:
        from utils import update_tbinfo
        update_tbinfo("⚠️ No file selected for this action.", "geel")
        from utils import log_error
        log_error("⚠️ No files selected.")
        return
    
    # Check if ffmpeg is available
    ffmpeg_path = get_tool_path("ffmpeg")
    if not ffmpeg_path:
        from utils import log_error
        log_error("❌ ffmpeg not found. Please install ffmpeg or set path in Settings/tools_cfg.json")
        return
    
    # Setup progress bar
    total = len(selected)
    s.bottomrow_label.label.grid_remove()
    s.bottomrow_label.progress.grid()
    s.bottomrow_label.progress_label.grid()  # Show percentage label
    s.bottomrow_label.progress.configure(mode="determinate")
    s.bottomrow_label.update_progress(0, "0%")
    
    tb_update('tb_info', f"🎬 Transform to MKV - {total} file(s)", "normal")
    
    video_exts = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    
    for idx, video_path in enumerate(selected):
        # Add dotted line between files (not before first)
        if idx > 0:
            tb_update('tb_info', "· " * 25, "normal")
        # Update progress
        progress = idx / total
        s.bottomrow_label.update_progress(progress)
        s.app.update_idletasks()
        ext = os.path.splitext(video_path)[1].lower()
        if ext == '.srt':
            from utils import update_tbinfo
            update_tbinfo(f"⚠️ Error: You tried to use an SRT file for a video action: '{os.path.basename(video_path)}'. Please select a valid video file.", "geel")
            continue
        
        ext = os.path.splitext(video_path)[1].lower()
        
        # Skip if already MKV
        if ext == ".mkv":
            print(f"⏭️ Already MKV: {os.path.basename(video_path)}")
            continue
        
        # Skip non-video files
        if ext not in video_exts:
            print(f"⏭️ Skipping non-video: {os.path.basename(video_path)}")
            continue
        
        # Create output filename with .mkv extension
        dir_name = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(dir_name, f"{base_name}.mkv")
        
        print(f"🎬 Transforming to MKV: {os.path.basename(video_path)}")
        tb_update('tb_info', f"🎬 Transforming: {os.path.basename(video_path)}", "normal")
        
        # Get video duration for progress calculation
        duration = get_video_duration(video_path)
        
        # Use ffmpeg to convert to MKV (copy streams, no re-encoding)
        cmd = [
            ffmpeg_path, "-i", video_path,
            "-fflags", "+genpts",
            "-c:v", "copy",
            "-c:a", "copy",
            "-y",  # Overwrite output file if exists
            output_path
        ]
        
        try:
            # Run ffmpeg with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Read stderr line by line for progress
            for line in process.stderr:
                if duration:
                    current_time = parse_ffmpeg_progress(line)
                    if current_time:
                        file_progress = min(current_time / duration, 1.0)
                        overall_progress = (idx + file_progress) / total
                        s.bottomrow_label.update_progress(overall_progress)
                        s.app.update_idletasks()
            
            process.wait()
            
            if process.returncode != 0:
                print(f"❌ FFmpeg failed with return code {process.returncode}")
                tb_update('tb_info', f"❌ Failed: {os.path.basename(video_path)}", "normal")
                if os.path.exists(output_path):
                    os.remove(output_path)
                continue
            
            # Check if output file was created
            if not os.path.exists(output_path):
                print(f"❌ Output file was not created: {output_path}")
                tb_update('tb_info', f"❌ Output not created: {os.path.basename(video_path)}", "normal")
                continue
            
            # Replace original file with the new MKV
            print(f"🔄 Replacing original with MKV version...")
            os.remove(video_path)
            
            print(f"✅ Transformed to MKV: {base_name}.mkv")
            tb_update('tb_info', f"✅ Transformed: {base_name}.mkv", "normal")
            
        except Exception as e:
            print(f"❌ Error processing {os.path.basename(video_path)}: {e}")
            tb_update('tb_info', f"❌ Error: {os.path.basename(video_path)}", "normal")
            if os.path.exists(output_path):
                os.remove(output_path)
    
    # Complete progress bar
    s.bottomrow_label.update_progress(1.0, "100%")
    
    # Rescan directory to show new MKV files
    print("🔄 Refreshing file list...")
    tb_update('tb_info', "🔄 Refreshing file list...", "normal")
    
    try:
        # Get current directory from base_path or first selected file's directory
        if hasattr(s, 'base_path') and s.base_path:
            scan_path = s.base_path
        elif selected:
            scan_path = os.path.dirname(selected[0])
        else:
            print("⚠️ Cannot determine directory to rescan")
            s.bottomrow_label.progress.grid_remove()
            s.bottomrow_label.label.grid()
            return
        
        from utils.scan_helpers import fast_scandir, update_lb
        fast_scandir(s.app, scan_path)
        update_lb(s.app)
        
        print("✅ Transform to MKV completed - file list refreshed")
        tb_update('tb_info', "· " * 25, "normal")
        tb_update('tb_info', "✅ Transform to MKV complete - list refreshed", "normal")
        tb_update('tb_info', "─" * 50, "normal")
        
    except Exception as e:
        print(f"⚠️ Transform completed but refresh failed: {e}")
        tb_update('tb_info', "⚠️ Transform done - manual refresh needed", "normal")
    finally:
        # Restore label
        s.bottomrow_label.progress.grid_remove()
        s.bottomrow_label.label.grid()

@menu_tag(label="Embed Sub", group="videos")
def mkv_embed_sub():
    """Embed SRT subtitle into MKV file"""
    from shared_data import get_shared
    s = get_shared()
    
    # Close popup menu before action
    if hasattr(s, 'pop_menu') and s.pop_menu:
        try:
            s.pop_menu.unpost()
        except:
            pass
    
    # Force UI update to close menu
    if hasattr(s, 'app') and hasattr(s.app, 'update_idletasks'):
        s.app.update_idletasks()
    
    selected = s.app.lb_files.get_selected_file_paths()
    if not selected:
        from utils import update_tbinfo
        update_tbinfo("⚠️ No file selected for this action.", "geel")
        print("⚠️ No files selected.")
        return
    
    # Separate videos and subtitles from selection
    video_exts = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
    video_files = [f for f in selected if os.path.splitext(f)[1].lower() in video_exts]
    srt_files = [f for f in selected if f.lower().endswith('.srt')]
    
    if not video_files:
        tb_update('tb_info', "⚠️ No video files selected for embedding.", "geel")
        return
    
    # Check if ffmpeg is available
    ffmpeg_path = get_tool_path("ffmpeg")
    if not ffmpeg_path:
        from utils import log_error
        log_error("❌ ffmpeg not found. Please install ffmpeg or set path in Settings/tools_cfg.json")
        return
    
    # Setup progress bar
    total = len(video_files)
    s.bottomrow_label.label.grid_remove()
    s.bottomrow_label.progress.grid()
    s.bottomrow_label.progress_label.grid()  # Show percentage label
    s.bottomrow_label.progress.configure(mode="determinate")
    s.bottomrow_label.update_progress(0, "0%")
    
    tb_update('tb_info', f"📥 Embed Sub - {total} file(s)", "normal")
    
    # If user selected both video and SRT, try to match them explicitly
    explicit_srt = srt_files[0] if len(srt_files) == 1 and len(video_files) == 1 else None
    
    for idx, video_path in enumerate(video_files):
        # Add dotted line between files (not before first)
        if idx > 0:
            tb_update('tb_info', "· " * 25, "normal")
        # Update progress
        progress = idx / total
        s.bottomrow_label.update_progress(progress)
        s.app.update_idletasks()
        
        dir_name = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # Use explicitly selected SRT if available, otherwise search
        srt_path = explicit_srt
        
        if not srt_path:
            # Try common subtitle patterns
            srt_patterns = [
                os.path.join(dir_name, f"{base_name}.srt"),
                os.path.join(dir_name, f"{base_name}.nl.srt"),
                os.path.join(dir_name, f"{base_name}.en.srt"),
                os.path.join(dir_name, f"{base_name}-dut.srt"),
                os.path.join(dir_name, f"{base_name}-nl.srt"),
                os.path.join(dir_name, f"{base_name}-eng.srt"),
                os.path.join(dir_name, f"{base_name}.eng.srt"),
                os.path.join(dir_name, f"{base_name}.dut.srt"),
            ]
            
            for pattern in srt_patterns:
                if os.path.exists(pattern):
                    srt_path = pattern
                    break
        
        # If no exact match, search directory for any SRT with similar name
        if not srt_path:
            try:
                for file in os.listdir(dir_name):
                    if file.endswith('.srt') and file.startswith(base_name):
                        srt_path = os.path.join(dir_name, file)
                        print(f"💡 Found subtitle: {file}")
                        break
            except Exception as e:
                print(f"⚠️ Error searching for subtitles: {e}")
        
        if not srt_path:
            print(f"⚠️ No SRT file found for: {os.path.basename(video_path)}")
            tb_update('tb_info', f"⚠️ No SRT for: {os.path.basename(video_path)}", "normal")
            continue
        
        # Create output filename
        output_path = os.path.join(dir_name, f"{base_name}_embed.mkv")
        
        print(f"🎬 Embedding subtitle: {os.path.basename(srt_path)} → {os.path.basename(video_path)}")
        tb_update('tb_info', f"🎬 Embedding: {os.path.basename(video_path)}", "normal")
        
        # Detect subtitle language from filename
        srt_basename = os.path.basename(srt_path).lower()
        if '.nl.' in srt_basename or '.dut.' in srt_basename:
            lang_code = "dut"
        elif '.en.' in srt_basename or '.eng.' in srt_basename:
            lang_code = "eng"
        elif '.fr.' in srt_basename or '.fra.' in srt_basename:
            lang_code = "fre"
        elif '.de.' in srt_basename or '.ger.' in srt_basename:
            lang_code = "ger"
        else:
            # Default to Dutch if no language detected
            lang_code = "dut"
        
        print(f"📝 Detected subtitle language: {lang_code}")
        
        # Get video duration for progress calculation
        duration = get_video_duration(video_path)
        
        # Use ffmpeg to embed subtitle with proper mapping
        cmd = [
            ffmpeg_path, 
            "-i", video_path,
            "-i", srt_path,
            "-map", "0",        # Map everything from first input
            "-map", "-0:s",     # Except subtitle streams (remove old subs)
            "-map", "1:0",      # Map subtitle from second input (SRT file)
            "-c:v", "copy",
            "-c:a", "copy",
            "-c:s", "srt",
            f"-metadata:s:s:0", f"language={lang_code}",
            "-disposition:s:0", "default",
            "-y",
            output_path
        ]
        
        try:
            print(f"🔧 Running ffmpeg command: {' '.join(cmd)}")
            
            # Run ffmpeg with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Capture all stderr output for error reporting
            stderr_output = []
            
            # Read stderr line by line for progress
            for line in process.stderr:
                stderr_output.append(line)
                if duration:
                    current_time = parse_ffmpeg_progress(line)
                    if current_time:
                        file_progress = min(current_time / duration, 1.0)
                        overall_progress = (idx + file_progress) / total
                        s.bottomrow_label.update_progress(overall_progress)
                        s.app.update_idletasks()
            
            process.wait()
            
            if process.returncode != 0:
                error_msg = ''.join(stderr_output[-10:])  # Last 10 lines
                print(f"❌ FFmpeg failed with return code {process.returncode}")
                print(f"Error output:\n{error_msg}")
                tb_update('tb_info', f"❌ Failed: {os.path.basename(video_path)} - Check console for details", "rood")
                if os.path.exists(output_path):
                    os.remove(output_path)
                continue
            
            if not os.path.exists(output_path):
                print(f"❌ Output file was not created: {output_path}")
                tb_update('tb_info', f"❌ Output not created", "normal")
                continue
            
            print(f"✅ Embedded subtitle: {base_name}_embed.mkv")
            tb_update('tb_info', f"✅ Created: {base_name}_embed.mkv", "normal")
            
        except Exception as e:
            print(f"❌ Error processing {os.path.basename(video_path)}: {e}")
            tb_update('tb_info', f"❌ Error: {os.path.basename(video_path)}", "normal")
            if os.path.exists(output_path):
                os.remove(output_path)
    
    # Complete progress bar
    s.bottomrow_label.update_progress(1.0, "100%")
    
    print("✅ Embed subtitles completed")
    tb_update('tb_info', "· " * 25, "normal")
    tb_update('tb_info', "✅ Embed subtitles completed", "normal")
    tb_update('tb_info', "─" * 50, "normal")
    
    # Refresh the listbox to show new embedded files
    from utils.scan_helpers import reload
    reload(s.app)
    
    # Restore label
    s.bottomrow_label.progress.grid_remove()
    s.bottomrow_label.label.grid()

@menu_tag(label="MKV -> 8 Bit HEVC", group="videos")
def mkv_2_8bitHEVC():
    """Convert 10-bit/12-bit HEVC to 8-bit HEVC"""
    from shared_data import get_shared
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    if not selected:
        from utils import update_tbinfo
        update_tbinfo("⚠️ No files selected.", "rood")
        print("⚠️ No files selected.")
        return
    
    # Setup progress bar
    total = len(selected)
    s.bottomrow_label.label.grid_remove()
    s.bottomrow_label.progress.grid()
    s.bottomrow_label.progress_label.grid()  # Show percentage label
    s.bottomrow_label.progress.configure(mode="determinate")
    s.bottomrow_label.update_progress(0, "0%")
    
    tb_update('tb_info', f"🎞️ MKV to 8-bit HEVC - {total} file(s)", "normal")
    
    video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv'}
    
    for idx, video_path in enumerate(selected):
        # Add dotted line between files (not before first)
        if idx > 0:
            tb_update('tb_info', "· " * 25, "normal")
        # Update progress
        progress = idx / total
        s.bottomrow_label.update_progress(progress)
        s.app.update_idletasks()
        ext = os.path.splitext(video_path)[1].lower()
        
        # Skip non-video files
        if ext not in video_exts:
            print(f"⏭️ Skipping non-video: {os.path.basename(video_path)}")
            continue
        
        # Check current pixel format with ffprobe
        print(f"🔍 Checking pixel format: {os.path.basename(video_path)}")
        check_cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=pix_fmt",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        
        try:
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pix_fmt = result.stdout.strip()
                print(f"  📊 Current pixel format: {pix_fmt}")
                
                # Check if already 8-bit (yuv420p is 8-bit)
                if pix_fmt == "yuv420p":
                    print(f"  ✅ Already 8-bit, skipping: {os.path.basename(video_path)}")
                    tb_update('tb_info', f"✅ Already 8-bit: {os.path.basename(video_path)}", "normal")
                    continue
                else:
                    print(f"  ⚡ Needs conversion from {pix_fmt} to 8-bit")
            else:
                print(f"  ⚠️ Could not determine pixel format, will attempt conversion")
        except Exception as e:
            print(f"  ⚠️ Error checking format: {e}, will attempt conversion")
        
        # Create output filename
        dir_name = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(dir_name, f"{base_name}_8bit.mkv")
        
        print(f"🎬 Converting to 8-bit HEVC: {os.path.basename(video_path)}")
        tb_update('tb_info', f"🎬 Converting: {os.path.basename(video_path)}", "normal")
        
        # Get video duration for progress calculation
        duration = get_video_duration(video_path)
        
        # Get max resolution setting from config
        from shared_data import shared
        max_res = shared.config.get("persistent_cfg", {}).get("Max_Resolution", "1080p")
        
        # Get current video resolution
        res_cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0",
            video_path
        ]
        
        scale_filter = None
        try:
            result = subprocess.run(res_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                width, height = map(int, result.stdout.strip().split(','))
                print(f"  📐 Current resolution: {width}x{height}")
                
                # Determine target height based on config
                target_height = 1080 if max_res == "1080p" else 720 if max_res == "720p" else 1080
                
                # Only scale down if current resolution is higher
                if height > target_height:
                    scale_filter = f"scale=-2:{target_height}"
                    print(f"  ⬇️ Scaling down to {target_height}p")
                else:
                    print(f"  ✅ Resolution already at or below {target_height}p")
        except Exception as e:
            print(f"  ⚠️ Could not detect resolution: {e}")
        
        # Build ffmpeg command with optional scaling
        cmd = ["ffmpeg", "-i", video_path]
        
        # Add video filter if scaling is needed
        if scale_filter:
            cmd.extend(["-vf", scale_filter])
        
        cmd.extend([
            "-c:v", "libx265",
            "-pix_fmt", "yuv420p",  # Force 8-bit
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "copy",
            "-c:s", "copy",
            "-y",
            output_path
        ])
        
        try:
            print("⚠️ This may take a while (re-encoding video)...")
            
            # Run ffmpeg with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Read stderr line by line for progress
            for line in process.stderr:
                if duration:
                    current_time = parse_ffmpeg_progress(line)
                    if current_time:
                        file_progress = min(current_time / duration, 1.0)
                        overall_progress = (idx + file_progress) / total
                        s.bottomrow_label.update_progress(overall_progress)
                        s.app.update_idletasks()
            
            process.wait()
            
            if process.returncode != 0:
                print(f"❌ FFmpeg failed with return code {process.returncode}")
                tb_update('tb_info', f"❌ Failed: {os.path.basename(video_path)}", "normal")
                if os.path.exists(output_path):
                    os.remove(output_path)
                continue
            
            if not os.path.exists(output_path):
                print(f"❌ Output file was not created: {output_path}")
                tb_update('tb_info', f"❌ Output not created", "normal")
                continue
            
            print(f"✅ Converted to 8-bit: {base_name}_8bit.mkv")
            tb_update('tb_info', f"✅ Created: {base_name}_8bit.mkv", "normal")
            
        except Exception as e:
            print(f"❌ Error processing {os.path.basename(video_path)}: {e}")
            tb_update('tb_info', f"❌ Error: {os.path.basename(video_path)}", "normal")
            if os.path.exists(output_path):
                os.remove(output_path)
    
    # Complete progress bar
    s.bottomrow_label.update_progress(1.0, "100%")
    
    print("✅ 8-bit HEVC conversion completed")
    tb_update('tb_info', "· " * 25, "normal")
    tb_update('tb_info', "✅ MKV to 8-bit HEVC complete", "normal")
    tb_update('tb_info', "─" * 50, "normal")
    
    # Refresh the listbox to show new 8bit files
    from utils.scan_helpers import reload
    reload(s.app)
    
    # Restore label
    s.bottomrow_label.progress.grid_remove()
    s.bottomrow_label.label.grid()

@menu_tag(label="Check Subs Language", group="videos")
def mkv_check_lang():
    """Check MKV embedded subtitle language"""
    from shared_data import get_shared
    s = get_shared()
    
    selected = s.app.lb_files.get_selected_file_paths()
    if not selected:
        from utils import update_tbinfo
        update_tbinfo("⚠️ No files selected.", "rood")
        print("⚠️ No files selected.")
        return
    
    mkv_exts = {".mkv"}
    total_subs_found = 0
    
    tb_update('tb_info', f"🔍 Check Subs Language - {len(selected)} file(s)", "normal")
    
    for idx, video_path in enumerate(selected):
        # Add dotted line between files (not before first)
        if idx > 0:
            tb_update('tb_info', "· " * 25, "normal")
            
        ext = os.path.splitext(video_path)[1].lower()
        
        # Only check MKV files
        if ext not in mkv_exts:
            print(f"⏭️ Skipping non-MKV: {os.path.basename(video_path)}")
            continue
        
        print(f"\n🔍 Checking: {os.path.basename(video_path)}")
        tb_update('tb_info', f"🔍 Checking: {os.path.basename(video_path)}", "normal")
        
        # Use ffprobe to check streams
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            video_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ ffprobe failed with return code {result.returncode}")
                tb_update('tb_info', f"❌ Failed: {os.path.basename(video_path)}", "normal")
                continue
            
            import json
            data = json.loads(result.stdout)
            
            # Find subtitle streams
            subtitle_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'subtitle']
            
            if not subtitle_streams:
                print("  ℹ️ No subtitle streams found")
                tb_update('tb_info', f"  ℹ️ No subs in: {os.path.basename(video_path)}", "normal")
            else:
                total_subs_found += len(subtitle_streams)
                print(f"  📝 Found {len(subtitle_streams)} subtitle stream(s):")
                for idx, stream in enumerate(subtitle_streams):
                    lang = stream.get('tags', {}).get('language', 'und')
                    codec = stream.get('codec_name', 'unknown')
                    title = stream.get('tags', {}).get('title', '')
                    info = f"    [{idx}] Language: {lang}, Codec: {codec}"
                    if title:
                        info += f", Title: {title}"
                    print(info)
                    tb_update('tb_info', info, "normal")
                
                tb_update('tb_info', "─" * 50, "normal")
            
        except Exception as e:
            print(f"❌ Error checking {os.path.basename(video_path)}: {e}")
            tb_update('tb_info', f"❌ Error: {os.path.basename(video_path)}", "normal")
    
    tb_update('tb_info', "· " * 25, "normal")
    if total_subs_found == 0:
        print("\n⚠️ No internal subs found")
        tb_update('tb_info', "⚠️ No internal subs found", "normal")
    else:
        print("\n✅ Language check completed")
        tb_update('tb_info', "✅ Check Subs Language complete", "normal")
    tb_update('tb_info', "─" * 50, "normal")

