#!/usr/bin/env python3

from __future__ import annotations

import sys
import subprocess
import ast
import re


class lsdvd:
    def __init__(self, device: str):
        self.device = device
        self.output = self.get_lsdvd_output(device)
        self.dvd_info = self.get_dvd_info(self.output)

    def get_dvd_info(self, lsdvd_output: str) -> dict:
        lsdvd_output = self.clear_lsdvd_output(lsdvd_output)

        lsdvd_data = ""

        try:
            lsdvd_data = ast.literal_eval(lsdvd_output)
        except Exception as inst:
            print(inst)
            print(lsdvd_data[:1024])
            sys.exit(2)

        return lsdvd_data

    @staticmethod
    def clear_lsdvd_output(lsdvd_output: str) -> str:
        return re.sub("(?m)^libdvdread:.*\n?", "", lsdvd_output).replace("lsdvd = ", "")

    @staticmethod
    def get_lsdvd_output(device: str) -> str:
        data = subprocess.Popen(["lsdvd", "-x", "-Oy", device], stdout=subprocess.PIPE)
        return data.communicate()[0].decode("utf-8", errors="ignore")

    def longest_title_idx(self) -> int:
        return self.dvd_info["longest_track"]
