#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     13/09/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import re
import sys
import os


_LANG_CODE_ALIASES = {
    'eng': 'en', 'english': 'en',
    'dut': 'nl', 'nld': 'nl', 'dutch': 'nl',
    'fre': 'fr', 'fra': 'fr', 'french': 'fr',
    'ger': 'de', 'deu': 'de', 'german': 'de',
    'spa': 'es', 'spanish': 'es',
    'ita': 'it', 'italian': 'it',
    'por': 'pt', 'portuguese': 'pt',
    'jpn': 'ja', 'japanese': 'ja',
    'chi': 'zh', 'zho': 'zh', 'chinese': 'zh',
    'kor': 'ko', 'korean': 'ko',
    'swe': 'sv', 'swedish': 'sv',
    'nor': 'no', 'norwegian': 'no',
    'dan': 'da', 'danish': 'da',
    'fin': 'fi', 'finnish': 'fi',
    'pol': 'pl', 'polish': 'pl',
    'cze': 'cs', 'ces': 'cs', 'czech': 'cs',
    'slo': 'sk', 'slk': 'sk', 'slovak': 'sk',
    'hun': 'hu', 'hungarian': 'hu',
    'rum': 'ro', 'ron': 'ro', 'romanian': 'ro',
}


def _status(message):
    """Print status messages safely on Windows consoles with limited encodings."""
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        safe_message = str(message).encode(encoding, errors='replace').decode(encoding, errors='replace')
        print(safe_message)


def normalize_language_code(lang_code, default=None):
    """Normalize common 3-letter or named language codes to Argos 2-letter codes."""
    if lang_code is None:
        return default

    code = str(lang_code).strip().lower()
    if not code:
        return default

    code = code.replace('_', '-')
    normalized = _LANG_CODE_ALIASES.get(code)
    if normalized:
        return normalized

    if '-' in code:
        base_code = code.split('-', 1)[0]
        normalized = _LANG_CODE_ALIASES.get(base_code, base_code)
        if normalized:
            return normalized

    if len(code) == 2:
        return code

    return _LANG_CODE_ALIASES.get(code, default or code)

# Configure Argos packages directory before importing argostranslate
if getattr(sys, 'frozen', False):
    if sys.platform == 'win32':
        appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        argos_packages_dir = os.path.join(appdata, 'MKVApp', 'argos_packages')
    else:
        argos_packages_dir = os.path.expanduser('~/.local/share/MKVApp/argos_packages')
    os.makedirs(argos_packages_dir, exist_ok=True)
    os.environ['ARGOS_PACKAGES_DIR'] = argos_packages_dir

def _import_argos():
    """Lazy-load argostranslate to avoid crashing on module import."""
    import argostranslate.translate
    import argostranslate.package
    return argostranslate

def get_argos_data_dir():
    """Get appropriate data directory for argostranslate packages"""
    # Check if running as frozen executable
    if getattr(sys, 'frozen', False):
        data_dir = os.environ.get('ARGOS_PACKAGES_DIR')
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)
            _status(f"📦 Using argostranslate data directory: {data_dir}")
            return data_dir
        return None
    else:
        # Running in normal Python environment, use default location
        return None

def ensure_language_installed(lang_code):
    """Ensure a language package is installed, download if needed"""
    get_argos_data_dir()
    argostranslate = _import_argos()

    lang_code = normalize_language_code(lang_code, default='en')

    installed_languages = argostranslate.translate.get_installed_languages()
    if any(lang.code == lang_code for lang in installed_languages):
        return True, lang_code
    
    _status(f"📥 Downloading language package: {lang_code}")
    
    try:
        # Update package index
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        # Find and install package containing this language
        installed = False
        for pkg in available_packages:
            if pkg.from_code == lang_code or pkg.to_code == lang_code:
                _status(f"⬇️ Installing: {pkg.from_name} → {pkg.to_name}")
                argostranslate.package.install_from_path(pkg.download())
                installed = True
        
        if not installed:
            _status(f"⚠️ Language '{lang_code}' not found in available packages")
            _status("   Falling back to English (en)")
            return False, "en"
        
        return True, lang_code
    except Exception as e:
        _status(f"❌ Failed to download language package for '{lang_code}': {e}")
        _status("   Falling back to English (en)")
        return False, "en"

