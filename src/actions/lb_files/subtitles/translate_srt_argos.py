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
import argostranslate.translate
import argostranslate.package

def get_argos_data_dir():
    """Get appropriate data directory for argostranslate packages"""
    # Check if running as frozen executable
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        # Use a writable location in user's AppData
        if sys.platform == 'win32':
            appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            data_dir = os.path.join(appdata, 'MKVApp', 'argos_packages')
        else:
            data_dir = os.path.expanduser('~/.local/share/MKVApp/argos_packages')
        
        os.makedirs(data_dir, exist_ok=True)
        
        # Set argostranslate to use this directory
        argostranslate.package.set_package_dirs([data_dir])
        print(f"📦 Using argostranslate data directory: {data_dir}")
        return data_dir
    else:
        # Running in normal Python environment, use default location
        return None

def ensure_language_installed(lang_code):
    """Ensure a language package is installed, download if needed"""
    # Set custom data dir if frozen
    get_argos_data_dir()
    
    installed_languages = argostranslate.translate.get_installed_languages()
    if any(lang.code == lang_code for lang in installed_languages):
        return True
    
    print(f"📥 Downloading language package: {lang_code}")
    
    try:
        # Update package index
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        # Find and install package containing this language
        installed = False
        for pkg in available_packages:
            if pkg.from_code == lang_code or pkg.to_code == lang_code:
                print(f"⬇️ Installing: {pkg.from_name} → {pkg.to_name}")
                argostranslate.package.install_from_path(pkg.download())
                installed = True
        
        if not installed:
            print(f"⚠️ Language '{lang_code}' not found in available packages")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to download language package: {e}")
        return False

def load_translation_model(from_code="en", to_code="nl"):
    """Load translation model, automatically download if needed"""
    # Set custom data dir if frozen
    get_argos_data_dir()
    
    # Ensure both languages are installed
    if not ensure_language_installed(from_code):
        raise Exception(f"Failed to install language: {from_code}")
    if not ensure_language_installed(to_code):
        raise Exception(f"Failed to install language: {to_code}")
    
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next(filter(lambda x: x.code == from_code, installed_languages), None)
    to_lang = next(filter(lambda x: x.code == to_code, installed_languages), None)
    
    if not from_lang or not to_lang:
        raise Exception(f"Required language models not available: {from_code} → {to_code}")
    
    return from_lang.get_translation(to_lang)

def translate_srt(input_path, output_path, translation, progress_callback=None):
    """Translate SRT file with optional progress callback.
    
    Args:
        input_path: Input SRT file path
        output_path: Output SRT file path
        translation: Translation model
        progress_callback: Optional callback(current, total) to report progress
    """
    # First pass: count total subtitle blocks
    total_blocks = 0
    with open(input_path, "r", encoding="utf-8") as infile:
        in_text_block = False
        for line in infile:
            if re.match(r"^\d+$", line.strip()):
                total_blocks += 1
    
    # Second pass: translate with progress reporting
    current_block = 0
    with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8") as outfile:
        buffer = []
        for line in infile:
            if re.match(r"^\d+$", line) or re.match(r"^\d{2}:\d{2}:\d{2},\d{3}", line) or line.strip() == "":
                if buffer:
                    translated = translation.translate(" ".join(buffer))
                    outfile.write(translated + "\n")
                    buffer = []
                    current_block += 1
                    if progress_callback and total_blocks > 0:
                        progress_callback(current_block, total_blocks)
                outfile.write(line)
            else:
                buffer.append(line.strip())
        if buffer:
            translated = translation.translate(" ".join(buffer))
            outfile.write(translated + "\n")
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