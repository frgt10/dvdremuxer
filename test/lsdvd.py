#!/usr/bin/env python3

from __future__ import annotations

from dvd_remuxer.lsdvd import lsdvd

lsdvd_otput = """libdvdread: Encrypted DVD support unavailable.
lsdvd = {
  'device' : '.',
  'title' : 'TEST_DVD',
  'track' : [
    {
      'ix' : 1,
      'length' : 3600.000,
    },
    {
      'ix' : 2,
      'length' : 600.000,
    },
    {
      'ix' : 3,
      'length' : 300.000,
    },
    {
      'ix' : 4,
      'length' : 0.100,
    },
  ],
  'longest_track' : 1,
}
"""

incorrect_lsdvd_otput = """{
  'device' : '.',
  'title' : 'TEST_DVD'
"""


class lsdvd_test(lsdvd):
    @staticmethod
    def get_lsdvd_output(device: str) -> str:
        return lsdvd_otput
