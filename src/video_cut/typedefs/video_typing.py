from dataclasses import dataclass, field


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
    fps: float = 0.0


@dataclass
class HdrMetadata:
    """HDR10 metadata from source file."""
    master_display: str | None = None
    max_cll: str | None = None


@dataclass
class EncodeOptions:
    """Options for re-encoding with libx265."""
    crf: int = 18
    preset: str = "slow"
    hdr: HdrMetadata | None = field(default_factory=HdrMetadata)
