# Speech-to-SRT using faster-whisper
# Runs transcription in a subprocess to isolate Intel DLL crashes from the main app.

import os
import sys
import subprocess
import threading
from decorators.decorators import menu_tag
from utils.text_helpers import tb_update

_WORKER = os.path.join(os.path.dirname(__file__), "_whisper_worker.py")


@menu_tag(label="Speech to SRT (Whisper)", group="videos")
def speech_to_srt():
    """Transcribe selected video(s) to SRT using faster-whisper (subprocess)."""
    from shared_data import get_shared
    from config.smart_config_manager import get_config_manager

    s = get_shared()
    selected = s.app.lb_files.get_selected_file_paths()

    video_exts = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v", ".flac", ".mp3", ".wav", ".m4a"}
    video_files = [f for f in selected if os.path.splitext(f)[1].lower() in video_exts]

    if not video_files:
        tb_update('tb_info', "⚠️ Geen video/audio bestanden geselecteerd.", "geel")
        return

    try:
        cfg = get_config_manager()
        model_size = cfg.get("persistent_cfg", "WhisperModel", "medium") or "medium"
        device     = cfg.get("persistent_cfg", "WhisperDevice", "cuda") or "cuda"
        language   = cfg.get("persistent_cfg", "WhisperLanguage", "en") or "en"
        _lang_map  = {"eng": "en", "dut": "nl", "nld": "nl", "fre": "fr",
                      "fra": "fr", "ger": "de", "deu": "de", "spa": "es",
                      "ita": "it", "por": "pt"}
        language = _lang_map.get(language.strip().lower(), language.strip().lower())
        if language in ("", "auto", "none"):
            language = None
    except Exception:
        model_size = "medium"
        device     = "cuda"
        language   = None

    total = len(video_files)

    # Signal batch system that this is an async action — batch will wait for True
    s.batch_step_done = False

    # Show progress bar
    s.bottomrow_label.label.grid_remove()
    s.bottomrow_label.progress.grid()
    s.bottomrow_label.progress_label.grid()
    s.bottomrow_label.progress.configure(mode="determinate")
    s.app.after(0, lambda: s.bottomrow_label.update_progress(0, "0%"))

    def run():
        python_exe = sys.executable

        if getattr(s, 'batch_cancel_requested', False):
            tb_update('tb_info', "⏹️ Actie geannuleerd vóór start.", "geel")
            s.batch_step_done = True
            return

        for idx, video_path in enumerate(video_files):
            if getattr(s, 'batch_cancel_requested', False):
                tb_update('tb_info', "⏹️ Speech-to-SRT geannuleerd.", "geel")
                break

            if idx > 0:
                tb_update('tb_info', "· " * 25, "normal")

            base      = idx / total
            base_name = os.path.splitext(video_path)[0]

            # Check if a language-tagged SRT already exists for this video (skip if so)
            existing = [
                f for f in os.listdir(os.path.dirname(video_path) or ".")
                if f.lower().endswith('.srt')
                and os.path.splitext(f)[0].lower().startswith(
                    os.path.splitext(os.path.basename(video_path))[0].lower())
            ]
            if existing:
                tb_update('tb_info', f"⏭️ SRT bestaat al: {existing[0]}", "geel")
                p = (idx + 1) / total
                s.app.after(0, lambda v=p: s.bottomrow_label.update_progress(v, f"{int(v*100)}%"))
                continue

            # Temp output path — renamed after LANG: is received from worker
            out_srt_tmp = base_name + ".__tmp__.srt"
            out_srt     = out_srt_tmp  # updated when LANG: arrives

            tb_update('tb_info', f"🎙️ Starten: {os.path.basename(video_path)}", "normal")

            try:
                proc = subprocess.Popen(
                    [python_exe, "-u", _WORKER, video_path, out_srt_tmp,
                     model_size, device, str(language)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                )
                try:
                    s.set_active_process(proc)
                except Exception:
                    pass
                detected_lang = language  # fallback to requested lang if LANG: never arrives
                for line in proc.stdout:
                    if getattr(s, 'batch_cancel_requested', False):
                        try:
                            proc.terminate()
                        except Exception:
                            pass
                        break
                    line = line.rstrip()
                    if line.startswith("PROGRESS:"):
                        seg_p = float(line.split(":", 1)[1])
                        overall = base + seg_p / total
                        s.app.after(0, lambda v=overall: s.bottomrow_label.update_progress(
                            v, f"{int(v*100)}%"))
                    elif line.startswith("LANG:"):
                        detected_lang = line[5:].strip()
                    elif line.startswith("INFO:"):
                        tb_update('tb_info', line[5:], "normal")
                    elif line.startswith("WARN:"):
                        tb_update('tb_info', f"⚠️ {line[5:]}", "geel")
                    elif line.startswith("ERROR:"):
                        tb_update('tb_info', f"❌ {line[6:]}", "rood")
                    elif line.startswith("DONE:"):
                        # Rename tmp → naam.{lang}.srt
                        lang_tag = detected_lang or "und"
                        out_srt  = base_name + f".{lang_tag}.srt"
                        try:
                            if os.path.exists(out_srt_tmp):
                                os.replace(out_srt_tmp, out_srt)
                        except Exception as rename_err:
                            print(f"⚠️ Rename failed: {rename_err}")
                            out_srt = out_srt_tmp
                        tb_update('tb_info', f"✅ SRT opgeslagen: {os.path.basename(out_srt)}", "groen")
                        break  # SRT is klaar — niet wachten op model-cleanup in worker
                    else:
                        print(line)

                # Forceer afsluiten van de worker (model-cleanup in subprocess kan minuten duren)
                try:
                    proc.kill()
                except Exception:
                    pass
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass
                try:
                    s.set_active_process(None)
                except Exception:
                    pass

                if getattr(s, 'batch_cancel_requested', False):
                    tb_update('tb_info', "⏹️ Speech-to-SRT geannuleerd.", "geel")
                    break

                if proc.returncode != 0 and not os.path.exists(out_srt):
                    tb_update('tb_info', f"❌ Subprocess mislukt (code {proc.returncode})", "rood")

            except Exception as e:
                import traceback
                traceback.print_exc()
                tb_update('tb_info', f"❌ Fout: {e}", "rood")

            done = (idx + 1) / total
            s.app.after(0, lambda v=done: s.bottomrow_label.update_progress(v, f"{int(v*100)}%"))

        # All done
        s.app.after(0, lambda: s.bottomrow_label.update_progress(1.0, "100%"))

        def _cleanup():
            try:
                s.bottomrow_label.progress.grid_remove()
                s.bottomrow_label.progress_label.grid_remove()
                s.bottomrow_label.label.grid()
            except Exception:
                pass

        s.app.after(2000, _cleanup)
        if getattr(s, 'batch_cancel_requested', False):
            tb_update('tb_info', "⏹️ Speech-to-SRT gestopt.", "geel")
        else:
            tb_update('tb_info', f"🏁 Speech-to-SRT klaar ({total} bestand(en)).", "groen")

        # Refresh lb_files to show the new SRT files, then signal batch done
        try:
            from utils.scan_helpers import reload
            def _reload_then_signal():
                reload(s.app)
                # Give lb_files 200ms to repopulate before batch continues
                s.app.after(200, lambda: setattr(s, 'batch_step_done', True))
            s.app.after(500, _reload_then_signal)
        except Exception as e:
            print(f"⚠️ Refresh mislukt: {e}")
            s.batch_step_done = True

    threading.Thread(target=run, daemon=True).start()

