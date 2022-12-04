import unittest

from dvd_remuxer.remux_service import RemuxService
from dvd_remuxer.lsdvd import lsdvd
from .dvdremux_test import DVDRemuxerTest
from .lsdvd_test import lsdvd_test


class TestRemuxService(unittest.TestCase):
    def test_init_without_lsdvd(self):
        args = Args(dvd=".")
        with self.assertRaises(Exception) as cm:
            RemuxService(lsdvd, DVDRemuxerTest, args)

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
            [[1, "ru"], [2, "fr"]],
        )

    def test_get_subs_params2(self):
        args = Args(dvd=".")
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        remux_service.run()
        self.assertLessEqual(
            remux_service.get_subs_params(1),
            [[1, "ru"]],
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

    def test_get_titles(self):
        args = Args(dvd=".", title_idx=[1, 2])
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        remux_service.run()
        self.assertListEqual(remux_service._get_titles(), [1, 2])

    def test_get_titles_all(self):
        args = Args(dvd=".", all_titles=True)
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        remux_service.run()
        self.assertListEqual(remux_service._get_titles(), [1, 2, 3])

    def test_run_dvd_info(self):
        args = Args(dvd=".", info=True)

        with self.assertRaises(SystemExit) as cm:
            RemuxService(lsdvd_test, DVDRemuxerTest, args).run()

        self.assertEqual(cm.exception.code, 0)

    def test_add_sub_langcode(self):
        args = Args(dvd=".", add_sub_langcode=["jp", "fr"])
        remux_service = RemuxService(lsdvd_test, DVDRemuxerTest, args)
        remux_service.run()
        self.assertListEqual(remux_service.langcodes, ["ru", "en", "jp", "fr"])

    def test_run_verbose(self):
        args = Args(dvd=".", verbose=True)
        RemuxService(lsdvd_test, DVDRemuxerTest, args).run()
        pass

    def test_run_stream(self):
        args = Args(dvd=".", action="stream")
        RemuxService(lsdvd_test, DVDRemuxerTest, args).run()
        pass

    def test_run_subs(self):
        args = Args(dvd=".", action="subs")
        RemuxService(lsdvd_test, DVDRemuxerTest, args).run()
        pass

    def test_run_chapters(self):
        args = Args(dvd=".", action="chapters")
        RemuxService(lsdvd_test, DVDRemuxerTest, args).run()
        pass


class Args:
    def __init__(self, **args) -> None:
        self.dvd = args.get("dvd")
        self.action = args.get("action") or "remux_to_mkv"
        self.title_idx = args.get("title_idx")
        self.all_titles = args.get("all_titles")
        self.info = args.get("info") or False
        self.verbose = args.get("verbose") or False
        self.dry_run = args.get("dry_run") or False
        self.keep = args.get("keep") or False
        self.rewrite = args.get("rewrite") or False
        self.use_sys_tmp_dir = args.get("use_sys_tmp_dir") or False
        self.aspect_ratio = args.get("aspect_ratio")
        self.audio_params = args.get("audio_params")
        self.subs_params = args.get("subs_params")
        self.split_chapters = args.get("split_chapters") or False
        self.add_sub_langcode = args.get("add_sub_langcode")


if __name__ == "__main__":
    unittest.main()
