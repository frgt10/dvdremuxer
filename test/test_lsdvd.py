import unittest

from unittest.mock import patch

from dvd_remuxer.lsdvd import lsdvd

lsdvd_otput = """libdvdread: Encrypted DVD support unavailable.
lsdvd = {
  'device' : '.',
  'title' : 'TEST_DVD',
  'track' : [],
  'longest_track' : 1,
}
"""

incorrect_lsdvd_otput = """{
  'device' : '.',
  'title' : 'TEST_DVD'
"""


class TestLsDVD(unittest.TestCase):
    @patch.object(lsdvd, "get_lsdvd_output")
    def setUp(self, mock_out):
        mock_out.return_value = lsdvd_otput
        self.lsdvd = lsdvd(".")

    def test_get_lsdvd_output(self):
        output = lsdvd.get_lsdvd_output(".")

        self.assertIn("libdvdread: Encrypted DVD support unavailable.", output)

    def test_clear_lsdvd_output1(self):
        self.assertNotIn("lsdvd = ", lsdvd.clear_lsdvd_output(lsdvd_otput))

    def test_clear_lsdvd_output2(self):
        self.assertNotIn("libdvdread:", lsdvd.clear_lsdvd_output(lsdvd_otput))

    def test_get_dvd_info(self):
        self.assertDictEqual(
            self.lsdvd.get_dvd_info(lsdvd_otput),
            {
                "device": ".",
                "title": "TEST_DVD",
                "track": [],
                "longest_track": 1,
            },
        )

    def test_get_dvd_info_raise(self):
        with self.assertRaises(SystemExit) as cm:
            self.lsdvd.get_dvd_info(incorrect_lsdvd_otput)

        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
