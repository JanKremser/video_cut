import sys
from pathlib import Path

from video_cut.cli.output import print_err, print_segment, print_summary
from video_cut.core.analyzer import load_clips_from_otio, merge_clips
from video_cut.core.validator import VideoValidator
from video_cut.typedefs.otio_typing import RawClip, SourceSegment


def handle_analyze(args) -> int:
    """Handle the 'analyze' subcommand."""
    use_color: bool = not args.no_color

    otio_path = Path(args.timeline)
    if not otio_path.exists():
        print_err(f"OTIO-Datei nicht gefunden: {otio_path}")
        return 1

    if args.video:
        video_path = Path(args.video)
        if not video_path.exists():
            print_err(f"Videodatei nicht gefunden: {video_path}")
            return 1
        validator = VideoValidator()
        try:
            validator.validate(filepath=video_path)
        except RuntimeError as e:
            print_err(str(e))
            return 1

    try:
        clips: list[RawClip] = load_clips_from_otio(
            otio_path=otio_path, track_index=args.track
        )
    except (ValueError, RuntimeError) as e:
        print_err(str(e))
        return 1

    try:
        segments: list[SourceSegment] = merge_clips(clips=clips)
    except Exception as e:
        print_err(f"Fehler beim Zusammenführen der Clips: {e}")
        return 1

    for segment in segments:
        print_segment(segment=segment, use_color=use_color)

    print_summary(segments=segments, total_clips=len(clips), use_color=use_color)

    return 0
