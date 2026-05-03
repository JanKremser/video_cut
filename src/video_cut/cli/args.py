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

    cut_parser = subparsers.add_parser(
        "cut",
        help="Cut video based on OTIO timeline (removes unnecessary cuts)",
    )
    cut_parser.add_argument(
        "-t", "--timeline",
        required=True,
        metavar="FILE",
        help="OpenTimelineIO (.otio) file to analyze",
    )
    cut_parser.add_argument(
        "-i", "--input",
        required=True,
        metavar="FILE",
        help="Source video file (MKV/HEVC/HDR10) to cut",
    )
    cut_parser.add_argument(
        "-o", "--output",
        required=True,
        metavar="FILE",
        help="Output video file after cutting",
    )
    cut_parser.add_argument(
        "-k", "--track",
        type=int,
        default=0,
        help="Video track index to analyze (default: 0)",
    )
    cut_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output",
    )
    cut_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show segments without running FFmpeg",
    )
    cut_parser.add_argument(
        "--reencode",
        action="store_true",
        help="Use libx265 re-encoding for frame-accurate cuts (slower but precise)",
    )
    cut_parser.add_argument(
        "--crf",
        type=int,
        default=18,
        help="CRF for re-encoding (default: 18, lower=higher quality)",
    )
    cut_parser.add_argument(
        "--preset",
        default="slow",
        help="x265 preset: ultrafast, faster, fast, medium, slow, slower (default: slow)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        parser.exit()

    return args
