import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / 'lb_files' / 'subtitles' / 'translate_srt_argos.py'


spec = importlib.util.spec_from_file_location('translate_srt_argos_direct', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NormalizeLanguageCodeTests(unittest.TestCase):
    def test_maps_common_three_letter_codes(self):
        self.assertEqual(module.normalize_language_code('eng'), 'en')
        self.assertEqual(module.normalize_language_code('dut'), 'nl')
        self.assertEqual(module.normalize_language_code('nld'), 'nl')
        self.assertEqual(module.normalize_language_code('fre'), 'fr')

    def test_keeps_two_letter_codes(self):
        self.assertEqual(module.normalize_language_code('en'), 'en')
        self.assertEqual(module.normalize_language_code('nl'), 'nl')

    def test_load_translation_model_raises_when_pair_is_missing(self):
        class FakeLanguage:
            def __init__(self, code):
                self.code = code

            def get_translation(self, other):
                return None

        class FakeTranslate:
            @staticmethod
            def get_installed_languages():
                return [FakeLanguage('en'), FakeLanguage('nl')]

        class FakeArgos:
            translate = FakeTranslate()

        with patch.object(module, '_import_argos', return_value=FakeArgos()):
            with patch.object(module, 'ensure_language_installed', side_effect=lambda code: (True, code)):
                with self.assertRaises(Exception):
                    module.load_translation_model('eng', 'dut')


if __name__ == '__main__':
    unittest.main()
