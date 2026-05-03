import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class FfmpegProgress:
    """Parsed FFmpeg progress information."""
    frame: int = 0
    fps: float = 0.0
    speed: float = 0.0
    elapsed_seconds: float = 0.0
    bitrate_kbps: float = 0.0
    total_size_bytes: int = 0


PROGRESS_LINES = 6
PROGRESS_BAR_WIDTH = 60


def clear_lines(n: int) -> None:
    """Clear N lines above cursor using ANSI escape codes."""
    for _ in range(n):
        sys.stdout.write("\033[1A\033[2K")
    sys.stdout.flush()


def format_seconds(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    if seconds < 0:
        seconds = 0
    total_sec = int(round(seconds))
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_eta(fps: float, current_frame: int, total_frames: int) -> float:
    """Calculate ETA in seconds based on current FPS and remaining frames."""
    if fps <= 0 or total_frames <= 0 or current_frame >= total_frames:
        return 0.0
    remaining_frames = total_frames - current_frame
    return remaining_frames / fps


def create_progress_bar(percent: float, width: int = PROGRESS_BAR_WIDTH) -> str:
    """Create a progress bar string with percentage.

    Args:
        percent: 0.0 to 100.0
        width: Total width in characters

    Returns:
        String like "████████░░░░░░░░░░░░░░░░░░ 40.0%"
    """
    percent = max(0.0, min(100.0, percent))
    filled = int(percent * width / 100)
    empty = width - filled

    bar = "█" * filled + "░" * empty
    return f"{bar}  {percent:5.1f}%"


def render_progress(
    progress: FfmpegProgress,
    segment_idx: int,
    total_segments: int,
    segment_start_sec: float,
    segment_end_sec: float,
    total_frames: int,
    start_time: float,
    first_render: bool = False,
) -> None:
    """Render FFmpeg progress bar to stdout.

    Args:
        progress: Current FFmpeg progress
        segment_idx: Current segment number (1-based)
        total_segments: Total number of segments
        segment_start_sec: Segment start time in seconds
        segment_end_sec: Segment end time in seconds
        total_frames: Total frames for this segment
        start_time: Time.time() when encoding started
        first_render: If True, print header; otherwise clear and overwrite
    """
    if total_frames <= 0:
        return

    percent = (progress.frame / total_frames) * 100 if total_frames > 0 else 0
    eta_sec = calculate_eta(progress.fps, progress.frame, total_frames)
    elapsed_sec = time.time() - start_time
    finish_time = datetime.now() + timedelta(seconds=eta_sec)

    if not first_render:
        clear_lines(PROGRESS_LINES)

    segment_start = format_seconds(segment_start_sec)
    segment_end = format_seconds(segment_end_sec)

    lines = [
        f"-- Segment {segment_idx}/{total_segments} ({segment_start} --> {segment_end}) " + "-" * 40,
        f"Frame    : {progress.frame:6d} / {total_frames:<6d} | FPS: {progress.fps:6.1f} | Speed: {progress.speed:5.2f}x",
        f"ETA      : {format_seconds(eta_sec)} ~> Done at {finish_time.strftime('%H:%M')}",
        f"Elapsed  : {format_seconds(elapsed_sec)}",
        create_progress_bar(percent),
        "-" * 80,
    ]

    for line in lines:
        print(line)
    sys.stdout.flush()
