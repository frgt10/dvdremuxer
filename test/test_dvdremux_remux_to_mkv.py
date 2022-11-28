import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class TestDVDRemuxRemuxToMKV(unittest.TestCase):
    def setUp(self):
        self.remuxer = DVDRemuxerTest(
            ".",
            lsdvd=lsdvd_test.read("."),
            file_prefix="TEST_DVD",
        )
        self.outdir = Path.cwd()

    def test_remux_to_mkv(self):
        self.assertEqual(
            self.remuxer.remux_to_mkv(1, [[1, "ru"]], [[1, "ru"]], self.outdir).name,
            "TEST_DVD_1.DVDRemux.mkv",
        )

    def test_remux_to_mkv_with_keep_temp_files(self):
        self.remuxer.keep_temp_files = 1

        self.assertEqual(
            self.remuxer.remux_to_mkv(1, [[1, "ru"]], [[1, "ru"]], self.outdir).name,
            "TEST_DVD_1.DVDRemux.mkv",
        )

    def test_remux_to_mkv_with_tmp_dir_obj(self):
        remuxer = DVDRemuxerTest(
            ".",
            lsdvd=lsdvd_test.read("."),
            use_sys_tmp_dir=True,
            file_prefix="TEST_DVD",
        )

        remuxer.remux_to_mkv(1, [[1, "ru"]], [[1, "ru"]], self.outdir)

        self.assertIsInstance(remuxer.tmp_dir_obj, TemporaryDirectory)


if __name__ == "__main__":
    unittest.main()
