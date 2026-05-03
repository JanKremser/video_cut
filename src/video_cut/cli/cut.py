import sys
from pathlib import Path

from video_cut.cli.output import print_err, print_segment, print_summary, print_warn
from video_cut.core.analyzer import load_clips_from_otio, merge_clips
from video_cut.core.cutter import cut_video
from video_cut.core.validator import VideoValidator
from video_cut.tools.hdr_probe import extract_hdr_metadata
from video_cut.typedefs.otio_typing import RawClip, SourceSegment
from video_cut.typedefs.video_typing import EncodeOptions


def handle_cut(args) -> int:
    """Handle the 'cut' subcommand."""
    use_color: bool = not args.no_color

    otio_path = Path(args.timeline)
    if not otio_path.exists():
        print_err(f"OTIO file not found: {otio_path}")
        return 1

    input_path = Path(args.input)
    if not input_path.exists():
        print_err(f"Input video file not found: {input_path}")
        return 1

    output_path = Path(args.output)

    validator = VideoValidator()
    try:
        video_info = validator.validate(filepath=input_path)
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
        print_err(f"Error merging clips: {e}")
        return 1

    print("Segments to cut:")
    for segment in segments:
        print_segment(segment=segment, use_color=use_color)

    print_summary(segments=segments, total_clips=len(clips), use_color=use_color)

    if args.dry_run:
        if args.reencode:
            print("[Dry-run] Would cut with libx265 re-encoding (frame-accurate)")
        else:
            print("[Dry-run] Would cut with stream-copy (fast, keyframe-dependent)")
        return 0

    encode_opts = None
    if args.reencode:
        print("Extracting HDR10 metadata...")
        try:
            hdr_meta = extract_hdr_metadata(input_path)
            encode_opts = EncodeOptions(
                crf=args.crf,
                preset=args.preset,
                hdr=hdr_meta,
            )
            if hdr_meta.master_display:
                print(f"  ✓ Master Display found")
            if hdr_meta.max_cll:
                print(f"  ✓ MaxCLL found")
            if not hdr_meta.master_display and not hdr_meta.max_cll:
                print_warn("No HDR10 metadata found, but re-encoding will proceed")
        except RuntimeError as e:
            print_err(f"Error extracting HDR10 metadata: {e}")
            return 1

        mode = f"libx265 (CRF {args.crf}, Preset {args.preset})"
    else:
        mode = "stream-copy (fast, keyframe-dependent)"

    print(f"\nCutting with {mode}...")
    print(f"Output to: {output_path}")

    try:
        cut_video(
            input_path=input_path,
            output_path=output_path,
            segments=segments,
            video_fps=video_info.fps,
            encode_opts=encode_opts,
            audio_stream_count=video_info.audio_stream_count,
            scale=args.scale if hasattr(args, 'scale') else None,
        )
    except (RuntimeError, ValueError) as e:
        print_err(f"Error cutting video: {e}")
        return 1

    print(f"\n✓ Video cut successfully: {output_path}")
    return 0
