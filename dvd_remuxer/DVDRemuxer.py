#!/usr/bin/env python3

import subprocess
import os.path
from datetime import datetime, timedelta
from pprint import pprint

class DVDRemuxer:

    def __init__(self, device: str, dry_run: bool, keep: bool, rewrite: bool):
        self.device = device
        self.dry_run = dry_run
        self.keep_temp_files = keep
        self.rewrite = rewrite

        code_locals = {}

        data = subprocess.Popen(["lsdvd", "-x", "-Oy", self.device], stdout=subprocess.PIPE)
        exec(data.communicate()[0], {}, code_locals)

        self.lsdvd = code_locals.get('lsdvd')

        self.temp_files = []
        self.file_prefix = self.lsdvd['title'] if self.lsdvd['title'] and self.lsdvd['title'] != 'unknown' else 'dvd'
        self.langcodes = ['ru','en']

    def print_dvd_info(self) -> None:
        print('Longest title: %i' % (self.longest_title_idx()))

        for track in self.lsdvd.get("track"):
            if track.get('length') < 1:
                continue

            print()

            print('Index:', track.get('ix'))

            print('Length:', self.convert_seconds_to_hhmmss(track.get('length')) )

            print('Video:', track.get('format'), track.get('width'), 'x', track.get('height'), track.get('aspect'), track.get('df'), track.get('fps') )

            print('Audio:' )
            pprint( track.get('audio') )

            if len( track['subp'] ) > 0:
                print('Subtitles:' )
                pprint( track.get('subp') )

            if len( track['chapter'] ) > 1:
                print('Chapters:', len( track['chapter'] ) )

    def dumpvobsub(self, title_idx: int, sub_ix: int, langcode: str) -> None:
        print('extracting subtitle %i lang %s' % (sub_ix, langcode))

        outfile = '%s_%i_vobsub_%i' % (self.file_prefix, title_idx, sub_ix)

        self.temp_files.append(outfile + '.idx')
        self.temp_files.append(outfile + '.sub')

        if not ( os.path.exists(outfile + '.idx') and os.path.exists(outfile + '.sub') ) or self.rewrite:
            # mencoder dvd://1 -dvd-device /dev/dvd -ovc copy -oac copy -vobsubout "videoname2" -vobsuboutindex 2 -sid 1 -nosound -o /dev/null -vf harddup
            dump_args = [
                'mencoder',
                '-dvd-device', self.device,
                'dvd://%i' % (title_idx),
                '-vobsubout', outfile,
                '-vobsuboutindex', '%i' % (sub_ix),
                '-sid', '%i' % (sub_ix - 1),
                '-ovc', 'copy',
                '-oac', 'copy',
                '-nosound',
                '-o', '/dev/null',
                '-vf', 'harddup',
            ]

            if self.dry_run:
                pprint(dump_args)
            else:
                open(outfile + '.idx', 'w').close()
                open(outfile + '.sub', 'w').close()
                subprocess.run(dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def dumpstream(self, title_idx: int) -> None:
        print('dump stream')

        outfile = '%s_%i_video.vob' % (self.file_prefix, title_idx)
        self.temp_files.append(outfile)

        if not os.path.exists(outfile) or self.rewrite:
            dump_args = [
                'mplayer',
                '-dvd-device', self.device,
                'dvd://%i' % (title_idx),
                '-dumpstream',
                '-dumpfile', outfile
            ]

            # mplayer -dvd-device "${DVD_DEVICE}" dvd://${t} -dumpstream -dumpfile "${DIR_DIST}${DIST_FILE_PREFIX}${t}.vob"
            if self.dry_run:
                pprint(dump_args)
            else:
                subprocess.run(dump_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def dumpchapters(self, title_idx: int) -> None:
        print('dump chapters')

        outfile = '%s_%i_chapters.txt' % (self.file_prefix, title_idx)

        self.temp_files.append(outfile)

        if not os.path.exists(outfile) or self.rewrite:
            start = 0.000
            chapters = ''

            for chapter in self.lsdvd['track'][title_idx-1].get('chapter'):
                chapters += "CHAPTER%02d=%s\n" % (chapter['ix'], self.convert_seconds_to_hhmmss( start ))
                chapters += "CHAPTER%02dNAME=\n" % (chapter['ix'])

                start += chapter['length']

            if not self.dry_run:
                with open(outfile, 'w') as f:
                    print(chapters, file=f)

    def convert_seconds_to_hhmmss(self, seconds: float) -> str:
        return (datetime.utcfromtimestamp(0) + timedelta(seconds=seconds)).strftime('%H:%M:%S.%f')[:-3]

    def remux_title(self, title_idx: int) -> None:
        print('remuxing title #%i' % (title_idx))

        self.dumpstream(title_idx)

        outfile='%s_%i.DVDRemux.mkv' % (self.file_prefix, title_idx)

        merge_args = ['mkvmerge', '--output', outfile]

        for audio in self.lsdvd['track'][title_idx-1].get('audio'):
            merge_args.append('--language')
            merge_args.append('%i:%s' % (audio['ix'], audio['langcode']))

        merge_args.append('%s_%i_video.vob' % (self.file_prefix, title_idx))

        for vobsub in self.lsdvd['track'][title_idx-1].get('subp'):
            if vobsub['langcode'] in self.langcodes:
                self.dumpvobsub(title_idx, vobsub['ix'], vobsub['langcode'])
                merge_args.append('--language')
                merge_args.append('0:%s' % (vobsub['langcode']))
                merge_args.append('%s_%i_vobsub_%i.idx' % (self.file_prefix, title_idx, vobsub['ix']))

        self.dumpchapters(title_idx)

        chapters_file = '%s_%i_chapters.txt' % (self.file_prefix, title_idx)

        merge_args.append('--chapters')
        merge_args.append(chapters_file)

        print('merge tracks')

        if self.dry_run:
            pprint(merge_args)
        else:
            open(outfile, 'w').close()
            subprocess.run(merge_args, stdout=subprocess.DEVNULL)

        if not self.keep_temp_files:
            self.__rm_temp_files()

    def __rm_temp_files(self) -> None:
        print('remove temp files')

        if self.dry_run:
            pprint(self.temp_files)
        else:
            for file in self.temp_files:
                os.remove(file)

    def longest_title_idx(self) -> int:
        return self.lsdvd['longest_track']

    def all_titles_idx(self):
        titles = []
        for track in self.lsdvd.get("track"):
            if track.get('length') < 1:
                continue

            titles.append(track.get('ix'))

        return titles
