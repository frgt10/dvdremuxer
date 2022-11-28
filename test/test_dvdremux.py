import unittest
from unittest.mock import MagicMock

from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class TestDVDRemuxInit(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
