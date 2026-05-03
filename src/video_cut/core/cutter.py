import shutil
import time
from pathlib import Path

from video_cut.cli.progress import FfmpegProgress, render_progress
from video_cut.tools.ffmpeg import concat_segments, cut_segment, cut_all_segments_reencode
from video_cut.typedefs.otio_typing import SourceSegment
from video_cut.typedefs.video_typing import EncodeOptions


def cut_video(
    input_path: Path,
    output_path: Path,
    segments: list[SourceSegment],
    video_fps: float,
    encode_opts: EncodeOptions | None = None,
    audio_stream_count: int = 1,
) -> None:
    """Cut and merge video segments using FFmpeg.

    For re-encoding: single FFmpeg pass with filter_complex (no intermediate files).
    For stream-copy: temporary segment files are created, concatenated, then cleaned up.

    Args:
        input_path: Source video file
        output_path: Output file path
        segments: List of SourceSegment objects to extract
        video_fps: Video frame rate (for progress calculation)
        encode_opts: If set, use libx265 re-encoding; if None, use stream copy
        audio_stream_count: Number of audio streams in source (for re-encoding)

    Raises:
        RuntimeError: if ffmpeg operations fail
        ValueError: if segments is empty
    """
    if not segments:
        raise ValueError("No segments to cut")

    if encode_opts:
        total_frames = sum(int(seg.duration_seconds * video_fps) for seg in segments)
        first_render = True
        start_time = time.time()

        def on_progress(progress: FfmpegProgress) -> None:
            nonlocal first_render
            render_progress(
                progress=progress,
                segment_idx=1,
                total_segments=1,
                segment_start_sec=segments[0].start_seconds,
                segment_end_sec=segments[-1].end_seconds,
                total_frames=total_frames,
                start_time=start_time,
                first_render=first_render,
            )
            first_render = False

        cut_all_segments_reencode(
            input_path=input_path,
            output_path=output_path,
            segments=segments,
            encode_opts=encode_opts,
            audio_stream_count=audio_stream_count,
            on_progress=on_progress,
        )
    else:
        tmpdir = output_path.parent / ".video_cut_tmp"
        tmpdir.mkdir(exist_ok=True)

        try:
            segment_files: list[Path] = []

            for idx, segment in enumerate(segments, start=1):
                seg_output = tmpdir / f"segment_{idx:03d}.mkv"
                total_frames = int(segment.duration_seconds * video_fps)
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
