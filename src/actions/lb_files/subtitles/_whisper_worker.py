"""
Standalone worker script for faster-whisper transcription.
Called as a subprocess by whisper_srt.py.
Writes progress lines to stdout: "PROGRESS:0.45"
Writes result to the output SRT path passed as argument.
On error writes "ERROR:<message>" to stdout.
"""
import sys
import os
import datetime


def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    millis = int((seconds - total_seconds) * 1000)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d},{millis:03d}"


def main():
    # Args: video_path out_srt model_size device language
    if len(sys.argv) < 6:
        print("ERROR:Missing arguments")
        sys.exit(1)

    video_path = sys.argv[1]
    out_srt    = sys.argv[2]
    model_size = sys.argv[3]
    device     = sys.argv[4]
    language   = sys.argv[5] if sys.argv[5] != "None" else None

    try:
        from faster_whisper import WhisperModel
        import torch

        if device == "cuda" and not torch.cuda.is_available():
            print("WARN:CUDA niet beschikbaar, gebruik CPU", flush=True)
            device = "cpu"

        compute_type = "float16" if device == "cuda" else "int8"
        print(f"INFO:Model laden ({model_size} op {device.upper()})", flush=True)

        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        lang_str = language or "auto-detect"
        print(f"INFO:Transcriberen ({lang_str}): {os.path.basename(video_path)}", flush=True)

        segments_gen, info = model.transcribe(video_path, language=language, beam_size=5)
        duration = info.duration or 1.0

        detected = info.language if not language else language
        print(f"LANG:{detected}", flush=True)
        print(f"INFO:Taal: {detected} ({info.language_probability:.0%})", flush=True)

        lines = []
        for i, seg in enumerate(segments_gen, start=1):
            start = format_timestamp(seg.start)
            end   = format_timestamp(seg.end)
            text  = seg.text.strip()
            lines.append(f"{i}\n{start} --> {end}\n{text}\n")
            progress = min(seg.end / duration, 0.99)
            print(f"PROGRESS:{progress:.4f}", flush=True)

        srt_content = "\n".join(lines)
        with open(out_srt, "w", encoding="utf-8") as f:
            f.write(srt_content)

        print(f"DONE:{out_srt}", flush=True)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR:{e}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
