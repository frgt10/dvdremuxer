#!/usr/bin/env python3

import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint


wrong_lang_codes = ["xx"]


class DVDRemuxer:
    def __init__(self, device: str, **options):
        self.device = device
        self.dry_run = options.get("dry_run")
        self.keep_temp_files = options.get("keep_temp_files")
        self.rewrite = options.get("rewrite")
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

        code_locals = {}
        data = subprocess.Popen(
            ["lsdvd", "-x", "-Oy", self.device], stdout=subprocess.PIPE
        )
        exec(data.communicate()[0], {}, code_locals)
        self.lsdvd = code_locals.get("lsdvd")

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

        in_file_number = 0

        self.temp_files.append(file_stream)

        # video from file_stream is first track
        track_order = "%i:0" % (in_file_number)

        for audio in self.lsdvd["track"][title_idx - 1].get("audio"):
            if audio["langcode"] not in wrong_lang_codes:
                merge_args.append("--language")
                merge_args.append("%i:%s" % (audio["ix"], audio["langcode"]))

            # audio from file_stream just after video
            track_order += ",%i:%s" % (in_file_number, audio["ix"])

        merge_args.append(file_stream)

        for vobsub in self.lsdvd["track"][title_idx - 1].get("subp"):
            if vobsub["langcode"] in self.langcodes:
                file_vobsub_idx, file_vobsub_sub = self.dumpvobsub(
                    title_idx, vobsub["ix"], vobsub["langcode"]
                )

                in_file_number += 1  # each subtitle track in separate file

                self.temp_files.append(file_vobsub_idx)
                self.temp_files.append(file_vobsub_sub)

                merge_args.append("--language")
                merge_args.append("0:%s" % (vobsub["langcode"]))
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
            if outfile.stat().st_size == 0:
                # An error occurred during the merge.
                # Unlink file of zero size.
                outfile.unlink()

        if not self.keep_temp_files and not self.tmp_dir_obj:
            self._rm_temp_files()

    def _rm_temp_files(self) -> None:
        print("remove temp files")

        if self.dry_run:
            pprint(self.temp_files)
        else:
            while self.temp_files:
                self.temp_files.pop().unlink()

    def longest_title_idx(self) -> int:
        return self.lsdvd["longest_track"]

    def all_titles_idx(self):
        titles = []
        for track in self.lsdvd.get("track"):
            if track.get("length") < 1:
                continue

            titles.append(track.get("ix"))

        return titles

    def dumpstream(self, title_idx: int) -> str:
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

            self.subprocess_run(
                dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

        return outfile

    def dumpchapters(self, title_idx: int) -> str:
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

        return outfile_idx, outfile_sub

    def list_languages(self) -> None:
        self._subprocess_run(["mkvmerge", "--list-languages"])

    def _subprocess_run(self, cmd, **options) -> None:
        if self.dry_run or self.verbose:
            pprint(cmd)

        if not self.dry_run:
            subprocess.run(cmd, **options)


def convert_seconds_to_hhmmss(seconds: float) -> str:
    return (datetime.utcfromtimestamp(0) + timedelta(seconds=seconds)).strftime(
        "%H:%M:%S.%f"
    )[:-3]
