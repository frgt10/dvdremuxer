import unittest
from unittest.mock import patch
from pathlib import Path

from dvd_remuxer.dvdremux import DVDRemuxer
from .lsdvd_test import lsdvd_test


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

    def test_clear_file(self):
        file_notempty = Path("test_notempty_file")
        with file_notempty.open(mode="w") as f:
            print(
                "This is not enpty file for testing DVDRemuxer._clear_file method",
                file=f,
            )

        self.remuxer._clear_file(file_notempty)

        self.assertEqual(file_notempty.stat().st_size, 0)

        file_notempty.unlink()

    def test_clear_file_dry_run(self):
        self.remuxer.dry_run = True

        with patch.object(Path, "unlink") as mock_unlink:
            file_notempty = Path("test_notempty_file")
            self.remuxer._clear_file(file_notempty)

        mock_unlink.assert_not_called()

    def test_rm_temp_files(self):
        file_for_remove1 = Path("file_for_remove1")
        file_for_remove2 = Path("file_for_remove2")
        file_for_remove1.open(mode="w").close()
        file_for_remove2.open(mode="w").close()
        self.assertTrue(file_for_remove1.exists())
        self.assertTrue(file_for_remove2.exists())
        self.remuxer.temp_files.append(file_for_remove1)
        self.remuxer.temp_files.append(file_for_remove2)

        self.remuxer._rm_temp_files()

        self.assertListEqual(self.remuxer.temp_files, [])

        file_for_remove1_exists = False
        file_for_remove2_exists = False

        if file_for_remove1.exists():
            file_for_remove1_exists = True
            file_for_remove1.unlink()

        if file_for_remove2.exists():
            file_for_remove2_exists = True
            file_for_remove2.unlink()

        self.assertFalse(file_for_remove1_exists)
        self.assertFalse(file_for_remove2_exists)

    def test_rm_temp_files_dry_run(self):
        self.remuxer.dry_run = True

        with patch.object(Path, "unlink") as mock_unlink:
            self.remuxer._rm_temp_files()

        mock_unlink.assert_not_called()


if __name__ == "__main__":
    unittest.main()
