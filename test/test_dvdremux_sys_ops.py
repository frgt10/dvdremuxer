import unittest
from unittest.mock import patch
from pathlib import Path

from dvd_remuxer.dvdremux import DVDRemuxer
from .lsdvd import lsdvd_test


class TestDVDRemuxSysOps(unittest.TestCase):
    def setUp(self):
        self.remuxer = DVDRemuxer(
            ".",
            lsdvd=lsdvd_test.read("."),
        )

    def test_unlink_empty_file(self):
        file_empty = Path("test_empty_file")
        file_empty.open(mode="w").close()

        self.remuxer._unlink_empty_file(file_empty)

        is_exists = False

        if file_empty.exists():
            is_exists = True
            file_empty.unlink()

        self.assertFalse(is_exists)

    def test_unlink_empty_file_with_notempty_file(self):
        file_notempty = Path("test_notempty_file")
        with file_notempty.open(mode="w") as f:
            print(
                "This is not enpty file for testing DVDRemuxer._unlink_empty_file method",
                file=f,
            )

        self.remuxer._unlink_empty_file(file_notempty)

        is_exists = False

        if file_notempty.exists():
            is_exists = True
            file_notempty.unlink()

        self.assertTrue(is_exists)

    def test_unlink_empty_file_dry_run(self):
        self.remuxer.dry_run = True

        with patch.object(Path, "unlink") as mock_unlink:
            file_empty = Path("test_empty_file")
            self.remuxer._unlink_empty_file(file_empty)

        mock_unlink.assert_not_called()


if __name__ == "__main__":
    unittest.main()
