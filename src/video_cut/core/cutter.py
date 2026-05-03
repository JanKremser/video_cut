import shutil
from pathlib import Path
from typing import Callable

from video_cut.tools.ffmpeg import concat_segments, cut_segment
from video_cut.typedefs.otio_typing import SourceSegment


def cut_video(
    input_path: Path,
    output_path: Path,
    segments: list[SourceSegment],
    progress_cb: Callable[[int, int, SourceSegment], None] | None = None,
) -> None:
    """Cut and merge video segments using FFmpeg with stream copy.

    Creates temporary segment files, concatenates them, and cleans up.
    HDR10 metadata is preserved (no re-encoding, stream copy only).
    Temp files are stored in the same directory as output_path for storage space.

    Args:
        input_path: Source video file
        output_path: Output file path
        segments: List of SourceSegment objects to extract
        progress_cb: Optional callback(segment_index, total_segments, segment) for progress

    Raises:
        RuntimeError: if ffmpeg operations fail
        ValueError: if segments is empty
    """
    if not segments:
        raise ValueError("No segments to cut")

    tmpdir = output_path.parent / ".video_cut_tmp"
    tmpdir.mkdir(exist_ok=True)

    try:
        segment_files: list[Path] = []

        for idx, segment in enumerate(segments, start=1):
            if progress_cb:
                progress_cb(idx, len(segments), segment)

            seg_output = tmpdir / f"segment_{idx:03d}.mkv"
            cut_segment(
                input_path=input_path,
                output_path=seg_output,
                start_seconds=segment.start_seconds,
                end_seconds=segment.end_seconds,
            )
            segment_files.append(seg_output)

        concat_segments(segment_files=segment_files, output_path=output_path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
