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

def load_translation_model(from_code="en", to_code="nl"):
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next(filter(lambda x: x.code == from_code, installed_languages), None)
    to_lang = next(filter(lambda x: x.code == to_code, installed_languages), None)
    if not from_lang or not to_lang:
        raise Exception("Required language models not installed.")
    return from_lang.get_translation(to_lang)

def translate_srt(input_path, output_path, translation):
    with open(input_path, "r", encoding="utf-8") as infile, open(output_path, "w", encoding="utf-8") as outfile:
        buffer = []
        for line in infile:
            if re.match(r"^\d+$", line) or re.match(r"^\d{2}:\d{2}:\d{2},\d{3}", line) or line.strip() == "":
                if buffer:
                    translated = translation.translate(" ".join(buffer))
                    outfile.write(translated + "\n")
                    buffer = []
                outfile.write(line)
            else:
                buffer.append(line.strip())
        if buffer:
            translated = translation.translate(" ".join(buffer))
            outfile.write(translated + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python translate_srt_argos.py input.srt output.srt")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    translation = load_translation_model()
    translate_srt(input_file, output_file, translation)
    print(f"✅ Translated: {input_file} → {output_file}")