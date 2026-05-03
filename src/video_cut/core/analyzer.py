from pathlib import Path

import opentimelineio as otio

from video_cut.typedefs.otio_typing import RawClip, SourceSegment

CONTIGUITY_TOLERANCE_FRAMES = 1


def load_clips_from_otio(otio_path: Path, track_index: int = 0) -> list[RawClip]:
    """Parse OTIO file and return all clips from the specified video track.

    Uses opentimelineio to load the Timeline, then iterates over
    the specified track to extract RawClip objects.

    Raises:
        ValueError: if no video track is found or the file is malformed
    """
    timeline = otio.adapters.read_from_file(str(otio_path))

    if track_index >= len(timeline.tracks):
        raise ValueError(
            f"Track index {track_index} out of range (only {len(timeline.tracks)} tracks)"
        )

    video_track = timeline.tracks[track_index]
    if video_track.kind != otio.schema.TrackKind.Video:
        raise ValueError(f"Track {track_index} is not a Video track (kind={video_track.kind})")

    clips: list[RawClip] = []
    for item in video_track:
        if not isinstance(item, otio.schema.Clip):
            continue
        if item.source_range is None:
            raise ValueError(f"Clip '{item.name}' has no source_range")

        sr = item.source_range
        clips.append(
            RawClip(
                name=item.name,
                start_frame=sr.start_time.value,
                duration_frames=sr.duration.value,
                rate=sr.start_time.rate,
            )
        )

    if not clips:
        raise ValueError(f"No clips found in video track {track_index}")

    return clips


def merge_clips(clips: list[RawClip]) -> list[SourceSegment]:
    """Merge consecutive contiguous clips into SourceSegments.

    Two clips are contiguous if:
        abs(clip[i].end_frame - clip[i+1].start_frame) <= CONTIGUITY_TOLERANCE_FRAMES
    """
    if not clips:
        return []

    segments: list[SourceSegment] = []
    seg_start = clips[0].start_frame
    seg_end = clips[0].end_frame
    rate = clips[0].rate
    clip_count = 1

    for clip in clips[1:]:
        if abs(clip.start_frame - seg_end) <= CONTIGUITY_TOLERANCE_FRAMES:
            seg_end = clip.end_frame
            clip_count += 1
        else:
            segments.append(
                SourceSegment(
                    index=len(segments) + 1,
                    start_frame=seg_start,
                    end_frame=seg_end,
                    rate=rate,
                    clip_count=clip_count,
                )
            )
            seg_start = clip.start_frame
            seg_end = clip.end_frame
            clip_count = 1

    segments.append(
        SourceSegment(
            index=len(segments) + 1,
            start_frame=seg_start,
            end_frame=seg_end,
            rate=rate,
            clip_count=clip_count,
        )
    )

    return segments
