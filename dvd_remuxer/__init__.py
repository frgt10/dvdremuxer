import sys
import argparse
import os.path
import textwrap
from pprint import pprint
from .DVDRemuxer import DVDRemuxer


def is_valid_file(parser, path):
    if not os.path.exists(path):
        parser.error("The path %s does not exist!" % path)
    else:
        return path

def parse_args():
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

    argparser.add_argument('--add-sub-langcode', dest='add_sub_langcode', metavar='LANGCODE',
                        help='Keep additional subtitles for language')

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

    return argparser.parse_args()

def _real_main(argv=None):
    args = parse_args()

    print('Run with arguments:')
    pprint(vars(args))

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

    if args.add_sub_langcode:
        remuxer.langcodes.append(args.add_sub_langcode)

    for idx in titles_idx:
        remuxer.remux_title(idx)

def main(argv=None):
    try:
        _real_main(argv)
    except KeyboardInterrupt:
        sys.exit('\nERROR: Interrupted by user')