def ensure_translation_pair_installed(from_code, to_code):
    """Ensure the specific Argos translation pair exists, downloading it if needed."""
    get_argos_data_dir()
    argostranslate = _import_argos()

    from_code = normalize_language_code(from_code, default='en')
    to_code = normalize_language_code(to_code, default='nl')

    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed_languages if lang.code == from_code), None)
    to_lang = next((lang for lang in installed_languages if lang.code == to_code), None)

    if from_lang and to_lang and from_lang.get_translation(to_lang) is not None:
        return True

    _status(f"📥 Downloading translation package: {from_code} → {to_code}")

    try:
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()

        for pkg in available_packages:
            pkg_from = normalize_language_code(getattr(pkg, 'from_code', None), default=getattr(pkg, 'from_code', None))
            pkg_to = normalize_language_code(getattr(pkg, 'to_code', None), default=getattr(pkg, 'to_code', None))
            if pkg_from == from_code and pkg_to == to_code:
                _status(f"⬇️ Installing translation pair: {pkg.from_name} → {pkg.to_name}")
                argostranslate.package.install_from_path(pkg.download())
                return True

        _status(f"⚠️ No direct Argos translation package found for {from_code} → {to_code}")
        return False
    except Exception as e:
        _status(f"❌ Failed to install translation pair {from_code} → {to_code}: {e}")
        return False


def load_translation_model(from_code="en", to_code="nl"):
    """Load translation model, automatically download if needed."""
    from_code = normalize_language_code(from_code, default="en")
    to_code = normalize_language_code(to_code, default="nl")

    get_argos_data_dir()
    argostranslate = _import_argos()

    # Ensure both languages are installed; if not, fallback to supported language
    success_from, from_code = ensure_language_installed(from_code)
    success_to, to_code = ensure_language_installed(to_code)
    
    if from_code == to_code:
        raise Exception(f"Source and target languages cannot be the same: {from_code}")

    pair_ready = ensure_translation_pair_installed(from_code, to_code)
    
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next(filter(lambda x: x.code == from_code, installed_languages), None)
    to_lang = next(filter(lambda x: x.code == to_code, installed_languages), None)
    
    if not from_lang or not to_lang:
        raise Exception(f"Required language models not available: {from_code} → {to_code}")
    
    translation = from_lang.get_translation(to_lang)
    if translation is None:
        raise Exception(
            f"No translation model available for {from_code} → {to_code}. "
            f"Install that specific language pair first."
        )
    
    # Log fallbacks if they occurred
    if not success_from or not success_to or not pair_ready:
        fallback_msg = []
        if not success_from:
            fallback_msg.append(f"source language fell back to {from_code}")
        if not success_to:
            fallback_msg.append(f"target language fell back to {to_code}")
        if not pair_ready:
            fallback_msg.append(f"pair check for {from_code} → {to_code} needs attention")
        _status(f"⚠️ Translation model loaded with fallback(s): {', '.join(fallback_msg)}")
    
    return translation

