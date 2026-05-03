from dataclasses import dataclass


@dataclass
class RawClip:
    """Raw clip extracted from an OTIO track — frame-valued."""
    name: str
    start_frame: float
    duration_frames: float
    rate: float

    @property
    def end_frame(self) -> float:
        """Exclusive end frame (start + duration)."""
        return self.start_frame + self.duration_frames


@dataclass
class SourceSegment:
    """A merged segment of source material to retain."""
    index: int
    start_frame: float
    end_frame: float
    rate: float
    clip_count: int

    @property
    def duration_frames(self) -> float:
        return self.end_frame - self.start_frame

    @property
    def start_seconds(self) -> float:
        return self.start_frame / self.rate

    @property
    def end_seconds(self) -> float:
        return self.end_frame / self.rate

    @property
    def duration_seconds(self) -> float:
        return self.duration_frames / self.rate
