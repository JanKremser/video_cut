from pathlib import Path

from video_cut.tools.ffprobe import probe_video_info
from video_cut.typedefs.video_typing import VideoInfo


class VideoValidator:
    """Validate video codec and color space (warnings only, never fatal)."""

    EXPECTED_CODEC = "hevc"
    EXPECTED_COLOR_PRIMARIES = "bt2020"
    EXPECTED_TRANSFER = "smpte2084"

    def validate(self, filepath: Path) -> VideoInfo:
        """Probe the video and warn if codec/colorspace unexpected.

        Returns:
            VideoInfo for the probed file

        Raises:
            RuntimeError: if ffprobe fails or file does not exist
        """
        info = probe_video_info(filepath)

        if info.codec_name != self.EXPECTED_CODEC:
            print(
                f"⚠ Warning: codec is '{info.codec_name}', expected '{self.EXPECTED_CODEC}'",
                flush=True,
            )

        if info.color_primaries and info.color_primaries != self.EXPECTED_COLOR_PRIMARIES:
            print(
                f"⚠ Warning: color_primaries is '{info.color_primaries}', expected '{self.EXPECTED_COLOR_PRIMARIES}'",
                flush=True,
            )

        if info.color_transfer and info.color_transfer != self.EXPECTED_TRANSFER:
            print(
                f"⚠ Warning: color_transfer is '{info.color_transfer}', expected '{self.EXPECTED_TRANSFER}'",
                flush=True,
            )

        return info
