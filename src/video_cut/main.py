import sys

from video_cut.cli.analyze import handle_analyze
from video_cut.cli.args import parse_args
from video_cut.cli.cut import handle_cut


def main() -> None:
    args = parse_args()

    if args.command == "analyze":
        exit_code = handle_analyze(args)
    elif args.command == "cut":
        exit_code = handle_cut(args)
    else:
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
