import unittest
from dvd_remuxer import options


class TestOptions(unittest.TestCase):
    def setUp(self):
        self.argparser = options.create_argparser()

    def test_parse_args(self):
        with self.assertRaises(SystemExit) as cm:
            options.parse_args()

        self.assertEqual(cm.exception.code, 2)

    def test_path(self):
        args = self.argparser.parse_args(["."])
        self.assertEqual(args.dvd, ".")

    def test_without_path(self):
        with self.assertRaises(SystemExit) as cm:
            self.argparser.parse_args([])

        self.assertEqual(cm.exception.code, 2)

    def test_nonexistent_path(self):
        with self.assertRaises(SystemExit) as cm:
            self.argparser.parse_args(["some/none/existent/path/for/test/"])

        self.assertEqual(cm.exception.code, 2)

    def test_comma_separated_title_list(self):
        args = self.argparser.parse_args(["--dvd-title", "1,2,3", "."])
        self.assertListEqual(args.title_idx, [1, 2, 3])

    def test_title_range(self):
        args = self.argparser.parse_args(["--dvd-title", "3-8", "."])
        self.assertListEqual(args.title_idx, [3, 4, 5, 6, 7, 8])

    def test_title_range_list(self):
        args = self.argparser.parse_args(["--dvd-title", "3-5,11-13", "."])
        self.assertListEqual(args.title_idx, [3, 4, 5, 11, 12, 13])

    def test_all(self):
        args = self.argparser.parse_args(["--all", "."])
        self.assertTrue(args.all_titles)

    def test_audio(self):
        args = self.argparser.parse_args(["--audio", "2:ru,1,3:en", "."])
        self.assertListEqual(
            args.audio_params, [[2, "ru"], [1, "undefined"], [3, "en"]]
        )

    def test_subs(self):
        args = self.argparser.parse_args(["--subs", "2:ru,1,3:en", "."])
        self.assertListEqual(args.subs_params, [[2, "ru"], [1, "undefined"], [3, "en"]])

    def test_add_sub_langcode(self):
        args = self.argparser.parse_args(["--add-sub-langcode", "ru,en,jp", "."])
        self.assertListEqual(args.add_sub_langcode, ["ru", "en", "jp"])


if __name__ == "__main__":
    unittest.main()
