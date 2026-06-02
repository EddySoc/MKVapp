import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


MODULE_PATH = Path(__file__).resolve().parents[1] / 'lb_files' / 'subtitles' / 'extract.py'


spec = importlib.util.spec_from_file_location('extract_direct', MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class UniqueOutputPathTests(unittest.TestCase):
    def test_returns_same_path_when_file_does_not_exist(self):
        with TemporaryDirectory() as tmp:
            candidate = Path(tmp) / 'Film-eng.srt'
            result = module.unique_output_path(str(candidate))
            self.assertEqual(result, str(candidate))

    def test_appends_dash_2_when_base_file_exists(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp) / 'Film-eng.srt'
            base.write_text('existing', encoding='utf-8')

            result = module.unique_output_path(str(base))
            self.assertEqual(result, str(Path(tmp) / 'Film-eng-2.srt'))

    def test_appends_next_available_index(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp) / 'Film-eng.srt'
            second = Path(tmp) / 'Film-eng-2.srt'
            base.write_text('existing', encoding='utf-8')
            second.write_text('existing', encoding='utf-8')

            result = module.unique_output_path(str(base))
            self.assertEqual(result, str(Path(tmp) / 'Film-eng-3.srt'))


class NormalizeTrackLanguageTests(unittest.TestCase):
    def test_maps_legacy_one_letter_language_code(self):
        self.assertEqual(module.normalize_track_language_to_iso6393('d'), 'nld')

    def test_maps_iso639_1_code(self):
        self.assertEqual(module.normalize_track_language_to_iso6393('nl'), 'nld')

    def test_maps_language_name(self):
        self.assertEqual(module.normalize_track_language_to_iso6393('dutch'), 'nld')


if __name__ == '__main__':
    unittest.main()