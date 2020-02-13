import sys
from pprint import pprint
from .options import parse_args
from .dvdremux import DVDRemuxer


def _real_main():
    args = parse_args()

    print("Run with arguments:")
    pprint(vars(args))

    remuxer = DVDRemuxer(
        args.dvd,
        dry_run = args.dry_run,
        keep_temp_files = args.keep,
        rewrite = args.rewrite,
        use_sys_tmp_dir = args.use_sys_tmp_dir
    )

    remuxer.print_dvd_info()

    titles_idx = []

    if args.title_idx:
        titles_idx.append(args.title_idx)
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
        remuxer.langcodes.append(args.add_sub_langcode)

    for idx in titles_idx:
        remuxer.remux_to_mkv(idx)


def main():
    try:
        _real_main()
    except KeyboardInterrupt:
        sys.exit("\nERROR: Interrupted by user")
