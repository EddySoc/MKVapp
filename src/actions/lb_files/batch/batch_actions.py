#-------------------------------------------------------------------------------
# Name:        batch_actions.py
# Purpose:     "Run Batch" menu action — executes the configured batch queue
#              on the currently selected files in lb_files.
#
# Author:      EddyS
# Created:     08/03/2026
#-------------------------------------------------------------------------------
from decorators.decorators import menu_tag
import os

# Time (ms) between batch steps — gives async thread-based actions time to settle.
# Increase this if heavy conversions (e.g. HEVC) overlap with the next step.
# How long (ms) to wait between checking s.batch_step_done during polling.
POLL_INTERVAL_MS = 500

# Action labels that produce new SRT files — after these, find newest SRT per video
_PRODUCES_SRT = {"Extract Subs", "Speech to SRT (Whisper)", "Translate", "Sync Srt"}
# Action labels that accept only SRT (NOT video) as input
_SRT_ONLY_LABELS = {"Clean & Fix", "Translate Sub", "Check SRT Language", "Resync Folder"}
# Video extensions used to identify original video files
_VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}


def _find_newest_srt_per_video(video_paths):
    """
    For each video, return the single newest .srt file in the same folder
    whose basename starts with the video's base name (sorted by mtime).
    Skips files smaller than 100 bytes (empty/partial output from failed steps).
    """
    result = []
    for vp in video_paths:
        directory = os.path.dirname(vp)
        base = os.path.splitext(os.path.basename(vp))[0].lower()
        try:
            candidates = [
                os.path.join(directory, f)
                for f in os.listdir(directory)
                if f.lower().endswith('.srt') and f.lower().startswith(base)
                and os.path.isfile(os.path.join(directory, f))
                and os.path.getsize(os.path.join(directory, f)) >= 100  # skip empty/partial
            ]
            if candidates:
                result.append(max(candidates, key=os.path.getmtime))
        except Exception:
            pass
    return result



def _restore_selection(lb, paths):
    """Re-select the given file paths in lb_files after a list refresh."""
    if not hasattr(lb, 'listbox') or not hasattr(lb, 'current_items'):
        return 0
    # Deselect all currently selected items
    for idx in list(lb.listbox.curselection()):
        try:
            lb.listbox.deactivate(idx)
        except Exception:
            pass
    # Re-select items whose full path is in the requested set
    path_set = set(paths)
    found = 0
    for i, item_path in enumerate(lb.current_items):
        if item_path in path_set:
            try:
                lb.listbox.activate(i)
                found += 1
            except Exception:
                pass
    return found


