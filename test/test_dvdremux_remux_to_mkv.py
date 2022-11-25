import unittest

from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class TestDVDRemuxRemuxToMKV(unittest.TestCase):
    def setUp(self):
        self.remuxer = DVDRemuxerTest(
            ".",
            lsdvd=lsdvd_test.read("."),
        )

    def test_remux_to_mkv(self):
        self.assertEqual(self.remuxer.remux_to_mkv(1).name, "TEST_DVD_1.DVDRemux.mkv")

    def test_remux_to_mkv_with_tmp_dir_obj(self):
        self.remuxer.tmp_dir_obj = 1

        self.assertEqual(self.remuxer.remux_to_mkv(1).name, "TEST_DVD_1.DVDRemux.mkv")

    def test_remux_to_mkv_with_tmp_dir_obj(self):
        self.remuxer.keep_temp_files = 1

        self.assertEqual(self.remuxer.remux_to_mkv(1).name, "TEST_DVD_1.DVDRemux.mkv")


if __name__ == "__main__":
    unittest.main()
