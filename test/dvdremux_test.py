#!/usr/bin/env python3

from __future__ import annotations

from dvd_remuxer.dvdremux import DVDRemuxer


class DVDRemuxerTest(DVDRemuxer):
    def _subprocess_run(self, cmd: list, **kwargs) -> None:
        pass
