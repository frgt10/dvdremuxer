#!/usr/bin/env python3

import argparse
import subprocess
import os.path
from datetime import datetime, timedelta
import textwrap
from pprint import pprint


def is_valid_file(parser, path):
    if not os.path.exists(path):
        parser.error("The path %s does not exist!" % path)
    else:
        return path


argparser = argparse.ArgumentParser(
    description='DVD Remuxer',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=textwrap.dedent('''\
        Utility programs:
        - lsdvd
        - mplayer
        - mkvmerge'''))

argparser.add_argument('dvd', metavar='PATH',
                    help='dir with VIDEO_TS or iso image',
                    type=lambda path: is_valid_file(argparser, path))

argparser.add_argument('--dvd-title', dest='title_idx', type=int,
                    help='title that should be remuxed')

argparser.add_argument('--all', dest='all_titles', action='store_true',
                    help='remux all titles')

argparser.add_argument('--keep', action='store_true',
                    help='keep temp files')

argparser.add_argument('--rewrite', action='store_true',
                    help='rewrite files')

argparser.add_argument('--dry-run', dest='dry_run', action='store_true',
                    help='only print commands that should be executed')

argparser.add_argument('--title',
                    help='movie title')

argparser.add_argument('--year',
                    help='movie release year')

argparser.add_argument('--director',
                    help='movie director')

args = argparser.parse_args()

print('Run with arguments:')
pprint(vars(args))

data = subprocess.Popen(["lsdvd", "-x", "-Oy", args.dvd], stdout=subprocess.PIPE)
exec(data.communicate()[0])


class DVDRemuxer:

    def __init__(self, device: str, dry_run: bool, keep: bool, rewrite: bool):
        self.device = device
        self.lsdvd = lsdvd
        self.dry_run = dry_run
        self.keep_temp_files = keep
        self.rewrite = rewrite
        self.temp_files = []
        self.file_prefix = self.lsdvd['title'] if self.lsdvd['title'] else 'dvd'

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
            if vobsub['langcode'] in ['ru','en']:
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


remuxer = DVDRemuxer(args.dvd, args.dry_run, args.keep, args.rewrite)

remuxer.print_dvd_info()

titles_idx = []

if args.title_idx:
    titles_idx.append(args.title_idx)
elif args.all_titles:
    print('Remuxing all titles')
    titles_idx = remuxer.all_titles_idx()
else:
    print('No titles specified. Use longest title #%i.' % (remuxer.longest_title_idx()))
    titles_idx.append(remuxer.longest_title_idx())

for idx in titles_idx:
    remuxer.remux_title(idx)
