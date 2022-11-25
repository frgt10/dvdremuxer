import unittest

from unittest.mock import MagicMock, patch
from pathlib import Path
from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class Test_dumpvobsub(unittest.TestCase):
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
        self.remuxer._clear_file = MagicMock()
        self.outfile = self.remuxer.tmp_dir / ("TEST_DVD_1_vobsub_1_ru")

    def test_dumpvobsub(self):
        self.assertTupleEqual(
            self.remuxer.dumpvobsub(1, 1, "ru"),
            (
                self.outfile.with_suffix(".idx"),
                self.outfile.with_suffix(".sub"),
            ),
        )

    def test_gen_vobsub_filenames(self):
        self.assertTupleEqual(
            self.remuxer.gen_vobsub_filenames(1, 1, "ru"),
            (
                self.outfile,
                self.outfile.with_suffix(".idx"),
                self.outfile.with_suffix(".sub"),
            ),
        )

    def test_gen_dumpvobsub_cmd(self):
        self.assertListEqual(
            self.remuxer.gen_dumpvobsub_cmd(self.outfile, 1, 1),
            [
                "mencoder",
                "-dvd-device",
                self.remuxer.device,
                "dvd://1",
                "-vobsubout",
                self.outfile,
                "-vobsuboutindex",
                "1",
                "-sid",
                "0",
                "-ovc",
                "copy",
                "-oac",
                "copy",
                "-nosound",
                "-o",
                "/dev/null",
                "-vf",
                "harddup",
            ],
        )

    def test_perform_dumpvobsub_outfile_exists(self):
        with patch.object(Path, "exists", return_value=True) as mock_method:
            self.remuxer._perform_dumpvobsub(
                [],
                self.outfile.with_suffix(".idx"),
                self.outfile.with_suffix(".sub"),
                "ru",
            )

        self.remuxer._clear_file.assert_not_called

    def test_perform_dumpvobsub_outfile_exists_and_rewrite(self):
        self.remuxer.rewrite = True
        with patch.object(Path, "exists", return_value=True) as mock_method:
            self.remuxer._perform_dumpvobsub(
                [],
                self.outfile.with_suffix(".idx"),
                self.outfile.with_suffix(".sub"),
                "ru",
            )

        self.remuxer._clear_file.assert_called

    def test_perform_dumpvobsub_outfile_not_exists(self):
        with patch.object(Path, "exists", return_value=False) as mock_method:
            self.remuxer._perform_dumpvobsub(
                [],
                self.outfile.with_suffix(".idx"),
                self.outfile.with_suffix(".sub"),
                "ru",
            )

        self.remuxer._clear_file.assert_not_called

    def test_fix_vobsub_lang_id(self):
        vobsub_with_wrong_lancode = "id: , index"

        self.assertEqual(
            self.remuxer._fix_vobsub_lang_id(vobsub_with_wrong_lancode, "ru"),
            "id: ru, index",
        )

    def test_dumpvobsubs(self):
        self.assertDictEqual(
            self.remuxer.dumpvobsubs(1),
            {
                "ru": (
                    self.outfile.with_suffix(".idx"),
                    self.outfile.with_suffix(".sub"),
                )
            },
        )


if __name__ == "__main__":
    unittest.main()
