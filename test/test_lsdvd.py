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
    def setUp(self):
        self.lsdvd = lsdvd()

    def test_get_lsdvd_output(self):
        output = self.lsdvd.get_lsdvd_output(".")

        self.assertIn("libdvdread: Encrypted DVD support unavailable.", output)

    @patch.object(lsdvd, "get_lsdvd_output")
    def test_clear_lsdvd_output1(self, mock_out):
        mock_out.return_value = lsdvd_otput
        self.assertNotIn("lsdvd = ", self.lsdvd.clear_lsdvd_output(lsdvd_otput))

    @patch.object(lsdvd, "get_lsdvd_output")
    def test_clear_lsdvd_output2(self, mock_out):
        mock_out.return_value = lsdvd_otput
        self.assertNotIn("libdvdread:", self.lsdvd.clear_lsdvd_output(lsdvd_otput))

    @patch.object(lsdvd, "get_lsdvd_output")
    def test_get_dvd_info(self, mock_out):
        mock_out.return_value = lsdvd_otput
        self.assertDictEqual(
            self.lsdvd.get_dvd_info("."),
            {
                "device": ".",
                "title": "TEST_DVD",
                "track": [],
                "longest_track": 1,
            },
        )

    @patch.object(lsdvd, "get_lsdvd_output")
    def test_get_dvd_info_raise(self, mock_out):
        mock_out.return_value = incorrect_lsdvd_otput
        with self.assertRaises(SystemExit) as cm:
            self.lsdvd.get_dvd_info(".")

        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
