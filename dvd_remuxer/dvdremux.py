#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import datetime, timedelta
from pprint import pprint
import re

from .lsdvd import lsdvd

wrong_lang_codes = ["", None]


class DVDRemuxer:
    def __init__(self, device: str, **options):
        self.device = device
        self.lsdvd = options.get("lsdvd")
        self.dry_run = options.get("dry_run")
        self.keep_temp_files = options.get("keep_temp_files")
        self.rewrite = options.get("rewrite")
        self.aspect_ratio = options.get("aspect_ratio")
        self.split_chapters = options.get("split_chapters")
        self.verbose = options.get("verbose")
        self.tmp_dir_obj = None
        self.file_prefix = options.get("file_prefix")
        self.tmp_dir = Path.cwd()
        self.use_sys_tmp_dir = options.get("use_sys_tmp_dir")

        self.temp_files = []
        self.langcodes = ["ru", "en"]

        if not self.lsdvd:
            raise Exception("Path is not valid video DVD")

    def remux_to_mkv(
        self, title_idx: int, audio_params: list, subs_params: list, outdir: Path
    ) -> None:
        print(
            "remuxing title #%i (%s)"
            % (
                title_idx,
                convert_seconds_to_hhmmss(self.lsdvd.track[title_idx - 1].length),
            )
        )

        pprint(self.use_sys_tmp_dir)

        if self.use_sys_tmp_dir:
            self.tmp_dir_obj = TemporaryDirectory(prefix="dvdremux_")
            self.tmp_dir = Path(self.tmp_dir_obj.name)

        if self.verbose:
            print("Temp directory: %s" % (self.tmp_dir))

        outfile = outdir / Path("%s_%i.DVDRemux.mkv" % (self.file_prefix, title_idx))

        mkvmerge_cmd = self.gen_mkvmerge_cmd(
            title_idx, audio_params, subs_params, outdir
        )

        file_stream = self.dumpstream(title_idx, self.tmp_dir)
        self.temp_files.append(file_stream)

        for sub_idx, langcode in subs_params:
            file_vobsub_idx, file_vobsub_sub = self.dumpvobsub(
                title_idx, sub_idx, langcode, self.tmp_dir
            )

            self.temp_files.append(file_vobsub_idx)
            self.temp_files.append(file_vobsub_sub)

        file_chapters = self.dumpchapters(title_idx, self.tmp_dir)
        self.temp_files.append(file_chapters)

        print("merge tracks")
        self._subprocess_run(mkvmerge_cmd)

        # Unlink а zero size file, when error occurred during the merge.
        self._unlink_empty_file(outfile)

        if not self.keep_temp_files and not self.tmp_dir_obj:
            print("remove temp files")
            self._rm_temp_files()

        return outfile

    def gen_mkvmerge_cmd(
        self, title_idx: int, audio_params: list, subs_params: list, outdir: Path
    ) -> list():
        outfile = outdir / Path("%s_%i.DVDRemux.mkv" % (self.file_prefix, title_idx))

        merge_args = ["mkvmerge", "--output", outfile]

        in_file_number = 0  # audio and video in first file

        # video from file_stream is first track
        track_order = "%i:0" % (in_file_number)

        audio_tracks = []

        for audio_idx, langcode in audio_params:
            audio_tracks.append(str(audio_idx))

            merge_args.append("--language")
            merge_args.append("%i:%s" % (audio_idx, langcode))

            # audio from file_stream just after video
            track_order += ",%i:%i" % (in_file_number, audio_idx)

        # set the necessary audio tracks
        merge_args.append("--audio-tracks")
        merge_args.append(str.join(",", audio_tracks))

        if self.aspect_ratio:
            merge_args.append("--aspect-ratio")
            merge_args.append("0:%s" % (self.aspect_ratio))

        file_stream = self.gen_dumpstream_filename(title_idx, self.tmp_dir)
        merge_args.append(file_stream)

        for sub_idx, langcode in subs_params:
            file_vobsub, file_vobsub_idx, file_vobsub_sub = self.gen_vobsub_filenames(
                title_idx, sub_idx, langcode, self.tmp_dir
            )

            in_file_number += 1  # each subtitle track in separate file

            merge_args.append("--language")
            merge_args.append("0:%s" % (langcode))
            merge_args.append(file_vobsub_idx)

            # subtitle just after audio
            track_order += ",%i:0" % (in_file_number)

        if len(self.lsdvd.track[title_idx - 1].chapter) > 1:
            file_chapters = self.gen_chapters_filename(title_idx, self.tmp_dir)
            merge_args.append("--chapters")
            merge_args.append(file_chapters)

        if self.split_chapters:
            merge_args.append("--split")
            merge_args.append("chapters:all")

        merge_args.append("--track-order")
        merge_args.append(track_order)

        return merge_args

    def dumpstream(self, title_idx: int, outdir: Path) -> Path:
        outfile, dump_args = self.build_dumpstream_cmd(title_idx, outdir)

        print("dump stream")
        self._perform_dumpstream(outfile, dump_args)

        return outfile

    def build_dumpstream_cmd(self, title_idx: int, outdir: Path) -> list:
        outfile = self.gen_dumpstream_filename(title_idx, outdir)

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

    def gen_dumpstream_filename(self, title_idx: int, outdir: Path) -> list:
        return outdir / ("%s_%i_video.vob" % (self.file_prefix, title_idx))

    def _perform_dumpstream(self, outfile: Path, dump_args: list) -> None:
        if not outfile.exists() or self.rewrite:
            self._subprocess_run(
                dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

    def dumpchapters(self, title_idx: int, outdir: Path) -> Path:
        print("dump chapters")

        outfile = self.gen_chapters_filename(title_idx, outdir)

        chapters = self.gen_chapters(title_idx)

        if self.verbose:
            print(chapters)

        self._perform_dumpchapters(outfile, chapters)

        return outfile

    def gen_chapters_filename(self, title_idx: int, outdir: Path) -> str:
        return outdir / ("%s_%i_chapters.txt" % (self.file_prefix, title_idx))

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

    def dumpvobsubs(self, title_idx: int, outdir: Path) -> dict:
        output_files = {}
        for vobsub in self.lsdvd.track[title_idx - 1].subp:
            if vobsub.langcode in self.langcodes:
                output_files[vobsub.langcode] = self.dumpvobsub(
                    title_idx, vobsub.ix, vobsub.langcode, outdir
                )

        return output_files

    def dumpvobsub(
        self, title_idx: int, sub_ix: int, langcode: str, outdir: Path
    ) -> tuple(Path, Path):
        print("extracting subtitle %i lang %s" % (sub_ix, langcode))

        outfile, outfile_idx, outfile_sub = self.gen_vobsub_filenames(
            title_idx, sub_ix, langcode, outdir
        )

        dump_args = self.gen_dumpvobsub_cmd(outfile, title_idx, sub_ix)

        self._perform_dumpvobsub(dump_args, outfile_idx, outfile_sub, langcode)

        return outfile_idx, outfile_sub

    def gen_vobsub_filenames(
        self, title_idx: int, sub_ix: int, langcode: str, outdir: Path
    ) -> tuple:
        outfile = outdir / (
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

    def _subprocess_run(self, cmd: list, **kwargs) -> None:
        if self.dry_run or self.verbose:
            print(subprocess.list2cmdline(cmd))

        if not self.dry_run:
            subprocess.run(cmd, **kwargs)

    def _save_to_file(self, outfile: Path, data: str) -> None:
        if self.dry_run:
            print(outfile.as_posix())
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


def convert_seconds_to_hhmmss(seconds: float) -> str:
    return (datetime.utcfromtimestamp(0) + timedelta(seconds=seconds)).strftime(
        "%H:%M:%S.%f"
    )[:-3]


class RemuxService:
    def __init__(self, dvd_info_reader_cls: lsdvd, remuxer_cls: DVDRemuxer, args):
        self.args = args
        self.dvd_info_reader_cls = dvd_info_reader_cls
        self.remuxer_cls = remuxer_cls
        self.lsdvd = self.dvd_info_reader_cls.read(self.args.dvd)
        self.langcodes = []
        self.outdir = Path.cwd()

    def run(self):
        if self.args.verbose:
            print("Run with arguments:")
            pprint(vars(self.args))

        if self.args.list_languages:
            self.list_languages()
            sys.exit(0)

        if self.args.info:
            self.dvd_info()
            sys.exit(0)

        if self.args.verbose:
            self.dvd_info()

        remuxer = self.remuxer_cls(
            self.args.dvd,
            lsdvd=self.lsdvd,
            dry_run=self.args.dry_run,
            keep_temp_files=self.args.keep,
            rewrite=self.args.rewrite,
            use_sys_tmp_dir=self.args.use_sys_tmp_dir,
            aspect_ratio=self.args.aspect_ratio,
            subs_params=self.args.subs_params,
            split_chapters=self.args.split_chapters,
            verbose=self.args.verbose,
            file_prefix=self._get_file_prefix(),
        )

        if self.args.add_sub_langcode:
            remuxer.langcodes = +self.args.add_sub_langcode

        self.langcodes = remuxer.langcodes

        pprint(remuxer.langcodes)

        titles_idx = self._get_titles()

        if self.args.action == "remux_to_mkv":
            for idx in titles_idx:
                remuxer.remux_to_mkv(
                    idx,
                    self.get_audio_params(idx),
                    self.get_subs_params(idx),
                    self.outdir,
                )
        elif self.args.action == "stream":
            for idx in titles_idx:
                remuxer.dumpstream(idx, self.outdir)
        elif self.args.action == "subs":
            for idx in titles_idx:
                remuxer.dumpvobsubs(idx, self.outdir)
        elif self.args.action == "chapters":
            for idx in titles_idx:
                remuxer.dumpchapters(idx, self.outdir)

    def list_languages(self) -> None:
        subprocess.run(["mkvmerge", "--list-languages"])

    def dvd_info(self) -> None:
        self.dvd_info_reader_cls.get_printable_dvd_info(self.args.dvd)

    def _get_titles(self):
        titles_idx = []

        if self.args.title_idx:
            titles_idx = self.args.title_idx
        elif self.args.all_titles:
            print("Remuxing all titles")
            titles_idx = self.lsdvd.all_titles_idx()
        else:
            print(
                "No titles specified. Use longest title #%i."
                % (self.lsdvd.longest_title_idx())
            )
            titles_idx.append(self.lsdvd.longest_title_idx())

        return titles_idx

    def _get_file_prefix(self):
        if self.lsdvd.title and self.lsdvd.title != "unknown":
            return self.lsdvd.title

        return "dvd"

    def get_audio_params(self, title_idx: int) -> list:
        audio_params = []

        # audio params from command line argumets
        if self.args.audio_params:
            audio_params = self.args.audio_params

        # or all audio from DVD title
        else:
            for audio in self.lsdvd.track[title_idx - 1].audio:
                audio_params.append([audio.ix, audio.langcode])

        for i in range(len(audio_params)):
            audio_idx, langcode = audio_params[i]
            audio_params[i][1] = self._normalize_langcode(
                "audio", title_idx, audio_idx, langcode
            )

        return audio_params

    def get_subs_params(self, title_idx: int) -> list:
        subs_params = []

        if self.args.subs_params:
            subs_params = self.args.subs_params
        else:
            for vobsub in self.lsdvd.track[title_idx - 1].subp:
                if vobsub.langcode in self.langcodes:
                    subs_params.append([vobsub.ix, vobsub.langcode])

        for i in range(len(subs_params)):
            vobp_idx, langcode = subs_params[i]
            subs_params[i][1] = self._normalize_langcode(
                "subp", title_idx, vobp_idx, langcode
            )

        return subs_params

    def _normalize_langcode(
        self, type: str, title_idx: int, idx: int, langcode: str
    ) -> str:
        if langcode == "undefined":
            langcode = getattr(self.lsdvd.track[title_idx - 1], type)[idx - 1].langcode

        if langcode == "xx":
            langcode = "mul"  # Multiple languages
        elif langcode in wrong_lang_codes:
            langcode = "und"

        return langcode
