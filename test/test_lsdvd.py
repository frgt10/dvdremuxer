import unittest

from dvd_remuxer.lsdvd import lsdvd
from .lsdvd import lsdvd_test, lsdvd_otput, incorrect_lsdvd_otput


class TestLsDVD(unittest.TestCase):
    def setUp(self):
        self.lsdvd = lsdvd_test.read(".")

    def test_get_lsdvd_output(self):
        output = lsdvd.get_lsdvd_output(".")

        self.assertIn("libdvdread: Encrypted DVD support unavailable.", output)

    def test_clear_lsdvd_output1(self):
        self.assertNotIn("lsdvd = ", lsdvd_test.clear_lsdvd_output(lsdvd_otput))

    def test_clear_lsdvd_output2(self):
        self.assertNotIn("libdvdread:", lsdvd_test.clear_lsdvd_output(lsdvd_otput))

    def test_get_dvd_info(self):
        self.assertDictEqual(
            lsdvd_test.get_dvd_info(lsdvd_otput),
            {
                "device": ".",
                "title": "TEST_DVD",
                "track": [
                    {
                        "ix": 1,
                        "length": 3600.000,
                    },
                    {
                        "ix": 2,
                        "length": 600.000,
                    },
                    {
                        "ix": 3,
                        "length": 300.000,
                    },
                    {
                        "ix": 4,
                        "length": 0.100,
                    },
                ],
                "longest_track": 1,
            },
        )

    def test_get_dvd_info_raise(self):
        with self.assertRaises(SystemExit) as cm:
            lsdvd_test.get_dvd_info(incorrect_lsdvd_otput)

        self.assertEqual(cm.exception.code, 2)

    def test_all_titles_idx(self):
        self.assertListEqual(self.lsdvd.all_titles_idx(), [1, 2, 3])

    def test_longest_title_idx(self):
        self.assertEqual(self.lsdvd.longest_title_idx(), 1)


if __name__ == "__main__":
    unittest.main()
