import unittest

from unittest.mock import MagicMock, patch
from pathlib import Path
from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class TestDumpstreamBase(unittest.TestCase):
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
        self.outfile = self.remuxer.tmp_dir / ("TEST_DVD_1_video.vob")


class TestDumpstream(TestDumpstreamBase):
    def test_dumpstream(self):
        self.assertEqual(self.remuxer.dumpstream(1), self.outfile)

    def test_build_dumpstream_cmd(self):
        self.assertTupleEqual(
            self.remuxer.build_dumpstream_cmd(1),
            (
                self.outfile,
                [
                    "mplayer",
                    "-dvd-device",
                    ".",
                    "dvd://1",
                    "-dumpstream",
                    "-dumpfile",
                    self.outfile,
                ],
            ),
        )

    def test_gen_dumpstream_filename(self):
        self.assertEqual(self.remuxer.gen_dumpstream_filename(1), self.outfile)


class Test_perform_dumpstream(TestDumpstreamBase):
    def test_outfile_exists(self):
        self.remuxer._subprocess_run = MagicMock()

        with patch.object(Path, "exists", return_value=True) as mock_method:
            self.remuxer._perform_dumpstream(self.outfile, [])

        self.remuxer._subprocess_run.assert_not_called

    def test_outfile_exists_and_rewrite(self):
        self.remuxer._subprocess_run = MagicMock()
        self.remuxer.rewrite = True
        dump_cmd = ["binary", "arg1", "arg2"]

        with patch.object(Path, "exists", return_value=True) as mock_method:
            self.remuxer._perform_dumpstream(self.outfile, dump_cmd)

        self.remuxer._subprocess_run.assert_called_with(dump_cmd, stdout=-3, stderr=-3)

    def test_outfile_not_exists(self):
        self.remuxer._subprocess_run = MagicMock()
        self.remuxer.rewrite = False
        dump_cmd = ["binary", "arg1", "arg2"]

        with patch.object(Path, "exists", return_value=False) as mock_method:
            self.remuxer._perform_dumpstream(self.outfile, dump_cmd)

        self.remuxer._subprocess_run.assert_called_with(dump_cmd, stdout=-3, stderr=-3)


if __name__ == "__main__":
    unittest.main()
