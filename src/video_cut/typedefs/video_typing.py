from dataclasses import dataclass


@dataclass
class VideoInfo:
    """Structured video metadata from ffprobe."""
    filepath: str
    codec_name: str
    color_primaries: str | None
    color_transfer: str | None
    color_space: str | None
    duration_seconds: float
    total_frames: int | None
    width: int
    height: int
