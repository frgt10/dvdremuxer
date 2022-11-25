import unittest
from unittest.mock import MagicMock

from tempfile import TemporaryDirectory
from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class TestDVDRemuxInit(unittest.TestCase):
    def test_use_sys_tmp_dir(self):
        self.remuxer = DVDRemuxerTest(
            ".",
            lsdvd=lsdvd_test.read("."),
            use_sys_tmp_dir=True,
        )

        self.assertIsInstance(self.remuxer.tmp_dir_obj, TemporaryDirectory)

    def test_lsdvd_title_empty(self):
        lsdvd_obj = lsdvd_test.read(".")
        lsdvd_obj.title = "unknown"

        self.remuxer = DVDRemuxerTest(".", lsdvd=lsdvd_obj)

        self.assertEqual(self.remuxer.file_prefix, "dvd")

    def test_lsdvd_title_eq_unknown(self):
        lsdvd_obj = lsdvd_test.read(".")
        lsdvd_obj.title = "unknown"

        self.remuxer = DVDRemuxerTest(".", lsdvd=lsdvd_obj)

        self.assertEqual(self.remuxer.file_prefix, "dvd")

    def test_without_lsdvd(self):
        with self.assertRaises(Exception) as cm:
            self.remuxer = DVDRemuxerTest(".", lsdvd=None)


class Test_DVDRemuxMethods(unittest.TestCase):
    def setUp(self):
        self.remuxer = DVDRemuxerTest(
            ".",
            lsdvd=lsdvd_test.read("."),
            dry_run=False,
            keep_temp_files=False,
            rewrite=False,
            use_sys_tmp_dir=False,
            verbose=False,
        )
        self.remuxer._subprocess_run = MagicMock()

    def test_normalize_langcode_empty(self):
        self.assertEqual(self.remuxer._normalize_langcode("audio", 1, 0, ""), "und")

    def test_normalize_langcode_xx(self):
        self.assertEqual(self.remuxer._normalize_langcode("audio", 1, 0, "xx"), "und")

    def test_normalize_langcode_xx(self):
        self.assertEqual(
            self.remuxer._normalize_langcode("audio", 1, 2, "undefined"), "ru"
        )

    def test_get_title_subs_params_defaults(self):
        self.assertListEqual(self.remuxer._get_title_subs_params(1), [[1, "ru"]])

    def test_get_title_subs_params_empty(self):
        self.remuxer.langcodes = ["jp", "ko"]

        self.assertListEqual(self.remuxer._get_title_subs_params(1), [])

    def test_get_title_subs_params_specified(self):
        self.remuxer.subs_params = [[1, "ru"], [2, "en"]]

        self.assertListEqual(
            self.remuxer._get_title_subs_params(1), [[1, "ru"], [2, "en"]]
        )

    def test_dvd_info(self):
        self.remuxer.dvd_info()
        self.remuxer._subprocess_run.assert_called_with(
            ["lsdvd", "-x", self.remuxer.device]
        )

    def test_list_languages(self):
        self.remuxer.list_languages()
        self.remuxer._subprocess_run.assert_called_with(
            ["mkvmerge", "--list-languages"]
        )


if __name__ == "__main__":
    unittest.main()
