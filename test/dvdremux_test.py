#!/usr/bin/env python3

from __future__ import annotations
from pathlib import Path

from dvd_remuxer.dvdremux import DVDRemuxer


class DVDRemuxerTest(DVDRemuxer):
    def _subprocess_run(self, cmd: list, **kwargs) -> None:
        pass

    def _save_to_file(self, outfile: Path, data: str) -> None:
        pass

    def _clear_file(self, file: Path) -> None:
        pass

    def _fix_vobsub_lang_id(self, idx_file: Path, langcode: str):
        pass

    def _rm_temp_files(self) -> None:
        pass
