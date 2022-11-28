import unittest

from dvd_remuxer.dvdremux import RemuxService
from dvd_remuxer.lsdvd import lsdvd
from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class TestRemuxService(unittest.TestCase):
    def test_init_without_lsdvd(self):
        args = Args(dvd=".")
        with self.assertRaises(Exception) as cm:
            RemuxService(lsdvd, DVDRemuxerTest, args)

    def test_run(self):
        args = Args(dvd=".")
        RemuxService(lsdvd_test, DVDRemuxerTest, args).run()

    def test_get_file_prefix_lsdvd_title_empty(self):
        args = Args(dvd=".")
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        remux_service.lsdvd.title = None

        self.assertEqual(remux_service._get_file_prefix(), "dvd")

    def test_get_file_prefix_lsdvd_title_eq_unknown(self):
        args = Args(dvd=".")
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        remux_service.lsdvd.title = "unknown"

        self.assertEqual(remux_service._get_file_prefix(), "dvd")

    def test_get_audio_params1(self):
        args = Args(dvd=".", audio_params=[[1, "undefined"], [2, "undefined"]])
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertLessEqual(
            remux_service.get_audio_params(1),
            [[1, "en"], [2, "ru"]],
        )

    def test_get_audio_params2(self):
        args = Args(dvd=".")
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertLessEqual(
            remux_service.get_audio_params(1),
            [[1, "en"], [2, "ru"]],
        )

    def test_get_audio_params3(self):
        args = Args(dvd=".", audio_params=[[1, "ru"], [2, "jp"]])
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertLessEqual(
            remux_service.get_audio_params(1),
            [[1, "ru"], [2, "jp"]],
        )

    def test_get_subs_params1(self):
        args = Args(dvd=".", subs_params=[[1, "undefined"], [2, "undefined"]])
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertLessEqual(
            remux_service.get_subs_params(1),
            [[1, "en"], [2, "ru"]],
        )

    def test_get_subs_params2(self):
        args = Args(dvd=".")
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertLessEqual(
            remux_service.get_subs_params(1),
            [[1, "en"], [2, "ru"]],
        )

    def test_get_subs_params3(self):
        args = Args(dvd=".", subs_params=[[1, "ru"], [2, "jp"]])
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertLessEqual(
            remux_service.get_subs_params(1),
            [[1, "ru"], [2, "jp"]],
        )

    def test_normalize_langcode_empty(self):
        args = Args(dvd=".")
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertEqual(remux_service._normalize_langcode("audio", 1, 0, ""), "und")

    def test_normalize_langcode_none(self):
        args = Args(dvd=".")
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertEqual(remux_service._normalize_langcode("audio", 1, 0, None), "und")

    def test_normalize_langcode_xx(self):
        args = Args(dvd=".")
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertEqual(remux_service._normalize_langcode("audio", 1, 0, "xx"), "mul")

    def test_normalize_langcode_undefined(self):
        args = Args(dvd=".")
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        self.assertEqual(
            remux_service._normalize_langcode("audio", 1, 2, "undefined"), "ru"
        )


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
        self.audio_params = args.get("audio_params")
        self.subs_params = None
        self.split_chapters = False
        self.add_sub_langcode = None


if __name__ == "__main__":
    unittest.main()
