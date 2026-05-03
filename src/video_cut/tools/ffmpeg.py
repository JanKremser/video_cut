import os
import subprocess
import tempfile
from pathlib import Path


def _clean_env() -> dict:
    """Remove LD_LIBRARY_PATH to avoid conflicts."""
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    return env


def cut_segment(input_path: Path, output_path: Path, start_seconds: float, end_seconds: float) -> None:
    """Cut a segment from input_path using FFmpeg with stream copy (no re-encoding).

    Copies all video, audio and subtitle streams.

    Args:
        input_path: Source video file
        output_path: Output segment file
        start_seconds: Start time in seconds
        end_seconds: End time in seconds (exclusive)

    Raises:
        RuntimeError: if ffmpeg fails
    """
    try:
        subprocess.run(
            [
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
                str(output_path),
            ],
            capture_output=True,
            text=True,
            check=True,
            env=_clean_env(),
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"FFmpeg failed to cut segment {start_seconds}s-{end_seconds}s: {e.stderr}"
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
