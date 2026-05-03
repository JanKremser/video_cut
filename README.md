# video_cut

A powerful CLI tool for analyzing and cutting videos based on OTIO (OpenTimelineIO) timelines. Supports both fast stream-copy cutting and frame-accurate re-encoding with HDR10 preservation.

## Features

- **Timeline Analysis** — Parse OTIO timelines and identify merged source segments
- **Stream-Copy Mode** — Fast cutting using FFmpeg stream copy (default, keyframe-dependent)
- **Re-encoding Mode** — Frame-accurate cutting with libx265 encoding and HDR10 metadata support
- **Progress Display** — Real-time FFmpeg progress with ETA, speed, FPS, and visual progress bar
- **Multi-stream Support** — Preserves video, audio, and subtitle streams
- **Portable Binary** — Single-file executable via PyInstaller, no Python installation required

## Requirements

- Python 3.10+ (for development/source installation)
- FFmpeg 4.0+ with libx265 (for re-encoding mode)
- OTIO timeline files (.otio or .otioz)

## Installation

### Option 1: Pre-built Binary

Download the latest release from [GitHub Releases](https://github.com/user/video_cut/releases):

```bash
chmod +x video_cut-linux-x64
./video_cut-linux-x64 --version
```

### Option 2: From Source

Clone the repository and install:

```bash
git clone https://github.com/user/video_cut.git
cd video_cut
pip install -e .
```

## Quick Start

### Analyze a Timeline

Extract merged segments from an OTIO timeline:

```bash
video_cut analyze -t timeline.otio
```

Output:
```
Segment  1: 00:00:00.000 --> 00:00:50.000  (duration: 0m 50s)
Segment  2: 00:01:20.000 --> 00:02:00.000  (duration: 0m 40s)
Segment  3: 00:02:30.000 --> 00:03:00.000  (duration: 0m 30s)

Summary: 3 segments | 0 merged cuts | Total duration: 00:02:00.000
```

### Cut a Video (Stream-Copy)

Fast cutting without re-encoding:

```bash
video_cut cut \
  -t timeline.otio \
  -i input.mkv \
  -o output.mkv
```

### Cut a Video (Re-encoding with HDR10)

Frame-accurate cutting with HDR10 preservation:

```bash
video_cut cut \
  -t timeline.otio \
  -i input.mkv \
  -o output.mkv \
  --reencode \
  --crf 18 \
  --preset slow
```

### Dry-Run Mode

Preview cuts without writing output:

```bash
video_cut cut \
  -t timeline.otio \
  -i input.mkv \
  -o output.mkv \
  --dry-run
```

## Command Reference

### analyze

```
usage: video_cut analyze [-h] -t TIMELINE [-k TRACK] [--no-color]

options:
  -t TIMELINE, --timeline TIMELINE   Path to OTIO timeline file
  -k TRACK, --track TRACK            Track index (default: 0)
  --no-color                         Disable colored output
```

### cut

```
usage: video_cut cut [-h] -t TIMELINE -i INPUT -o OUTPUT 
                     [-k TRACK] [--no-color] [--dry-run] 
                     [--reencode] [--crf CRF] [--preset PRESET]

options:
  -t TIMELINE, --timeline TIMELINE   Path to OTIO timeline file
  -i INPUT, --input INPUT            Input video file
  -o OUTPUT, --output OUTPUT         Output video file
  -k TRACK, --track TRACK            Track index (default: 0)
  --no-color                         Disable colored output
  --dry-run                          Preview cuts without writing
  --reencode                         Use libx265 re-encoding (frame-accurate)
  --crf CRF                          Quality (0-51, default: 18)
  --preset PRESET                    Encoding speed (ultrafast-veryslow, default: slow)
```

## Build from Source

### Local Build

```bash
./build.sh
# Binary: dist/video_cut (11 MB, single-file ELF)
```

### Docker Build (Reproducible)

```bash
./build_with_docker.sh
# Same binary as GitHub Actions workflow
```

## Modes Explained

### Stream-Copy Mode (Default)

- **Speed**: Very fast (minimal processing)
- **Accuracy**: Keyframe-dependent (cuts may not be exact frame)
- **Use Case**: Quick editorial cuts, when precision isn't critical
- **Codec**: Same as input (no re-encoding)

### Re-encoding Mode (--reencode)

- **Speed**: Slow (full encoding pass)
- **Accuracy**: Frame-accurate (exact cuts preserved)
- **Use Case**: Precision editing, archival, HDR10 workflows
- **Codec**: libx265 (H.265 / HEVC)
- **HDR Support**: Automatic extraction and preservation of:
  - Master Display (gamut/luminance)
  - MaxCLL (content light level)
  - BT.2020 color primaries
  - SMPTE 2084 transfer function

## HDR10 Support

When using `--reencode` on HDR10 content:

1. **Automatic Metadata Extraction** — Reads master display and max-cll from source
2. **x265 Configuration** — Sets appropriate color space, transfer, and hdr-opt flags
3. **Frame Accuracy** — Ensures HDR metadata aligns with edited frames

Example workflow:

```bash
video_cut cut \
  -t hdr_timeline.otio \
  -i source_hdr10.mkv \
  -o output_hdr10.mkv \
  --reencode --crf 18 --preset slow
```

## Troubleshooting

### "ffmpeg not found in PATH"

Install FFmpeg:
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **Arch**: `sudo pacman -S ffmpeg`

### "No space left on device" during re-encoding

Temporary files are created in `output_path.parent/.video_cut_tmp`. Ensure the output directory's filesystem has at least 2x the input file size available.

### Subtitles not preserved

Use `--reencode` mode, which always copies subtitle streams. Stream-copy mode depends on FFmpeg's ability to mux all streams.

### Cuts don't align to expected frames (stream-copy mode)

This is expected—stream-copy is keyframe-dependent. Use `--reencode` for frame-accuracy.

## Development

### Install Development Dependencies

```bash
pip install -e ".[build]"
```

### Run Tests (if available)

```bash
python -m pytest tests/
```

### Debug with VSCode

Launch configurations are defined in `.vscode/launch.json`:
- `Analyze`
- `Cut (Stream-Copy)`
- `Cut (Re-encode)`
- `Cut (Dry-Run)`

## License

MIT License — see LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `./build.sh`
5. Submit a pull request

## Support

For issues, feature requests, or questions:
- Open an issue on [GitHub Issues](https://github.com/user/video_cut/issues)
- Check existing documentation in `CLAUDE.md` for developer notes

---

**Version**: 0.1.0  
**Last Updated**: 2026-05-03
