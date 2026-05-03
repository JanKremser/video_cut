from pathlib import Path

from video_cut.tools.ffprobe import probe_video_info
from video_cut.typedefs.video_typing import VideoInfo


class VideoValidator:
    """Validate video file (all codecs supported via stream copy)."""

    def validate(self, filepath: Path) -> VideoInfo:
        """Probe the video and return metadata.

        Returns:
            VideoInfo for the probed file

        Raises:
            RuntimeError: if ffprobe fails or file does not exist
        """
        return probe_video_info(filepath)
