import sys
from pprint import pprint
from .options import parse_args
from .dvdremux import DVDRemuxer


def _real_main():
    args = parse_args()

    if args.verbose:
        print("Run with arguments:")
        pprint(vars(args))

    remuxer = DVDRemuxer(
        args.dvd,
        dry_run=args.dry_run,
        keep_temp_files=args.keep,
        rewrite=args.rewrite,
        use_sys_tmp_dir=args.use_sys_tmp_dir,
        aspect_ratio=args.aspect_ratio,
        audio_params=args.audio_params,
        verbose=args.verbose,
    )

    if args.list_languages:
        remuxer.list_languages()
        sys.exit(0)

    if args.info or args.verbose:
        remuxer.dvd_info()
        sys.exit(0)

    titles_idx = []

    if args.title_idx:
        titles_idx = args.title_idx
    elif args.all_titles:
        print("Remuxing all titles")
        titles_idx = remuxer.all_titles_idx()
    else:
        print(
            "No titles specified. Use longest title #%i."
            % (remuxer.longest_title_idx())
        )
        titles_idx.append(remuxer.longest_title_idx())

    if args.add_sub_langcode:
        remuxer.langcodes = +args.add_sub_langcode

    pprint(remuxer.langcodes)

    action = {
        "remux_to_mkv": "remux_to_mkv",
        "stream": "dumpstream",
        "subs": "dumpvobsubs",
        "chapters": "dumpchapters",
    }.get(args.action)

    for idx in titles_idx:
        getattr(remuxer, action)(idx)


def main():
    try:
        _real_main()
    except KeyboardInterrupt:
        sys.exit("\nERROR: Interrupted by user")
    except Exception as error:
        sys.exit("\nERROR: %s" % (error))
