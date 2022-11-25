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
      'audio' : [
        {
          'ix' : 1,
          'langcode' : 'en',
        },
        {
          'ix' : 2,
          'langcode' : 'ru',
        },
      ],
      'chapter' : [
        {
          'ix' : 1,
          'length' : 100.880,
          'startcell' : 1,
        },
        {
          'ix' : 2,
          'length' : 69.160,
          'startcell' : 2,
        },
        {
          'ix' : 3,
          'length' : 78.000,
          'startcell' : 3,
        },
      ],
      'subp' : [
        {
          'ix' : 1,
          'langcode' : 'ru',
        },
        {
          'ix' : 2,
          'langcode' : 'fr',
        },
      ],
    },
    {
      'ix' : 2,
      'length' : 600.000,
      'chapter' : [],
    },
    {
      'ix' : 3,
      'length' : 300.000,
      'chapter' : [],
    },
    {
      'ix' : 4,
      'length' : 0.100,
      'chapter' : [],
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

    @staticmethod
    def get_printable_dvd_info(device: str) -> str:
        return "Disc Title: TEST_DVD"
