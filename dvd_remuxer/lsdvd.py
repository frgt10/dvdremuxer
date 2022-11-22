#!/usr/bin/env python3

from __future__ import annotations

import sys
import subprocess
import ast
import re


class lsdvd:
    def get_dvd_info(self, device: str) -> dict:
        lsdvd_output = self.clear_lsdvd_output(self.get_lsdvd_output(device))

        lsdvd_data = ""

        try:
            lsdvd_data = ast.literal_eval(lsdvd_output)
        except Exception as inst:
            print(inst)
            print(lsdvd_data[:1024])
            sys.exit(2)

        return lsdvd_data

    def clear_lsdvd_output(self, lsdvd_output: str) -> str:
        return re.sub("(?m)^libdvdread:.*\n?", "", lsdvd_output).replace("lsdvd = ", "")

    def get_lsdvd_output(self, device: str) -> str:
        data = subprocess.Popen(["lsdvd", "-x", "-Oy", device], stdout=subprocess.PIPE)
        return data.communicate()[0].decode("utf-8", errors="ignore")