@menu_tag(label="Run Batch", icon="⚙️", group="batch")
def run_batch():
    """Run all actions in the batch queue on the selected lb_files entries."""
    from shared_data import get_shared
    from menus.menu_registry import global_menu_registry
    from utils import update_tbinfo

    s = get_shared()

    # Start a fresh batch run state
    s.batch_cancel_requested = False
    s.batch_running = True
    s.batch_current_label = ""

    if not s.batch_queue:
        update_tbinfo(
            "⚠️ Batch wachtrij is leeg. "
            "Voeg eerst acties toe via het Batch-tabblad.",
            "geel"
        )
        return

    original_paths = s.app.lb_files.get_selected_file_paths()
    if not original_paths:
        update_tbinfo("⚠️ Geen bestanden geselecteerd in lb_files.", "geel")
        return

    queue_snapshot = list(s.batch_queue)
    total = len(queue_snapshot)
    update_tbinfo(
        f"🚀 Batch gestart: {total} actie(s) op {len(original_paths)} bestand(en).",
        "groen"
    )
    print(f"[BATCH] Queue ({total} stap(pen)): {queue_snapshot}")

    # Mutable box so nested closures can update the active selection
    active_paths = [list(original_paths)]  # active_paths[0] = current selection

    def _finish_cancelled():
        s.batch_running = False
        s.batch_current_label = ""
        s.batch_step_done = True
        update_tbinfo("⏹️ Batch gestopt door gebruiker.", "geel")

    def _finish_done():
        s.batch_running = False
        s.batch_current_label = ""
        update_tbinfo(f"✅ Batch klaar ({total} stap(pen) uitgevoerd).", "groen")

    def execute_step(step_idx):
        if s.batch_cancel_requested:
            _finish_cancelled()
            return

        if step_idx >= total:
            _finish_done()
            return

        label = queue_snapshot[step_idx]
        s.batch_current_label = label
        current = active_paths[0]

        # Restore selection — counteracts any file-list refresh that clears it
        restored = _restore_selection(s.app.lb_files, current)
        if restored == 0:
            # Bestanden staan mogelijk nog niet in de listbox (bv. _nosubs.mkv net aangemaakt)
            # Forceer een reload en probeer één keer opnieuw
            from utils.scan_helpers import reload as _reload
            def _retry_after_reload(idx=step_idx):
                _reload(s.app)
                s.app.after(500, lambda: _execute_or_stop(idx))
            def _execute_or_stop(idx):
                if _restore_selection(s.app.lb_files, active_paths[0]) == 0:
                    update_tbinfo(
                        f"  ⚠️ [{idx+1}/{total}] Bestanden niet meer aanwezig in de lijst — batch gestopt.",
                        "geel"
                    )
                    return
                _run_step(idx)
            s.app.after(0, lambda: _retry_after_reload(step_idx))
            return

        _run_step(step_idx)

    def _run_step(step_idx):
        label = queue_snapshot[step_idx]
        s.batch_current_label = label

        entry = global_menu_registry.get(label)
        if not entry or not callable(entry.get("func")):
            update_tbinfo(
                f"  ⚠️ [{step_idx+1}/{total}] Actie '{label}' niet gevonden — overgeslagen.",
                "geel"
            )
            s.app.after(100, lambda idx=step_idx: execute_step(idx + 1))
            return

        update_tbinfo(f"  ▶ [{step_idx+1}/{total}] {label} …", "info")

        # Mark step as done before calling — async actions will flip it to False
        s.batch_step_done = True
        try:
            entry["func"]()
        except Exception as exc:
            update_tbinfo(f"  ❌ [{step_idx+1}/{total}] Fout bij '{label}': {exc}", "rood")
            s.batch_step_done = True  # ensure we don't get stuck

        # Wait for the done bit, then continue to next step
        s.app.after(POLL_INTERVAL_MS, lambda idx=step_idx, lbl=label: _wait_done(idx, lbl))


    def _wait_done(step_idx, completed_label):
        """Poll until async action signals completion, dan advance to next step."""
        if s.batch_cancel_requested:
            _finish_cancelled()
            return

        if not s.batch_step_done:
            s.app.after(POLL_INTERVAL_MS, lambda: _wait_done(step_idx, completed_label))
            return

        import glob
        def rename_to_orig_and_short(new_file, orig_file):
            import os
            if not os.path.exists(orig_file):
                return new_file
            orig_orig = orig_file + ".orig"
            if not os.path.exists(orig_orig):
                os.rename(orig_file, orig_orig)
            os.replace(new_file, orig_file)
            return orig_file

        if step_idx + 1 < total:
            next_label = queue_snapshot[step_idx + 1]
            current_sel = active_paths[0]
            video_paths = [p for p in current_sel if os.path.splitext(p)[1].lower() in _VIDEO_EXTS]

            # Als huidige selectie geen video's bevat (bv. na een SRT-only stap),
            # val terug op de originele video's voor stappen die video's nodig hebben
            if not video_paths and next_label not in _SRT_ONLY_LABELS:
                video_paths = [p for p in original_paths if os.path.splitext(p)[1].lower() in _VIDEO_EXTS]

            # Scan mappen voor nieuwste SRT's
            all_dirs = set(os.path.dirname(p) for p in current_sel) | set(os.path.dirname(p) for p in video_paths)
            found_srts = set()
            for d in all_dirs:
                try:
                    for f in os.listdir(d):
                        fp = os.path.join(d, f)
                        if f.lower().endswith('.srt') and os.path.getsize(fp) >= 100:
                            found_srts.add(fp)
                except Exception:
                    pass

            # Per geselecteerde video: nieuwste video-variant (bv. na Remove All Subs → in-place vervanging)
            newest_videos = []
            for v in video_paths:
                d = os.path.dirname(v)
                base = os.path.splitext(os.path.basename(v))[0].lower()
                try:
                    candidates = [
                        os.path.join(d, f) for f in os.listdir(d)
                        if os.path.splitext(f)[1].lower() in _VIDEO_EXTS
                        and os.path.splitext(f)[0].lower().startswith(base)
                        and os.path.join(d, f) != v
                    ]
                except Exception:
                    candidates = []
                if candidates:
                    newest_videos.append(max(candidates, key=os.path.getmtime))
                else:
                    newest_videos.append(v)  # origineel in-place vervangen

            # Per video: nieuwste bijbehorende SRT
            newest_srts = []
            seen_srts = set()
            for v in video_paths:
                base = os.path.splitext(os.path.basename(v))[0].lower()
                candidates = [s for s in found_srts if os.path.basename(s).lower().startswith(base)]
                if candidates:
                    newest = max(candidates, key=os.path.getmtime)
                    if newest not in seen_srts:
                        newest_srts.append(newest)
                        seen_srts.add(newest)

            # Als current_sel alleen SRT's bevat: nieuwste variant per geselecteerde SRT
            srt_paths = [p for p in current_sel if p.lower().endswith('.srt')]
            if not video_paths and srt_paths:
                import re as _re
                for srt in srt_paths:
                    raw = os.path.splitext(os.path.basename(srt))[0].lower()
                    base = _re.sub(r'(\.(en|nl|fr|de|es|it|pt|ja|zh|und|eng|dut|fre|ger|spa|ita|por|sync|tmp|clean))+$', '', raw)
                    candidates = [s for s in found_srts if os.path.basename(s).lower().startswith(base)]
                    if candidates:
                        newest = max(candidates, key=os.path.getmtime)
                        if newest not in seen_srts:
                            newest_srts.append(newest)
                            seen_srts.add(newest)

            # Nieuwe selectie afhankelijk van volgende stap
            if next_label in _SRT_ONLY_LABELS:
                new_sel = newest_srts
                sel_desc = f"{len(new_sel)} SRT('s)"
            else:
                new_sel = newest_videos + newest_srts
                sel_desc = f"{len(newest_videos)} video('s) + {len(newest_srts)} SRT('s)"

            if new_sel:
                active_paths[0] = new_sel
                _restore_selection(s.app.lb_files, new_sel)
                update_tbinfo(f"  \U0001f504 Selectie voor '{next_label}': {sel_desc}.", "info")
            else:
                update_tbinfo(f"  \u26a0\ufe0f Geen SRT of video gevonden na '{completed_label}' — selectie ongewijzigd.", "geel")

        execute_step(step_idx + 1)

    execute_step(0)


@menu_tag(label="Stop Batch", icon="⏹️", group="batch")
def stop_batch():
    """Stop the currently running batch without closing the app."""
    from shared_data import get_shared
    from utils import update_tbinfo

    s = get_shared()

    if not getattr(s, "batch_running", False):
        update_tbinfo("ℹ️ Er draait geen batch.", "geel")
        return

    s.batch_cancel_requested = True
    s.batch_step_done = True  # Release polling waits immediately.
    stopped = False
    try:
        stopped = s.stop_active_process()
    except Exception:
        stopped = False

    if stopped:
        update_tbinfo(f"⏹️ Batch stop aangevraagd tijdens '{s.batch_current_label}' (subprocess gestopt).", "geel")
    else:
        update_tbinfo(f"⏹️ Batch stop aangevraagd tijdens '{s.batch_current_label}'.", "geel")
