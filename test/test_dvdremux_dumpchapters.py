import unittest

from unittest.mock import MagicMock, patch
from pathlib import Path
from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class Test_dumpchapters(unittest.TestCase):
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
        self.outfile = self.remuxer.tmp_dir / ("TEST_DVD_1_chapters.txt")
        self.remuxer._save_to_file = MagicMock()

    def test_dumpchapters(self):
        self.assertEqual(self.remuxer.dumpchapters(1), self.outfile)

    def test_gen_chapters_filename(self):
        self.assertEqual(self.remuxer.gen_chapters_filename(1), self.outfile)

    def test_gen_chapters(self):
        chapters_expected = (
            "CHAPTER01=00:00:00.000\n"
            + "CHAPTER01NAME=\n"
            + "CHAPTER02=00:01:40.880\n"
            + "CHAPTER02NAME=\n"
            + "CHAPTER03=00:02:50.040\n"
            + "CHAPTER03NAME=\n"
        )

        self.assertEqual(self.remuxer.gen_chapters(1), chapters_expected)

    def test_perform_dumpchapters_outfile_exists(self):
        with patch.object(Path, "exists", return_value=True) as mock_method:
            self.remuxer._perform_dumpchapters(self.outfile, "test")

        self.remuxer._save_to_file.assert_not_called

    def test_perform_dumpchapters_outfile_exists_and_rewrite(self):
        self.remuxer.rewrite = True

        with patch.object(Path, "exists", return_value=True) as mock_method:
            self.remuxer._perform_dumpchapters(self.outfile, "test")

        self.remuxer._save_to_file.assert_called_with(self.outfile, "test")

    def test_perform_dumpchapters_outfile_not_exists(self):
        self.remuxer.rewrite = False

        self.remuxer._perform_dumpchapters(self.outfile, "test")

        self.remuxer._save_to_file.assert_called_with(self.outfile, "test")


if __name__ == "__main__":
    unittest.main()
