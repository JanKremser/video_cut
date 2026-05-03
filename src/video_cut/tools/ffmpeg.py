import os
import re
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable

from video_cut.cli.progress import FfmpegProgress
from video_cut.typedefs.video_typing import EncodeOptions


def _clean_env() -> dict:
    """Remove LD_LIBRARY_PATH to avoid conflicts."""
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    return env


def cut_segment(
    input_path: Path,
    output_path: Path,
    start_seconds: float,
    end_seconds: float,
    on_progress: Callable[[FfmpegProgress], None] | None = None,
) -> None:
    """Cut a segment from input_path using FFmpeg with stream copy (no re-encoding).

    Copies all video, audio and subtitle streams.

    Args:
        input_path: Source video file
        output_path: Output segment file
        start_seconds: Start time in seconds
        end_seconds: End time in seconds (exclusive)
        on_progress: Optional callback for progress updates

    Raises:
        RuntimeError: if ffmpeg fails
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start_seconds),
        "-to", str(end_seconds),
        "-i", str(input_path),
        "-map", "0:v:0",
        "-map", "0:a",
        "-map", "0:s?",
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "copy",
    ]

    if on_progress:
        cmd.extend(["-progress", "pipe:2"])

    cmd.append(str(output_path))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE if on_progress else subprocess.DEVNULL,
            stderr=subprocess.PIPE if on_progress else subprocess.DEVNULL,
            text=True,
            env=_clean_env(),
        )

        if on_progress:
            reader = threading.Thread(
                target=_progress_reader_thread,
                args=(process, on_progress),
                daemon=True,
            )
            reader.start()

        returncode = process.wait()
        if returncode != 0:
            raise RuntimeError(
                f"FFmpeg failed to cut segment {start_seconds}s-{end_seconds}s"
            )
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found in PATH")


def concat_segments(segment_files: list[Path], output_path: Path) -> None:
    """Concatenate multiple segments into a single output file using FFmpeg concat demuxer.

    Copies all video, audio and subtitle streams.

    Args:
        segment_files: List of segment file paths (in order)
        output_path: Output file path

    Raises:
        RuntimeError: if ffmpeg fails or concat list cannot be created
    """
    if not segment_files:
        raise ValueError("No segments to concatenate")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for seg_file in segment_files:
            f.write(f"file '{seg_file.absolute()}'\n")
        concat_list_path = f.name

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
                "-map", "0:v:0",
                "-map", "0:a",
                "-map", "0:s?",
                "-c:v", "copy",
                "-c:a", "copy",
                "-c:s", "copy",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            check=True,
            env=_clean_env(),
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg failed to concatenate segments: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found in PATH")
    finally:
        Path(concat_list_path).unlink(missing_ok=True)


def cut_segment_reencode(
    input_path: Path,
    output_path: Path,
    start_seconds: float,
    end_seconds: float,
    encode_opts: EncodeOptions,
    on_progress: Callable[[FfmpegProgress], None] | None = None,
) -> None:
    """Cut a segment using libx265 re-encoding with HDR10 support.

    Frame-accurate cutting with proper HDR10 metadata handling.

    Args:
        input_path: Source video file
        output_path: Output segment file
        start_seconds: Start time in seconds
        end_seconds: End time in seconds
        encode_opts: Encoding options (crf, preset, hdr metadata)
        on_progress: Optional callback for progress updates

    Raises:
        RuntimeError: if ffmpeg fails
    """
    x265_params = _build_x265_params(encode_opts)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start_seconds),
        "-to", str(end_seconds),
        "-i", str(input_path),
        "-map", "0:v:0",
        "-map", "0:a",
        "-map", "0:s?",
        "-c:v", "libx265",
        "-crf", str(encode_opts.crf),
        "-preset", encode_opts.preset,
        "-pix_fmt", "yuv420p10le",
        "-x265-params", x265_params,
        "-c:a", "copy",
        "-c:s", "copy",
    ]

    if on_progress:
        cmd.extend(["-progress", "pipe:2"])

    cmd.append(str(output_path))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE if on_progress else subprocess.DEVNULL,
            stderr=subprocess.PIPE if on_progress else subprocess.DEVNULL,
            text=True,
            env=_clean_env(),
        )

        if on_progress:
            reader = threading.Thread(
                target=_progress_reader_thread,
                args=(process, on_progress),
                daemon=True,
            )
            reader.start()

        returncode = process.wait()
        if returncode != 0:
            raise RuntimeError(
                f"FFmpeg failed to encode segment {start_seconds}s-{end_seconds}s"
            )
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found in PATH")


def _build_x265_params(encode_opts: EncodeOptions) -> str:
    """Build x265-params string with HDR10 settings."""
    params = [
        "colorprim=bt2020",
        "transfer=smpte2084",
        "colormatrix=bt2020nc",
        "hdr-opt=1",
        "hdr10=1",
        "repeat-headers=1",
    ]

    if encode_opts.hdr and encode_opts.hdr.master_display:
        params.append(f"master-display={encode_opts.hdr.master_display}")

    if encode_opts.hdr and encode_opts.hdr.max_cll:
        params.append(f"max-cll={encode_opts.hdr.max_cll}")

    return ":".join(params)


class _ProgressAccumulator:
    """Accumulates FFmpeg progress key=value pairs until progress=continue."""
    def __init__(self):
        self.data = {}

    def add_line(self, line: str) -> FfmpegProgress | None:
        """Add a progress line and return FfmpegProgress if complete.

        Returns:
            FfmpegProgress when progress=continue is found, None otherwise
        """
        line = line.strip()
        if not line or "=" not in line:
            return None

        key, value = line.split("=", 1)
        self.data[key] = value

        if key == "progress" and value in ("continue", "end"):
            return self._build_progress()

        return None

    def _build_progress(self) -> FfmpegProgress:
        """Build FfmpegProgress from accumulated data."""
        progress = FfmpegProgress()

        try:
            if "frame" in self.data:
                progress.frame = int(self.data["frame"])
            if "fps" in self.data:
                progress.fps = float(self.data["fps"])
            if "speed" in self.data:
                match = re.search(r"([\d.]+)x", self.data["speed"])
                if match:
                    progress.speed = float(match.group(1))
            if "bitrate" in self.data:
                match = re.search(r"([\d.]+)", self.data["bitrate"])
                if match:
                    progress.bitrate_kbps = float(match.group(1))
            if "total_size" in self.data:
                progress.total_size_bytes = int(self.data["total_size"])
        except (ValueError, AttributeError, KeyError):
            pass

        self.data.clear()
        return progress


def _progress_reader_thread(
    process: subprocess.Popen,
    on_progress: Callable[[FfmpegProgress], None],
) -> None:
    """Read FFmpeg progress output in a separate thread.

    Args:
        process: subprocess.Popen object for FFmpeg
        on_progress: Callback function called with each progress update
    """
    try:
        if process.stderr is None:
            return

        accumulator = _ProgressAccumulator()

        for line in iter(process.stderr.readline, ""):
            if not line:
                break

            progress = accumulator.add_line(line)
            if progress:
                on_progress(progress)
    except Exception:
        pass
