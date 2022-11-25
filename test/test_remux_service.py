import unittest
from unittest.mock import MagicMock
import json

from dvd_remuxer.dvdremux import RemuxService
from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class TestRemuxService(unittest.TestCase):
    def test_run(self):
        args = Args(dvd=".")
        RemuxService(lsdvd_test, DVDRemuxerTest, args).run()


class Args:
    def __init__(self, **args) -> None:
        self.dvd = args.get("dvd")
        self.action = "remux_to_mkv"
        self.title_idx = [1]
        self.list_languages = False
        self.info = False
        self.verbose = False
        self.dry_run = False
        self.keep = False
        self.rewrite = False
        self.use_sys_tmp_dir = False
        self.aspect_ratio = None
        self.audio_params = None
        self.subs_params = None
        self.split_chapters = False
        self.add_sub_langcode = None


if __name__ == "__main__":
    unittest.main()
