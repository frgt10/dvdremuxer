#!/usr/bin/env python3

from __future__ import annotations

import sys
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint
import ast
import re

wrong_lang_codes = ["xx", ""]


class DVDRemuxer:
    def __init__(self, device: str, **options):
        self.device = device
        self.dry_run = options.get("dry_run")
        self.keep_temp_files = options.get("keep_temp_files")
        self.rewrite = options.get("rewrite")
        self.aspect_ratio = options.get("aspect_ratio")
        self.audio_params = options.get("audio_params") or []
        self.subs_params = options.get("subs_params") or []
        self.verbose = options.get("verbose")
        self.tmp_dir_obj = None

        if options.get("use_sys_tmp_dir"):
            self.tmp_dir_obj = tempfile.TemporaryDirectory(prefix="_dvdremux")
            self.tmp_dir = Path(self.tmp_dir_obj.name)
        else:
            self.tmp_dir = Path.cwd()

        if self.verbose:
            print("Temp directory: %s" % (self.tmp_dir))

        self.temp_files = []
        self.langcodes = ["ru", "en"]

        data = subprocess.Popen(
            ["lsdvd", "-x", "-Oy", self.device], stdout=subprocess.PIPE
        )
        data_code = (
            data.communicate()[0]
            .decode("utf-8", errors="ignore")
            .replace("lsdvd = ", "")
        )

        try:
            self.lsdvd = ast.literal_eval(
                re.sub("(?m)^libdvdread:.*\n?", "", data_code)
            )
        except Exception as inst:
            print(inst)
            print(data_code[:1024])
            sys.exit(2)

        if not self.lsdvd:
            raise Exception("Path is not valid video DVD")

        self.file_prefix = "dvd"
        if self.lsdvd["title"] and self.lsdvd["title"] != "unknown":
            self.file_prefix = self.lsdvd["title"]

    def dvd_info(self) -> None:
        self._subprocess_run(["lsdvd", "-x", self.device])

    def remux_to_mkv(self, title_idx: int) -> None:
        print("remuxing title #%i" % (title_idx))

        outfile = Path("%s_%i.DVDRemux.mkv" % (self.file_prefix, title_idx))

        merge_args = ["mkvmerge", "--output", outfile]

        file_stream = self.dumpstream(title_idx)

        in_file_number = 0  # audio and video in first file

        self.temp_files.append(file_stream)

        # video from file_stream is first track
        track_order = "%i:0" % (in_file_number)

        # audio params from command line argumets
        if self.audio_params:
            audio_tracks = []
            for audio_idx, langcode in self.audio_params:
                langcode = self._normalize_langcode(
                    "audio", title_idx, audio_idx, langcode
                )

                audio_tracks.append(str(audio_idx))

                merge_args.append("--language")
                merge_args.append("%i:%s" % (audio_idx, langcode))

                # audio from file_stream just after video
                track_order += ",%i:%s" % (in_file_number, audio_idx)

            # set the necessary audio tracks
            merge_args.append("--audio-tracks")
            merge_args.append(str.join(",", audio_tracks))

        # or all audio from DVD title
        else:
            for audio in self.lsdvd["track"][title_idx - 1].get("audio"):
                langcode = self._normalize_langcode(
                    "audio", title_idx, audio["ix"], audio["langcode"]
                )
                merge_args.append("--language")
                merge_args.append("%i:%s" % (audio["ix"], langcode))

                # audio from file_stream just after video
                track_order += ",%i:%s" % (in_file_number, audio["ix"])

        if self.aspect_ratio:
            merge_args.append("--aspect-ratio")
            merge_args.append("0:%s" % (self.aspect_ratio))

        merge_args.append(file_stream)

        for sub_idx, langcode in self._get_title_subs_params(title_idx):
            langcode = self._normalize_langcode("vobp", title_idx, sub_idx, langcode)

            file_vobsub_idx, file_vobsub_sub = self.dumpvobsub(
                title_idx, sub_idx, langcode
            )

            in_file_number += 1  # each subtitle track in separate file

            self.temp_files.append(file_vobsub_idx)
            self.temp_files.append(file_vobsub_sub)

            merge_args.append("--language")
            merge_args.append("0:%s" % (langcode))
            merge_args.append(file_vobsub_idx)

            # subtitle just after audio
            track_order += ",%i:0" % (in_file_number)

        if len(self.lsdvd["track"][title_idx - 1]["chapter"]) > 1:
            file_chapters = self.dumpchapters(title_idx)

            self.temp_files.append(file_chapters)

            merge_args.append("--chapters")
            merge_args.append(file_chapters)

        merge_args.append("--track-order")
        merge_args.append(track_order)

        print("merge tracks")

        self._subprocess_run(merge_args)

        if not self.dry_run:
            try:
                if outfile.stat().st_size == 0:
                    # An error occurred during the merge.
                    # Unlink file of zero size.
                    outfile.unlink()
            except:
                print("Oops! %s" % outfile)

        if not self.keep_temp_files and not self.tmp_dir_obj:
            self._rm_temp_files()

    def _rm_temp_files(self) -> None:
        print("remove temp files")

        if self.dry_run:
            pprint(self.temp_files)
        else:
            while self.temp_files:
                try:
                    self.temp_files.pop().unlink()
                except:
                    print("Oops!")

    def longest_title_idx(self) -> int:
        return self.lsdvd["longest_track"]

    def all_titles_idx(self):
        titles = []
        for track in self.lsdvd.get("track"):
            if track.get("length") < 1:
                continue

            titles.append(track.get("ix"))

        return titles

    def dumpstream(self, title_idx: int) -> Path:
        print("dump stream")

        outfile = self.tmp_dir / ("%s_%i_video.vob" % (self.file_prefix, title_idx))

        if not outfile.exists() or self.rewrite:
            dump_args = [
                "mplayer",
                "-dvd-device",
                self.device,
                "dvd://%i" % (title_idx),
                "-dumpstream",
                "-dumpfile",
                outfile,
            ]

            self._subprocess_run(
                dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

        return outfile

    def dumpchapters(self, title_idx: int) -> Path:
        print("dump chapters")

        outfile = self.tmp_dir / ("%s_%i_chapters.txt" % (self.file_prefix, title_idx))

        if not outfile.exists() or self.rewrite:
            start = 0.000
            chapters = ""

            for chapter in self.lsdvd["track"][title_idx - 1].get("chapter"):
                chapters += "CHAPTER%02d=%s\n" % (
                    chapter["ix"],
                    convert_seconds_to_hhmmss(start),
                )
                chapters += "CHAPTER%02dNAME=\n" % (chapter["ix"])

                start += chapter["length"]

            if self.verbose:
                print(chapters)

            if not self.dry_run:
                with outfile.open(mode="w") as f:
                    print(chapters, file=f)

        return outfile

    def dumpvobsubs(self, title_idx: int):
        for vobsub in self.lsdvd["track"][title_idx - 1].get("subp"):
            if vobsub["langcode"] in self.langcodes:
                self.dumpvobsub(title_idx, vobsub["ix"], vobsub["langcode"])

    def dumpvobsub(self, title_idx: int, sub_ix: int, langcode: str):
        print("extracting subtitle %i lang %s" % (sub_ix, langcode))

        outfile = self.tmp_dir / (
            "%s_%i_vobsub_%i_%s" % (self.file_prefix, title_idx, sub_ix, langcode)
        )

        outfile_idx = outfile.with_suffix(".idx")
        outfile_sub = outfile.with_suffix(".sub")

        if not (outfile_idx.exists() and outfile_sub.exists()) or self.rewrite:
            dump_args = [
                "mencoder",
                "-dvd-device",
                self.device,
                "dvd://%i" % (title_idx),
                "-vobsubout",
                outfile,
                "-vobsuboutindex",
                "%i" % (sub_ix),
                "-sid",
                "%i" % (sub_ix - 1),
                "-ovc",
                "copy",
                "-oac",
                "copy",
                "-nosound",
                "-o",
                "/dev/null",
                "-vf",
                "harddup",
            ]

            if not self.dry_run:
                outfile_idx.open(mode="w").close()
                outfile_sub.open(mode="w").close()

            self._subprocess_run(
                dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

        self._fix_vobsub_lang_id(outfile_idx, langcode)

        return outfile_idx, outfile_sub

    def _fix_vobsub_lang_id(self, idx_file: Path, langcode: str):
        f = idx_file.open(mode="r")
        content = f.read()
        f.close()
        content_new = re.sub(
            "id: , index", f"id: {langcode}, index", content, flags=re.M
        )

        if content != content_new:
            f = idx_file.open(mode="w")
            f.write(content_new)
            f.close()

    def list_languages(self) -> None:
        self._subprocess_run(["mkvmerge", "--list-languages"])

    def _subprocess_run(self, cmd: list, **kwargs) -> None:
        if self.dry_run or self.verbose:
            print(subprocess.list2cmdline(cmd))

        if not self.dry_run:
            subprocess.run(cmd, **kwargs)

    def _get_title_subs_params(self, title_idx: int) -> list:
        subs_params = []

        if self.subs_params:
            subs_params = self.subs_params
        else:
            for vobsub in self.lsdvd["track"][title_idx - 1].get("subp"):
                if vobsub["langcode"] in self.langcodes:
                    subs_params.append([vobsub["ix"], vobsub["langcode"]])

        return subs_params

    def _normalize_langcode(
        self, type: str, title_idx: int, idx: int, langcode: str
    ) -> str:
        if langcode == "undefined":
            langcode = self.lsdvd["track"][title_idx - 1][type][idx - 1]["langcode"]

        if langcode in wrong_lang_codes:
            langcode = "und"

        return langcode


def convert_seconds_to_hhmmss(seconds: float) -> str:
    return (datetime.utcfromtimestamp(0) + timedelta(seconds=seconds)).strftime(
        "%H:%M:%S.%f"
    )[:-3]
