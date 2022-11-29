#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import ast
import re
import json


class lsdvd:
    def __init__(self, lsdvd_dict):
        self.__dict__.update(lsdvd_dict)

    @classmethod
    def read(cls, device: str) -> lsdvd:
        data_dict = cls.get_dvd_info(cls.get_lsdvd_output(device))

        # using json.loads method and passing json.dumps
        # method and custom object hook as arguments
        lsdvd_obj = json.loads(json.dumps(data_dict), object_hook=cls)

        return lsdvd_obj

    @staticmethod
    def get_dvd_info(lsdvd_output: str) -> dict:
        lsdvd_output = lsdvd.clear_lsdvd_output(lsdvd_output)

        lsdvd_data = ""

        try:
            lsdvd_data = ast.literal_eval(lsdvd_output)
        except Exception as inst:
            print(inst)
            print(lsdvd_data[:1024])
            raise Exception("Path is not valid video DVD")

        return lsdvd_data

    @staticmethod
    def get_printable_dvd_info(device: str) -> str:
        subprocess.run(["lsdvd", "-x", device])

    @staticmethod
    def clear_lsdvd_output(lsdvd_output: str) -> str:
        return re.sub("(?m)^libdvdread:.*\n?", "", lsdvd_output).replace("lsdvd = ", "")

    @staticmethod
    def get_lsdvd_output(device: str) -> str:
        data = subprocess.Popen(["lsdvd", "-x", "-Oy", device], stdout=subprocess.PIPE)
        return data.communicate()[0].decode("utf-8", errors="ignore")

    def all_titles_idx(self) -> list:
        titles = []
        for track in self.track:
            if track.length < 1:
                continue

            titles.append(track.ix)

        return titles

    def longest_title_idx(self) -> int:
        return self.longest_track
