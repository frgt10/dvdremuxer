import unittest
from unittest.mock import MagicMock

from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class TestDVDRemuxInit(unittest.TestCase):
    def test_without_lsdvd(self):
        with self.assertRaises(Exception) as cm:
            self.remuxer = DVDRemuxerTest(".", lsdvd=None)


if __name__ == "__main__":
    unittest.main()