def translate_srt(input_path, output_path, translation, progress_callback=None):
    """Translate SRT file with optional progress callback.
    
    Args:
        input_path: Input SRT file path
        output_path: Output SRT file path
        translation: Translation model
        progress_callback: Optional callback(current, total) to report progress
    """
    # Helper to open file with multiple encoding fallbacks
    def open_with_fallback(path, mode='r'):
        """Open file trying multiple encodings in order."""
        for encoding in ['utf-8-sig', 'utf-8', 'utf-16', 'latin-1', 'cp1252']:
            try:
                return open(path, mode, encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        # Final fallback: use errors='replace' to skip undecodable bytes
        return open(path, mode, encoding='utf-8', errors='replace')
    
    # First pass: count total subtitle blocks
    total_blocks = 0
    with open_with_fallback(input_path) as infile:
        in_text_block = False
        for line in infile:
            if re.match(r"^\d+$", line.strip()):
                total_blocks += 1
    
    # Helper: perform translation with a timeout to avoid hanging on a block
    from concurrent.futures import ThreadPoolExecutor, TimeoutError

    def safe_translate(translation_obj, text, timeout=30):
        """Run translation.translate(text) with a timeout; on failure return original text."""
        if not text:
            return ""
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(translation_obj.translate, text)
                return future.result(timeout=timeout)
        except TimeoutError:
            _status("⚠️ Translation timed out for block: returning original text")
            return text
        except Exception as e:
            _status(f"❌ Translation error: {e}")
            return text

    # Second pass: translate with progress reporting
    import os
    current_block = 0
    # Inform caller about total blocks (so UI can initialize determinate progress)
    if progress_callback and total_blocks > 0:
        try:
            progress_callback(0, total_blocks)
        except Exception:
            pass

    # Heuristic: preserve preamble/header lines (e.g., ASS/SSA "[Script Info]" or "Format:")
    seen_first_index = False
    # If file looks like an ASS/SSA file with Dialogue lines and a Format specifying Text,
    # handle it specially by translating only the Text field while preserving formatting.
    def translate_ass(in_path, out_path, translation_obj, progress_cb=None):
        fmt_fields = []
        total_dialogues = 0
        # First pass: discover Format fields and count Dialogue lines
        with open_with_fallback(in_path) as f:
            for ln in f:
                if ln.strip().lower().startswith('format:'):
                    # e.g. "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
                    fmt_fields = [x.strip() for x in ln.split(':', 1)[1].split(',')]
                if ln.strip().lower().startswith('dialogue:'):
                    total_dialogues += 1

        # If we have a Format and a Text field, translate dialogues
        if not fmt_fields or 'Text' not in [f.title() for f in fmt_fields]:
            # fallback: copy file unchanged
            with open_with_fallback(in_path) as src, open_with_fallback(out_path, 'w') as dst:
                dst.write(src.read())
            return

        text_index = None
        # find index of Text (case-insensitive)
        for i, nm in enumerate(fmt_fields):
            if nm.strip().lower() == 'text':
                text_index = i
                break

        current = 0
        # Inform caller of total for progress
        if progress_cb and total_dialogues > 0:
            try:
                progress_cb(0, total_dialogues)
            except Exception:
                pass

        with open_with_fallback(in_path) as src, open_with_fallback(out_path, 'w') as dst:
            for ln in src:
                if ln.strip().lower().startswith('dialogue:'):
                    # split into fields: Dialogue: a,b,c,... where text is last or at text_index
                    prefix, rest = ln.split(':', 1)
                    # split into N parts where N = len(fmt_fields)-1 so remainder is text (which may contain commas)
                    parts = [p for p in rest.split(',', len(fmt_fields)-1)]
                    if text_index is None or text_index >= len(parts):
                        # fallback: treat last part as text
                        text = parts[-1]
                    else:
                        text = parts[text_index]

                    # preserve escape for newlines; convert to marker
                    marker = '|||NEWLINE|||'  # unlikely sequence
                    text_for_trans = text.replace('\\N', marker).replace('\\n', marker)
                    # strip leading/trailing whitespace
                    text_for_trans_stripped = text_for_trans.strip()

                    try:
                        translated_text = safe_translate(translation_obj, text_for_trans_stripped, timeout=30) if text_for_trans_stripped else ''
                    except Exception:
                        translated_text = text_for_trans_stripped

                    # restore marker to \N
                    translated_text = translated_text.replace(marker, '\\N')

                    # rebuild parts with translated text
                    if text_index is None or text_index >= len(parts):
                        parts[-1] = translated_text
                    else:
                        parts[text_index] = translated_text

                    new_rest = ','.join(parts)
                    dst.write(f"{prefix}:{new_rest}")
                    current += 1
                    if progress_cb and total_dialogues > 0:
                        try:
                            progress_cb(current, total_dialogues)
                        except Exception:
                            pass
                else:
                    dst.write(ln)

    # Quick detection: if file contains an ASS/SSA header and Dialogue lines, use translate_ass
    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace') as _fcheck:
            sample = _fcheck.read(4096)
            if ('[script info]' in sample.lower() or '[v4+' in sample.lower() or 'format:' in sample.lower()) and 'dialogue:' in sample.lower():
                # treat as ASS-like file
                return translate_ass(input_path, output_path, translation, progress_callback)
    except Exception:
        pass
    with open_with_fallback(input_path) as infile, open_with_fallback(output_path, 'w') as outfile:
        buffer = []          # stripped lines for translation
        buffer_raw = []      # original lines for possible header passthrough
        for line in infile:
            is_index = bool(re.match(r"^\d+$", line.strip()))
            is_timecode = bool(re.match(r"^\d{2}:\d{2}:\d{2}[,\.]\d{3}", line.strip()))
            is_blank = line.strip() == ""

            if is_index or is_timecode or is_blank:
                if buffer:
                    # If we haven't seen the first numeric index yet, check whether the
                    # buffered lines look like a header/preamble (ASS/SSA or metadata).
                    is_preamble = (not seen_first_index) and any(
                        (ln.strip().startswith("[") or "Format:" in ln or "Script Info" in ln or "PlayRes" in ln or "ScaledBorder" in ln or "V4+" in ln or ln.strip().startswith("Style:") )
                        for ln in buffer_raw
                    )

                    if is_preamble:
                        # Write raw header lines unchanged
                        for orig in buffer_raw:
                            outfile.write(orig)
                            outfile.flush()
                            try:
                                os.fsync(outfile.fileno())
                            except Exception:
                                pass
                    else:
                        text_to_translate = " ".join(buffer).strip()
                        translated = safe_translate(translation, text_to_translate, timeout=30) if text_to_translate else ""

                        # Write the translated text followed by a newline, flush to disk
                        outfile.write(translated + "\n")
                        outfile.flush()
                        try:
                            os.fsync(outfile.fileno())
                        except Exception:
                            pass

                    buffer = []
                    buffer_raw = []
                    current_block += 1
                    if progress_callback and total_blocks > 0:
                        progress_callback(current_block, total_blocks)

                # always write structural lines (indexes, timecodes, blank lines)
                if is_index:
                    seen_first_index = True
                outfile.write(line)
                outfile.flush()
                try:
                    os.fsync(outfile.fileno())
                except Exception:
                    pass
            else:
                buffer.append(line.strip())
                buffer_raw.append(line)

        # final buffer
        if buffer:
            # If the file had no index blocks at all (or final preamble), preserve raw lines
            if not seen_first_index:
                for orig in buffer_raw:
                    outfile.write(orig)
                    outfile.flush()
                    try:
                        os.fsync(outfile.fileno())
                    except Exception:
                        pass
            else:
                text_to_translate = " ".join(buffer).strip()
                try:
                    translated = translation.translate(text_to_translate) if text_to_translate else ""
                except Exception as te:
                    _status(f"❌ Translation error for final block: {te}")
                    translated = text_to_translate
                outfile.write(translated + "\n")
                outfile.flush()
                try:
                    os.fsync(outfile.fileno())
                except Exception:
                    pass
                current_block += 1
                if progress_callback and total_blocks > 0:
                    progress_callback(current_block, total_blocks)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python translate_srt_argos.py input.srt output.srt")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    translation = load_translation_model()
    translate_srt(input_file, output_file, translation)
    print(f"✅ Translated: {input_file} → {output_file}")