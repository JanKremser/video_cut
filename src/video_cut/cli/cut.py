import sys
from pathlib import Path

from video_cut.cli.output import print_err, print_segment, print_summary, print_warn
from video_cut.core.analyzer import load_clips_from_otio, merge_clips
from video_cut.core.cutter import cut_video
from video_cut.core.validator import VideoValidator
from video_cut.typedefs.otio_typing import RawClip, SourceSegment


def handle_cut(args) -> int:
    """Handle the 'cut' subcommand."""
    use_color: bool = not args.no_color

    otio_path = Path(args.timeline)
    if not otio_path.exists():
        print_err(f"OTIO-Datei nicht gefunden: {otio_path}")
        return 1

    input_path = Path(args.input)
    if not input_path.exists():
        print_err(f"Eingabe-Videodatei nicht gefunden: {input_path}")
        return 1

    output_path = Path(args.output)

    validator = VideoValidator()
    try:
        validator.validate(filepath=input_path)
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

    print("Segmente zum Schneiden:")
    for segment in segments:
        print_segment(segment=segment, use_color=use_color)

    print_summary(segments=segments, total_clips=len(clips), use_color=use_color)

    if args.dry_run:
        print("\n[Dry-run] FFmpeg würde jetzt ausgeführt, aber --dry-run ist aktiviert.")
        return 0

    print(f"\nSchneiden beginnt... Ausgabe wird zu: {output_path}")

    try:
        def progress_cb(idx: int, total: int, segment: SourceSegment) -> None:
            print(f"  [{idx}/{total}] Schneide Segment {segment.index}...", flush=True)

        cut_video(
            input_path=input_path,
            output_path=output_path,
            segments=segments,
            progress_cb=progress_cb,
        )
    except (RuntimeError, ValueError) as e:
        print_err(f"Fehler beim Schneiden: {e}")
        return 1

    print(f"✓ Video erfolgreich geschnitten: {output_path}")
    return 0
