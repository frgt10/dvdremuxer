#!/usr/bin/env python3

import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint

wrong_lang_codes = ["xx"]


class DVDRemuxer:
    def __init__(self, device: str, dry_run: bool, keep: bool, rewrite: bool):
        self.device = device
        self.dry_run = dry_run
        self.keep_temp_files = keep
        self.rewrite = rewrite

        self.temp_files = []
        self.langcodes = ["ru", "en"]

        code_locals = {}
        data = subprocess.Popen(
            ["lsdvd", "-x", "-Oy", self.device], stdout=subprocess.PIPE
        )
        exec(data.communicate()[0], {}, code_locals)
        self.lsdvd = code_locals.get("lsdvd")

        self.file_prefix = "dvd"
        if self.lsdvd["title"] and self.lsdvd["title"] != "unknown":
            self.file_prefix = self.lsdvd["title"]

    def print_dvd_info(self) -> None:
        print("Longest title: %i" % (self.longest_title_idx()))

        for track in self.lsdvd.get("track"):
            if track.get("length") < 1:
                continue

            print()

            print("Index:", track.get("ix"))

            print("Length:", convert_seconds_to_hhmmss(track.get("length")))

            print(
                "Video:",
                track.get("format"),
                track.get("width"),
                "x",
                track.get("height"),
                track.get("aspect"),
                track.get("df"),
                track.get("fps"),
            )

            print("Audio:")
            pprint(track.get("audio"))

            if len(track["subp"]) > 0:
                print("Subtitles:")
                pprint(track.get("subp"))

            if len(track["chapter"]) > 1:
                print("Chapters:", len(track["chapter"]))

    def remux_title(self, title_idx: int) -> None:
        print("remuxing title #%i" % (title_idx))

        outfile = "%s_%i.DVDRemux.mkv" % (self.file_prefix, title_idx)

        merge_args = ["mkvmerge", "--output", outfile]

        file_stream = StreamDumper(self).dumpstream(title_idx)

        self.temp_files.append(file_stream)

        for audio in self.lsdvd["track"][title_idx - 1].get("audio"):
            if audio["langcode"] not in wrong_lang_codes:
                merge_args.append("--language")
                merge_args.append("%i:%s" % (audio["ix"], audio["langcode"]))

        merge_args.append(file_stream)

        for vobsub in self.lsdvd["track"][title_idx - 1].get("subp"):
            if vobsub["langcode"] in self.langcodes:
                file_vobsub_idx, file_vobsub_sub = VobsubDumper(self).dumpvobsub(
                    title_idx, vobsub["ix"], vobsub["langcode"]
                )

                self.temp_files.append(file_vobsub_idx)
                self.temp_files.append(file_vobsub_sub)

                merge_args.append("--language")
                merge_args.append("0:%s" % (vobsub["langcode"]))
                merge_args.append(file_vobsub_idx)

        if len(self.lsdvd["track"][title_idx - 1]["chapter"]) > 1:
            file_chapters = ChaptersDumper(self).dumpchapters(title_idx)

            self.temp_files.append(file_chapters)

            merge_args.append("--chapters")
            merge_args.append(file_chapters)

        print("merge tracks")

        if self.dry_run:
            pprint(merge_args)
        else:
            open(outfile, "w").close()
            subprocess.run(merge_args, stdout=subprocess.DEVNULL)

        if not self.keep_temp_files:
            self.__rm_temp_files()

    def __rm_temp_files(self) -> None:
        print("remove temp files")

        if self.dry_run:
            pprint(self.temp_files)
        else:
            for file in self.temp_files:
                Path(file).unlink()

    def longest_title_idx(self) -> int:
        return self.lsdvd["longest_track"]

    def all_titles_idx(self):
        titles = []
        for track in self.lsdvd.get("track"):
            if track.get("length") < 1:
                continue

            titles.append(track.get("ix"))

        return titles


class StreamDumper:
    def __init__(self, remuxer: DVDRemuxer):
        self.remuxer = remuxer

    def dumpstream(self, title_idx: int) -> str:
        print("dump stream")

        outfile = "%s_%i_video.vob" % (self.remuxer.file_prefix, title_idx)

        if not Path(outfile).exists() or self.remuxer.rewrite:
            dump_args = [
                "mplayer",
                "-dvd-device",
                self.remuxer.device,
                "dvd://%i" % (title_idx),
                "-dumpstream",
                "-dumpfile",
                outfile,
            ]

            if self.remuxer.dry_run:
                pprint(dump_args)
            else:
                subprocess.run(
                    dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

        return outfile


class ChaptersDumper:
    def __init__(self, remuxer: DVDRemuxer):
        self.remuxer = remuxer

    def dumpchapters(self, title_idx: int) -> str:
        print("dump chapters")

        outfile = "%s_%i_chapters.txt" % (self.remuxer.file_prefix, title_idx)

        if not Path(outfile).exists() or self.remuxer.rewrite:
            start = 0.000
            chapters = ""

            for chapter in self.remuxer.lsdvd["track"][title_idx - 1].get("chapter"):
                chapters += "CHAPTER%02d=%s\n" % (
                    chapter["ix"],
                    convert_seconds_to_hhmmss(start),
                )
                chapters += "CHAPTER%02dNAME=\n" % (chapter["ix"])

                start += chapter["length"]

            if not self.remuxer.dry_run:
                with open(outfile, "w") as f:
                    print(chapters, file=f)

        return outfile


class VobsubDumper:
    def __init__(self, remuxer: DVDRemuxer):
        self.remuxer = remuxer

    def dumpvobsub(self, title_idx: int, sub_ix: int, langcode: str):
        print("extracting subtitle %i lang %s" % (sub_ix, langcode))

        outfile = "%s_%i_vobsub_%i_%s" % (
            self.remuxer.file_prefix,
            title_idx,
            sub_ix,
            langcode,
        )

        if (
            not (Path(outfile + ".idx").exists() and Path(outfile + ".sub").exists())
            or self.remuxer.rewrite
        ):
            dump_args = [
                "mencoder",
                "-dvd-device",
                self.remuxer.device,
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

            if self.remuxer.dry_run:
                pprint(dump_args)
            else:
                open(outfile + ".idx", "w").close()
                open(outfile + ".sub", "w").close()
                subprocess.run(
                    dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

        return outfile + ".idx", outfile + ".sub"


def convert_seconds_to_hhmmss(seconds: float) -> str:
    return (datetime.utcfromtimestamp(0) + timedelta(seconds=seconds)).strftime(
        "%H:%M:%S.%f"
    )[:-3]