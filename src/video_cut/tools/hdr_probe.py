import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


def _clean_env() -> dict:
    """Remove LD_LIBRARY_PATH to avoid conflicts."""
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    return env


@dataclass
class HdrMetadata:
    """HDR10 metadata extracted from video file."""
    master_display: str | None
    max_cll: str | None


def extract_hdr_metadata(input_path: Path) -> HdrMetadata:
    """Extract HDR10 metadata from video using FFmpeg showinfo filter.

    Parses ffmpeg stderr for mastering display and content light level metadata
    from the first 10 frames. Returns x265-compatible format strings.

    Args:
        input_path: Path to video file

    Returns:
        HdrMetadata with master_display and max_cll (or None if not found)

    Raises:
        RuntimeError: if ffmpeg fails
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-v", "info",
                "-i", str(input_path),
                "-vf", "showinfo",
                "-frames:v", "10",
                "-f", "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=_clean_env(),
        )
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found in PATH")

    stderr = result.stderr

    master_display = _parse_master_display(stderr)
    max_cll = _parse_max_cll(stderr)

    return HdrMetadata(master_display=master_display, max_cll=max_cll)


def _parse_master_display(text: str) -> str | None:
    """Parse mastering display metadata from ffmpeg showinfo output.

    Returns x265-compatible format: G(gx,gy)B(bx,by)R(rx,ry)WP(wpx,wpy)L(max,min)
    """
    mastering_re = (
        r"(?:Mastering display metadata|side data - mastering display).*?"
        r"(?:r_x|R)\s*=\s*([\d.]+).*?(?:r_y|R)\s*=\s*([\d.]+).*?"
        r"(?:g_x|G)\s*=\s*([\d.]+).*?(?:g_y|G)\s*=\s*([\d.]+).*?"
        r"(?:b_x|B)\s*=\s*([\d.]+).*?(?:b_y|B)\s*=\s*([\d.]+).*?"
        r"(?:wp_x|WP)\s*=\s*([\d.]+).*?(?:wp_y|WP)\s*=\s*([\d.]+).*?"
        r"min_luminance\s*=\s*([\d.]+).*?max_luminance\s*=\s*([\d.]+)"
    )

    match = re.search(mastering_re, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None

    try:
        r_x, r_y, g_x, g_y, b_x, b_y, wp_x, wp_y, min_lum, max_lum = match.groups()

        r_x = int(float(r_x) * 50000)
        r_y = int(float(r_y) * 50000)
        g_x = int(float(g_x) * 50000)
        g_y = int(float(g_y) * 50000)
        b_x = int(float(b_x) * 50000)
        b_y = int(float(b_y) * 50000)
        wp_x = int(float(wp_x) * 50000)
        wp_y = int(float(wp_y) * 50000)
        min_lum = int(float(min_lum) * 10000)
        max_lum = int(float(max_lum) * 10000)

        return f"G({g_x},{g_y})B({b_x},{b_y})R({r_x},{r_y})WP({wp_x},{wp_y})L({max_lum},{min_lum})"
    except (ValueError, IndexError):
        return None


def _parse_max_cll(text: str) -> str | None:
    """Parse content light level metadata from ffmpeg showinfo output.

    Returns x265-compatible format: MaxCLL,MaxFALL
    """
    light_re = r"(?:Content light level|MaxCLL)\s*=\s*(\d+),\s*MaxFALL\s*=\s*(\d+)"

    match = re.search(light_re, text, re.IGNORECASE)
    if not match:
        return None

    try:
        maxcll, maxfall = match.groups()
        return f"{maxcll},{maxfall}"
    except (ValueError, IndexError):
        return None
