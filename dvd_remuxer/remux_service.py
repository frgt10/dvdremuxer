#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path
from pprint import pprint

from .lsdvd import lsdvd
from .dvdremux import DVDRemuxer

wrong_lang_codes = ["", None]


class RemuxService:
    def __init__(self, dvd_info_reader_cls: lsdvd, remuxer_cls: DVDRemuxer, args):
        self.args = args
        self.dvd_info_reader_cls = dvd_info_reader_cls
        self.remuxer_cls = remuxer_cls
        self.langcodes = []
        self.outdir = Path.cwd()

        self.lsdvd = self.dvd_info_reader_cls.read(self.args.dvd)
        if not self.lsdvd:
            raise Exception("Path is not valid video DVD")

    def run(self) -> None:
        if self.args.verbose:
            print("Run with arguments:")
            pprint(vars(self.args))

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

    def dvd_info(self) -> None:
        self.dvd_info_reader_cls.get_printable_dvd_info(self.args.dvd)

    def _get_titles(self) -> list:
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

    def _get_file_prefix(self) -> str:
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
