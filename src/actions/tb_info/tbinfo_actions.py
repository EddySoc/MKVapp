#-------------------------------------------------------------------------------
# Name:        tbinfo_actions.py
# Purpose:     Actions for tb_info textbox
#
# Author:      EddyS
#
# Created:     14/01/2026
# Copyright:   (c) EddyS 2026
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import os
from decorators.decorators import menu_tag
from utils.text_helpers import tb_update

def show_video_subtitle_info():
    """Toon info in tb_info als er een video geselecteerd is en een keuze uit het subtitles-menu is gemaakt, vooral als de keuze 'all' is."""
    from shared_data import get_shared
    s = get_shared()

    # Controleer of er een video geselecteerd is
    selected_videos = []
    if hasattr(s.app, "lb_files"):
        selected_videos = [f for f in s.app.lb_files.get_selected_file_paths() if f.lower().endswith((".mp4", ".mkv", ".avi"))]

    if not selected_videos:
        tb_update('tb_info', "⚠️ Geen video geselecteerd.", "geel")
        return

    # Controleer keuze uit extensie-segment (Videos / Subtitles / All)
    subtitle_choice = None
    if hasattr(s, "segbut_var") and s.segbut_var is not None:
        subtitle_choice = s.segbut_var.get() if hasattr(s.segbut_var, 'get') else s.segbut_var

    if not subtitle_choice:
        tb_update('tb_info', "⚠️ Geen keuze uit subtitles-menu.", "geel")
        return

    # Toon info, vooral als keuze 'all' is
    tb_update('tb_info', f"🎬 Geselecteerde video(s): {', '.join([os.path.basename(v) for v in selected_videos])}", "normal")
    tb_update('tb_info', f"🗂️ Subtitles-menu keuze: {subtitle_choice}", "normal")
    # Controleer op verkeerde combinaties
    verkeerde_combinaties = ["all", "none", "invalid", "onjuist", "fout"]
    if str(subtitle_choice).lower() in verkeerde_combinaties:
        tb_update('tb_info', f"⚠️ Waarschuwing: De keuze '{subtitle_choice}' bij subtitles in combinatie met een geselecteerde video is mogelijk onjuist.", "geel")


@menu_tag(label="Clear Textbox", icon="🧹", group=[])
def clear_tb_info():
    """Clear the tb_info textbox"""
    from shared_data import get_shared
    s = get_shared()
    
    if hasattr(s, 'app') and hasattr(s.app, 'tb_info'):
        tb = s.app.tb_info
        print(f"🔍 Before clear: '{tb.textbox.get('1.0', 'end')[:50]}'")
        print(f"🔍 State before: {tb.textbox.cget('state')}")
        
        tb.textbox.configure(state="normal")
        tb.textbox.delete("1.0", "end")
        tb.textbox.update_idletasks()
        
        print(f"🔍 After clear: '{tb.textbox.get('1.0', 'end')}'")
        print(f"🔍 State after: {tb.textbox.cget('state')}")
        print("✅ Cleared tb_info textbox")
    else:
        print("⚠️ tb_info textbox not found")
