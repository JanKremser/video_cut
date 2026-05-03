import json
import os
import subprocess
from pathlib import Path

from video_cut.typedefs.video_typing import VideoInfo


def _clean_env() -> dict:
    """Remove LD_LIBRARY_PATH to avoid conflicts."""
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    return env


def probe_video_info(filepath: Path) -> VideoInfo:
    """Run ffprobe on filepath and return structured VideoInfo.

    Raises:
        RuntimeError: if ffprobe fails or the file has no video stream
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(filepath),
            ],
            capture_output=True,
            text=True,
            check=True,
            env=_clean_env(),
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe failed for {filepath}: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("ffprobe not found in PATH")

    data = json.loads(result.stdout)

    video_stream = None
    audio_stream_count = 0
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio":
            audio_stream_count += 1

    if video_stream is None:
        raise RuntimeError(f"No video stream found in {filepath}")

    duration_str = data.get("format", {}).get("duration")
    duration_seconds = float(duration_str) if duration_str else 0.0

    total_frames = None
    if "nb_frames" in video_stream:
        try:
            total_frames = int(video_stream["nb_frames"])
        except (ValueError, TypeError):
            pass

    fps = _parse_fps(video_stream.get("r_frame_rate", ""))

    return VideoInfo(
        filepath=str(filepath),
        codec_name=video_stream.get("codec_name", ""),
        color_primaries=video_stream.get("color_primaries"),
        color_transfer=video_stream.get("color_transfer"),
        color_space=video_stream.get("color_space"),
        duration_seconds=duration_seconds,
        total_frames=total_frames,
        width=video_stream.get("width", 0),
        height=video_stream.get("height", 0),
        fps=fps,
        audio_stream_count=max(audio_stream_count, 1),
    )


def _parse_fps(r_frame_rate: str) -> float:
    """Parse r_frame_rate string (e.g., '24000/1001' or '24') to float.

    Args:
        r_frame_rate: Frame rate string from ffprobe

    Returns:
        FPS as float, or 0.0 if parsing fails
    """
    if not r_frame_rate:
        return 0.0

    try:
        if "/" in r_frame_rate:
            num, den = r_frame_rate.split("/")
            return float(num) / float(den)
        else:
            return float(r_frame_rate)
    except (ValueError, ZeroDivisionError):
        return 0.0
