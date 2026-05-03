import argparse


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments with subcommand structure.

    Usage:
        video_cut analyze -t <timeline.otio>
        video_cut analyze -t <timeline.otio> -v <source.mkv>
        video_cut analyze -t <timeline.otio> --no-color
    """
    parser = argparse.ArgumentParser(
        prog="video_cut",
        description="Video cut CLI tool for OTIO timeline analysis",
    )
    parser.add_argument(
        "--version", action="version", version="video_cut 0.1.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze OTIO timeline and print merged source segments",
    )
    analyze_parser.add_argument(
        "-t", "--timeline",
        required=True,
        metavar="FILE",
        help="OpenTimelineIO (.otio) file to analyze",
    )
    analyze_parser.add_argument(
        "-v", "--video",
        metavar="FILE",
        help="Source video file (MKV/HEVC/HDR10) — used for validation only",
    )
    analyze_parser.add_argument(
        "-k", "--track",
        type=int,
        default=0,
        help="Video track index to analyze (default: 0)",
    )
    analyze_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        parser.exit()

    return args
