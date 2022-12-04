import unittest

from pathlib import Path
from .dvdremux_test import DVDRemuxerTest
from .lsdvd_test import lsdvd_test


class Test_gen_mkvmerge_cmd(unittest.TestCase):
    def setUp(self):
        self.remuxer = DVDRemuxerTest(
            ".",
            lsdvd=lsdvd_test.read("."),
            dry_run=False,
            keep_temp_files=False,
            rewrite=False,
            use_sys_tmp_dir=False,
            verbose=False,
            file_prefix="TEST_DVD",
        )
        self.outdir = Path.cwd()
        self.outfile = self.outdir / "TEST_DVD_1.DVDRemux.mkv"

    def test_basic_case(self):
        self.assertListEqual(
            self.remuxer.gen_mkvmerge_cmd(
                1, [[1, "en"], [2, "ru"]], [[1, "ru"]], self.outdir
            ),
            [
                "mkvmerge",
                "--output",
                self.outfile,
                "--language",
                "1:en",
                "--language",
                "2:ru",
                "--audio-tracks",
                "1,2",
                self.remuxer.tmp_dir / ("TEST_DVD_1_video.vob"),
                "--language",
                "0:ru",
                self.remuxer.tmp_dir / ("TEST_DVD_1_vobsub_1_ru.idx"),
                "--chapters",
                self.remuxer.tmp_dir / ("TEST_DVD_1_chapters.txt"),
                "--track-order",
                "0:0,0:1,0:2,1:0",
            ],
        )

    def test_with_aspect_ratio(self):
        self.remuxer.aspect_ratio = "16/9"
        self.assertListEqual(
            self.remuxer.gen_mkvmerge_cmd(
                1, [[1, "en"], [2, "ru"]], [[1, "ru"]], self.outdir
            ),
            [
                "mkvmerge",
                "--output",
                self.outfile,
                "--language",
                "1:en",
                "--language",
                "2:ru",
                "--audio-tracks",
                "1,2",
                "--aspect-ratio",
                "0:16/9",
                self.remuxer.tmp_dir / ("TEST_DVD_1_video.vob"),
                "--language",
                "0:ru",
                self.remuxer.tmp_dir / ("TEST_DVD_1_vobsub_1_ru.idx"),
                "--chapters",
                self.remuxer.tmp_dir / ("TEST_DVD_1_chapters.txt"),
                "--track-order",
                "0:0,0:1,0:2,1:0",
            ],
        )

    def test_with_split_chapters(self):
        self.remuxer.split_chapters = True
        self.assertListEqual(
            self.remuxer.gen_mkvmerge_cmd(
                1, [[1, "en"], [2, "ru"]], [[1, "ru"]], self.outdir
            ),
            [
                "mkvmerge",
                "--output",
                self.outfile,
                "--language",
                "1:en",
                "--language",
                "2:ru",
                "--audio-tracks",
                "1,2",
                self.remuxer.tmp_dir / ("TEST_DVD_1_video.vob"),
                "--language",
                "0:ru",
                self.remuxer.tmp_dir / ("TEST_DVD_1_vobsub_1_ru.idx"),
                "--chapters",
                self.remuxer.tmp_dir / ("TEST_DVD_1_chapters.txt"),
                "--split",
                "chapters:all",
                "--track-order",
                "0:0,0:1,0:2,1:0",
            ],
        )

    def test_with_audio(self):
        self.assertListEqual(
            self.remuxer.gen_mkvmerge_cmd(
                1, [[2, "ru"], [1, "en"]], [[1, "ru"]], self.outdir
            ),
            [
                "mkvmerge",
                "--output",
                self.outfile,
                "--language",
                "2:ru",
                "--language",
                "1:en",
                "--audio-tracks",
                "2,1",
                self.remuxer.tmp_dir / ("TEST_DVD_1_video.vob"),
                "--language",
                "0:ru",
                self.remuxer.tmp_dir / ("TEST_DVD_1_vobsub_1_ru.idx"),
                "--chapters",
                self.remuxer.tmp_dir / ("TEST_DVD_1_chapters.txt"),
                "--track-order",
                "0:0,0:2,0:1,1:0",
            ],
        )

    def test_without_chapters(self):
        self.remuxer.lsdvd.track[0].chapter = []
        self.assertListEqual(
            self.remuxer.gen_mkvmerge_cmd(
                1, [[1, "en"], [2, "ru"]], [[1, "ru"]], self.outdir
            ),
            [
                "mkvmerge",
                "--output",
                self.outfile,
                "--language",
                "1:en",
                "--language",
                "2:ru",
                "--audio-tracks",
                "1,2",
                self.remuxer.tmp_dir / ("TEST_DVD_1_video.vob"),
                "--language",
                "0:ru",
                self.remuxer.tmp_dir / ("TEST_DVD_1_vobsub_1_ru.idx"),
                "--track-order",
                "0:0,0:1,0:2,1:0",
            ],
        )


if __name__ == "__main__":
    unittest.main()
