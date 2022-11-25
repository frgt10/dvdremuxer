#!/usr/bin/env python3

from __future__ import annotations

import subprocess
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint
import re

wrong_lang_codes = ["xx", ""]


class DVDRemuxer:
    def __init__(self, device: str, **options):
        self.device = device
        self.lsdvd = options.get("lsdvd")
        self.dry_run = options.get("dry_run")
        self.keep_temp_files = options.get("keep_temp_files")
        self.rewrite = options.get("rewrite")
        self.aspect_ratio = options.get("aspect_ratio")
        self.audio_params = options.get("audio_params") or []
        self.subs_params = options.get("subs_params") or []
        self.split_chapters = options.get("split_chapters")
        self.verbose = options.get("verbose")
        self.tmp_dir_obj = None

        if options.get("use_sys_tmp_dir"):
            self.tmp_dir_obj = TemporaryDirectory(prefix="_dvdremux")
            self.tmp_dir = Path(self.tmp_dir_obj.name)
        else:
            self.tmp_dir = Path.cwd()

        if self.verbose:
            print("Temp directory: %s" % (self.tmp_dir))

        self.temp_files = []
        self.langcodes = ["ru", "en"]

        if not self.lsdvd:
            raise Exception("Path is not valid video DVD")

        self.file_prefix = "dvd"
        if self.lsdvd.title and self.lsdvd.title != "unknown":
            self.file_prefix = self.lsdvd.title

    def dvd_info(self) -> None:
        self._subprocess_run(["lsdvd", "-x", self.device])

    def remux_to_mkv(self, title_idx: int) -> None:
        print(
            "remuxing title #%i (%s)"
            % (title_idx, convert_seconds_to_hhmmss(self.lsdvd.track[title_idx].length))
        )

        outfile = Path("%s_%i.DVDRemux.mkv" % (self.file_prefix, title_idx))

        mkvmerge_cmd = self.gen_mkvmerge_cmd(title_idx)

        file_stream = self.dumpstream(title_idx)
        self.temp_files.append(file_stream)

        for sub_idx, langcode in self._get_title_subs_params(title_idx):
            langcode = self._normalize_langcode("vobp", title_idx, sub_idx, langcode)

            file_vobsub_idx, file_vobsub_sub = self.dumpvobsub(
                title_idx, sub_idx, langcode
            )

            self.temp_files.append(file_vobsub_idx)
            self.temp_files.append(file_vobsub_sub)

        file_chapters = self.dumpchapters(title_idx)
        self.temp_files.append(file_chapters)

        print("merge tracks")
        self._subprocess_run(mkvmerge_cmd)

        # Unlink а zero size file, when error occurred during the merge.
        self._unlink_empty_file(outfile)

        if not self.keep_temp_files and not self.tmp_dir_obj:
            print("remove temp files")
            self._rm_temp_files()

        return outfile

    def gen_mkvmerge_cmd(self, title_idx: int) -> list():
        outfile = Path("%s_%i.DVDRemux.mkv" % (self.file_prefix, title_idx))

        merge_args = ["mkvmerge", "--output", outfile]

        in_file_number = 0  # audio and video in first file

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
                track_order += ",%i:%i" % (in_file_number, audio_idx)

            # set the necessary audio tracks
            merge_args.append("--audio-tracks")
            merge_args.append(str.join(",", audio_tracks))

        # or all audio from DVD title
        else:
            for audio in self.lsdvd.track[title_idx - 1].audio:
                langcode = self._normalize_langcode(
                    "audio", title_idx, audio.ix, audio.langcode
                )
                merge_args.append("--language")
                merge_args.append("%i:%s" % (audio.ix, langcode))

                # audio from file_stream just after video
                track_order += ",%i:%i" % (in_file_number, audio.ix)

        if self.aspect_ratio:
            merge_args.append("--aspect-ratio")
            merge_args.append("0:%s" % (self.aspect_ratio))

        file_stream = self.gen_dumpstream_filename(title_idx)
        merge_args.append(file_stream)

        for sub_idx, langcode in self._get_title_subs_params(title_idx):
            langcode = self._normalize_langcode("vobp", title_idx, sub_idx, langcode)

            file_vobsub, file_vobsub_idx, file_vobsub_sub = self.gen_vobsub_filenames(
                title_idx, sub_idx, langcode
            )

            in_file_number += 1  # each subtitle track in separate file

            merge_args.append("--language")
            merge_args.append("0:%s" % (langcode))
            merge_args.append(file_vobsub_idx)

            # subtitle just after audio
            track_order += ",%i:0" % (in_file_number)

        if len(self.lsdvd.track[title_idx - 1].chapter) > 1:
            file_chapters = self.gen_chapters_filename(title_idx)
            merge_args.append("--chapters")
            merge_args.append(file_chapters)

        if self.split_chapters:
            merge_args.append("--split")
            merge_args.append("chapters:all")

        merge_args.append("--track-order")
        merge_args.append(track_order)

        return merge_args

    def dumpstream(self, title_idx: int) -> Path:
        outfile, dump_args = self.build_dumpstream_cmd(title_idx)

        print("dump stream")
        self._perform_dumpstream(outfile, dump_args)

        return outfile

    def build_dumpstream_cmd(self, title_idx: int) -> list:
        outfile = self.gen_dumpstream_filename(title_idx)

        dump_args = [
            "mplayer",
            "-dvd-device",
            self.device,
            "dvd://%i" % (title_idx),
            "-dumpstream",
            "-dumpfile",
            outfile,
        ]

        return outfile, dump_args

    def gen_dumpstream_filename(self, title_idx: int) -> list:
        return self.tmp_dir / ("%s_%i_video.vob" % (self.file_prefix, title_idx))

    def _perform_dumpstream(self, outfile: Path, dump_args: list) -> None:
        if not outfile.exists() or self.rewrite:
            self._subprocess_run(
                dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

    def dumpchapters(self, title_idx: int) -> Path:
        print("dump chapters")

        outfile = self.gen_chapters_filename(title_idx)

        chapters = self.gen_chapters(title_idx)

        if self.verbose:
            print(chapters)

        self._perform_dumpchapters(outfile, chapters)

        return outfile

    def gen_chapters_filename(self, title_idx: int) -> str:
        return self.tmp_dir / ("%s_%i_chapters.txt" % (self.file_prefix, title_idx))

    def gen_chapters(self, title_idx: int) -> str:
        start = 0.000
        chapters = ""

        for chapter in self.lsdvd.track[title_idx - 1].chapter:
            chapters += "CHAPTER%02d=%s\n" % (
                chapter.ix,
                convert_seconds_to_hhmmss(start),
            )
            chapters += "CHAPTER%02dNAME=\n" % (chapter.ix)

            start += chapter.length

        return chapters

    def _perform_dumpchapters(self, outfile: Path, chapters: str) -> Path:
        if not outfile.exists() or self.rewrite:
            self._save_to_file(outfile, chapters)

    def dumpvobsubs(self, title_idx: int):
        for vobsub in self.lsdvd.track[title_idx - 1].subp:
            if vobsub.langcode in self.langcodes:
                self.dumpvobsub(title_idx, vobsub.ix, vobsub.langcode)

    def dumpvobsub(self, title_idx: int, sub_ix: int, langcode: str):
        print("extracting subtitle %i lang %s" % (sub_ix, langcode))

        outfile, outfile_idx, outfile_sub = self.gen_vobsub_filenames(
            title_idx, sub_ix, langcode
        )

        dump_args = self.gen_dumpvobsub_cmd(outfile, title_idx, sub_ix)

        self._perform_dumpvobsub(dump_args, outfile_idx, outfile_sub, langcode)

        return outfile_idx, outfile_sub

    def gen_vobsub_filenames(self, title_idx: int, sub_ix: int, langcode: str) -> tuple:
        outfile = self.tmp_dir / (
            "%s_%i_vobsub_%i_%s" % (self.file_prefix, title_idx, sub_ix, langcode)
        )

        outfile_idx = outfile.with_suffix(".idx")
        outfile_sub = outfile.with_suffix(".sub")

        return outfile, outfile_idx, outfile_sub

    def gen_dumpvobsub_cmd(self, outfile: int, title_idx: int, sub_ix: int) -> list:
        return [
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

    def _perform_dumpvobsub(
        self,
        dump_args: list,
        outfile_idx: Path,
        outfile_sub: Path,
        langcode: str,
    ) -> None:
        if outfile_idx.exists() or outfile_sub.exists():
            if self.rewrite:
                self._clear_file(outfile_idx)
                self._clear_file(outfile_sub)
            else:
                return

        self._subprocess_run(
            dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        self._fix_vobsub_file_content(outfile_idx, langcode)

    def _fix_vobsub_file_content(self, idx_file: Path, langcode: str):
        if self.dry_run:
            return

        f = idx_file.open(mode="r")
        content = f.read()
        f.close()
        content_new = self._fix_vobsub_lang_id(content, langcode)

        if content != content_new:
            f = idx_file.open(mode="w")
            f.write(content_new)
            f.close()

    def _fix_vobsub_lang_id(self, content: str, langcode: str) -> str:
        return re.sub("id: , index", f"id: {langcode}, index", content, flags=re.M)

    def list_languages(self) -> None:
        self._subprocess_run(["mkvmerge", "--list-languages"])

    def _subprocess_run(self, cmd: list, **kwargs) -> None:
        if self.dry_run or self.verbose:
            print(subprocess.list2cmdline(cmd))

        if not self.dry_run:
            subprocess.run(cmd, **kwargs)

    def _save_to_file(self, outfile: Path, data: str) -> None:
        if self.dry_run:
            return

        with outfile.open(mode="w") as f:
            print(data, file=f)

    def _clear_file(self, file: Path) -> None:
        if self.dry_run:
            return

        file.open(mode="w").close()

    def _unlink_empty_file(self, file: Path) -> None:
        if self.dry_run:
            return

        try:
            if file.stat().st_size == 0:
                file.unlink()
        except:
            print("Oops! %s" % file)

    def _rm_temp_files(self) -> None:
        if self.dry_run:
            pprint(self.temp_files)
        else:
            while self.temp_files:
                try:
                    self.temp_files.pop().unlink()
                except:
                    print("Oops!")

    def _get_title_subs_params(self, title_idx: int) -> list:
        subs_params = []

        if self.subs_params:
            subs_params = self.subs_params
        else:
            for vobsub in self.lsdvd.track[title_idx - 1].subp:
                if vobsub.langcode in self.langcodes:
                    subs_params.append([vobsub.ix, vobsub.langcode])

        return subs_params

    def _normalize_langcode(
        self, type: str, title_idx: int, idx: int, langcode: str
    ) -> str:
        if langcode == "undefined":
            langcode = getattr(self.lsdvd.track[title_idx - 1], type)[idx - 1].langcode

        if langcode in wrong_lang_codes:
            langcode = "und"

        return langcode


def convert_seconds_to_hhmmss(seconds: float) -> str:
    return (datetime.utcfromtimestamp(0) + timedelta(seconds=seconds)).strftime(
        "%H:%M:%S.%f"
    )[:-3]
