import unittest
from dvd_remuxer.dvdremux import convert_seconds_to_hhmmss


class Test_convert_seconds_to_hhmmss(unittest.TestCase):
    def test_convert_seconds_to_hhmmss(self):
        output = convert_seconds_to_hhmmss(3600 + 23 * 60 + 45)

        self.assertEqual(output, "01:23:45.000")


if __name__ == "__main__":
    unittest.main()
