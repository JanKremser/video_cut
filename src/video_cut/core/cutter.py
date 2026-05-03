import shutil
import time
from pathlib import Path

from video_cut.cli.progress import FfmpegProgress, render_progress
from video_cut.tools.ffmpeg import concat_segments, cut_segment, cut_segment_reencode
from video_cut.typedefs.otio_typing import SourceSegment
from video_cut.typedefs.video_typing import EncodeOptions


def cut_video(
    input_path: Path,
    output_path: Path,
    segments: list[SourceSegment],
    video_fps: float,
    encode_opts: EncodeOptions | None = None,
) -> None:
    """Cut and merge video segments using FFmpeg.

    Creates temporary segment files, concatenates them, and cleans up.
    Displays progress bar for each segment.

    Args:
        input_path: Source video file
        output_path: Output file path
        segments: List of SourceSegment objects to extract
        video_fps: Video frame rate (for progress calculation)
        encode_opts: If set, use libx265 re-encoding; if None, use stream copy

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
            seg_output = tmpdir / f"segment_{idx:03d}.mkv"

            # Calculate total frames for this segment
            total_frames = int(segment.duration_seconds * video_fps)

            # Create progress callback for this segment
            first_render = True
            start_time = time.time()

            def on_progress(progress: FfmpegProgress) -> None:
                nonlocal first_render
                render_progress(
                    progress=progress,
                    segment_idx=idx,
                    total_segments=len(segments),
                    segment_start_sec=segment.start_seconds,
                    segment_end_sec=segment.end_seconds,
                    total_frames=total_frames,
                    start_time=start_time,
                    first_render=first_render,
                )
                first_render = False

            if encode_opts:
                cut_segment_reencode(
                    input_path=input_path,
                    output_path=seg_output,
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    encode_opts=encode_opts,
                    on_progress=on_progress,
                )
            else:
                cut_segment(
                    input_path=input_path,
                    output_path=seg_output,
                    start_seconds=segment.start_seconds,
                    end_seconds=segment.end_seconds,
                    on_progress=on_progress,
                )
            segment_files.append(seg_output)

        concat_segments(segment_files=segment_files, output_path=output_path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
