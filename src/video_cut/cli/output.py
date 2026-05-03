import sys

from video_cut.typedefs.otio_typing import SourceSegment


def format_timecode(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    whole_secs = int(secs)
    millis = round((secs - whole_secs) * 1000)

    if millis >= 1000:
        whole_secs += 1
        millis -= 1000
        if whole_secs >= 60:
            minutes += 1
            whole_secs -= 60
            if minutes >= 60:
                hours += 1
                minutes -= 60

    return f"{hours:02d}:{minutes:02d}:{whole_secs:02d}.{millis:03d}"


def format_duration(seconds: float) -> str:
    """Format duration as 'Xm Ys' (e.g. '2m 38s')"""
    total_sec = int(round(seconds))
    minutes = total_sec // 60
    secs = total_sec % 60
    return f"{minutes}m {secs:2d}s"


def print_segment(segment: SourceSegment, use_color: bool) -> None:
    """Print one segment line to stdout."""
    start_tc = format_timecode(segment.start_seconds)
    end_tc = format_timecode(segment.end_seconds)
    dur = format_duration(segment.duration_seconds)
    print(f"Segment {segment.index:2d}: {start_tc} --> {end_tc}  (duration: {dur})")


def print_summary(
    segments: list[SourceSegment],
    total_clips: int,
    use_color: bool,
) -> None:
    """Print summary block to stdout."""
    merged_cuts = total_clips - len(segments)
    total_duration_sec = sum(seg.duration_seconds for seg in segments)
    total_tc = format_timecode(total_duration_sec)

    print()
    print(
        f"Summary: {len(segments)} segments | {merged_cuts} merged unnecessary cuts"
        f" | Total duration: {total_tc}"
    )


def print_warn(msg: str) -> None:
    print(f"⚠ {msg}", file=sys.stderr, flush=True)


def print_err(msg: str) -> None:
    print(f"✗ {msg}", file=sys.stderr, flush=True)
