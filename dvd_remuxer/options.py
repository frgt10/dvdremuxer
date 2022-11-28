import argparse
from pathlib import Path
import textwrap


def is_valid_path(parser, path):
    if not Path(path).exists():
        parser.error("The path %s does not exist!" % path)
    else:
        return path


def get_int_list(parser, title_idx):
    int_numbers = []
    for string in list(map(str, title_idx.split(","))):
        if "-" in string:
            range_start, range_stop = list(map(int, string.split("-")))
            int_numbers += list(range(range_start, range_stop + 1))
        else:
            int_numbers.append(int(string))
    return int_numbers


def get_str_list(parser, langcodes):
    return langcodes.split(",")


def get_complex_params(parser, params_str):
    params_list = []
    for item_str in params_str.split(","):
        params = item_str.split(":")
        params[0] = int(params[0])

        if len(params) == 1:
            params.append("undefined")

        params_list.append(params)

    return params_list


def create_argparser():
    argparser = argparse.ArgumentParser(
        description="DVD Remuxer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Utility programs:
            - lsdvd
            - mplayer
            - mencoder
            - mkvmerge"""
        ),
    )

    argparser.add_argument(
        "dvd",
        metavar="PATH",
        help="directory with VIDEO_TS or ISO image",
        type=lambda path: is_valid_path(argparser, path),
    )

    argparser.add_argument(
        "--dvd-title",
        dest="title_idx",
        nargs="?",
        type=lambda title_idx: get_int_list(argparser, title_idx),
        help="title(s) that should be remuxed. E.g.: '1', '1,2,3', '1-5', '1-3,5,7,10-12'",
    )

    argparser.add_argument(
        "--all", dest="all_titles", action="store_true", help="remux all titles"
    )

    argparser.add_argument(
        "--action",
        choices=["remux_to_mkv", "stream", "subs", "chapters"],
        default="remux_to_mkv",
        help="one of the actions (default: remux_to_mkv)",
    )

    argparser.add_argument(
        "--audio",
        dest="audio_params",
        metavar="AUDIO_ID[:LANGCODE][,AUDIO_ID[:LANGCODE]...]",
        nargs="?",
        type=lambda audio_str: get_complex_params(argparser, audio_str),
        help="audio id with langcode (optional) in necessary order (e.g. 2:ru,1,3:en)."
        + " All languages including their ISO 639-2 codes can be listed with the --list-languages option",
    )

    argparser.add_argument(
        "--subs",
        dest="subs_params",
        metavar="SUB_ID[:LANGCODE][,SUB_ID[:LANGCODE]...]",
        nargs="?",
        type=lambda audio_str: get_complex_params(argparser, audio_str),
        help="subtitle id with langcode (optional) in necessary order (e.g. 2:ru,1,3:en)."
        + " All languages including their ISO 639-2 codes can be listed with the --list-languages option",
    )

    argparser.add_argument(
        "--add-sub-langcode",
        dest="add_sub_langcode",
        metavar="LANGCODE",
        nargs="?",
        type=lambda langcodes: get_str_list(argparser, langcodes),
        help="keep additional subtitles for language. Default 'ru', 'en'",
    )

    argparser.add_argument(
        "--aspect-ratio",
        dest="aspect_ratio",
        nargs="?",
        help="video aspect ratio: 16/9, 4/3",
    )

    argparser.add_argument(
        "--list-languages",
        action="store_true",
        help="lists all languages and their ISO 639-2 code",
    )

    argparser.add_argument(
        "--split-chapters",
        dest="split_chapters",
        action="store_true",
        help="split video by chapters",
    )

    argparser.add_argument("--info", action="store_true", help="show DVD info")

    argparser.add_argument(
        "--use-sys-tmp-dir",
        dest="use_sys_tmp_dir",
        action="store_true",
        help="use system temp directory to store temp files",
    )

    argparser.add_argument(
        "--keep",
        action="store_true",
        help="keep temp files. Not work with --use-sys-tmp-dir",
    )

    argparser.add_argument("--rewrite", action="store_true", help="rewrite files")

    argparser.add_argument(
        "--verbose", action="store_true", help="print various debugging information"
    )

    argparser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="only print commands that should be executed",
    )

    return argparser


def parse_args():
    argparser = create_argparser()
    return argparser.parse_args()
