import unittest

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


if __name__ == "__main__":
    unittest.main()
