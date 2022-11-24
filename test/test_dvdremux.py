import unittest

from tempfile import TemporaryDirectory
from .dvdremux_test import DVDRemuxerTest
from .lsdvd import lsdvd_test


class TestDVDRemuxInit(unittest.TestCase):
    def test_use_sys_tmp_dir(self):
        self.remuxer = DVDRemuxerTest(
            ".",
            lsdvd=lsdvd_test.read("."),
            use_sys_tmp_dir=True,
        )

        self.assertIsInstance(self.remuxer.tmp_dir_obj, TemporaryDirectory)


if __name__ == "__main__":
    unittest.main()
