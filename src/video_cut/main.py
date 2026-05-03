import sys

from video_cut.cli.args import parse_args
from video_cut.cli.analyze import handle_analyze


def main() -> None:
    args = parse_args()

    if args.command == "analyze":
        exit_code = handle_analyze(args)
    else:
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
