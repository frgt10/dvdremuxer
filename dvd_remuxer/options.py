import argparse
from pathlib import Path
import textwrap


def is_valid_path(parser, path):
    if not Path(path).exists():
        parser.error("The path %s does not exist!" % path)
    else:
        return path


def get_int_list(parser, title_idx):
    return list(map(int, title_idx.split(",")))


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
            - mkvmerge"""
        ),
    )

    argparser.add_argument(
        "dvd",
        metavar="PATH",
        help="dir with VIDEO_TS or iso image",
        type=lambda path: is_valid_path(argparser, path),
    )

    argparser.add_argument(
        "--dvd-title",
        dest="title_idx",
        nargs="?",
        type=lambda title_idx: get_int_list(argparser, title_idx),
        help="title(s) that should be remuxed",
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
        "--use-sys-tmp-dir",
        dest="use_sys_tmp_dir",
        action="store_true",
        help="use system temp directory to store temp files",
    )

    argparser.add_argument(
        "--add-sub-langcode",
        dest="add_sub_langcode",
        metavar="LANGCODE",
        nargs="?",
        type=lambda langcodes: get_str_list(argparser, langcodes),
        help="keep additional subtitles for language",
    )

    argparser.add_argument(
        "--aspect-ratio",
        dest="aspect_ratio",
        nargs="?",
        help="Video aspect ratio: 16/9, 4/3",
    )

    argparser.add_argument(
        "--audio",
        dest="audio_params",
        metavar="AUDIO_ID[:LANGCODE][,AUDIO_ID[:LANGCODE]...]",
        nargs="?",
        type=lambda audio_str: get_complex_params(argparser, audio_str),
        help="Audio id with langcode (optional) in necessary order (e.g. 2:ru,1,3:en)."
        + " All languages including their ISO 639-2 codes can be listed with the --list-languages option.",
    )

    argparser.add_argument(
        "--subs",
        dest="subs_params",
        metavar="SUB_ID[:LANGCODE][,SUB_ID[:LANGCODE]...]",
        nargs="?",
        type=lambda audio_str: get_complex_params(argparser, audio_str),
        help="Subtitle id with langcode (optional) in necessary order (e.g. 2:ru,1,3:en)."
        + " All languages including their ISO 639-2 codes can be listed with the --list-languages option.",
    )

    argparser.add_argument(
        "--list-languages",
        action="store_true",
        help="lists all languages and their ISO 639-2 code",
    )

    argparser.add_argument("--info", action="store_true", help="show DVD info")

    argparser.add_argument("--keep", action="store_true", help="keep temp files")

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

    argparser.add_argument("--title", help="movie title")

    argparser.add_argument("--year", help="movie release year")

    argparser.add_argument("--director", help="movie director")

    return argparser


def parse_args():
    argparser = create_argparser()
    return argparser.parse_args()
