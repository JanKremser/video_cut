# video_cut — CLAUDE.md

Hello! This is the **video_cut** project: A CLI tool for analyzing and cutting videos based on OTIO timelines with a focus on H.265/BT.2020/HDR10 support.

## Project Overview

The tool provides two main features:

1. **analyze** — Parse OTIO timeline and extract merged source segments
2. **cut** — Cut videos with two modes:
   - **Stream-Copy** (fast, keyframe-dependent) — Default
   - **libx265 Re-encoding** (frame-accurate, HDR10 support) — with `--reencode`

## Language

Communicate with the user in **German**. German error messages and console output are preferred.

## Architecture

```
src/video_cut/
├── main.py              # Entry point
├── cli/
│   ├── args.py          # Argument parser
│   ├── cut.py           # Cut command handler
│   ├── output.py        # Output formatting
│   └── progress.py      # FFmpeg progress display (6-line terminal UI)
├── core/
│   ├── analyzer.py      # OTIO parsing and segment merging
│   ├── cutter.py        # Video orchestration (temp dir, progress, concat)
│   └── validator.py     # VideoInfo validation
├── tools/
│   ├── ffmpeg.py        # cut_segment(), cut_segment_reencode(), concat_segments()
│   ├── ffprobe.py       # VideoInfo extraction (fps parsing, codec details)
│   └── hdr_probe.py     # HDR10 metadata extraction (showinfo filter)
└── typedefs/
    ├── otio_typing.py   # RawClip, SourceSegment
    └── video_typing.py  # VideoInfo, HdrMetadata, EncodeOptions
```

## Important Technical Details

### FFmpeg Progress Parsing
- FFmpeg is invoked with `-progress pipe:2`
- Output: One `key=value` per line, blocks end with `progress=continue`
- **CRITICAL**: `_ProgressAccumulator` collects all key=value pairs until `progress=continue`, NOT individual lines!
- Important keys: `frame`, `fps`, `speed` (e.g. "2.5x"), `bitrate`, `total_size`

### HDR10 Handling
- Metadata: `master_display` (coordinates in format `G(x,y)B(x,y)R(x,y)WP(x,y)L(min,max)`)
- x265 expects normalized to 50000/10000 units
- `max_cll` (Content Light Level) stored separately
- Both optional but extracted from source and passed through

### Temporary Files
- Temp dir: `output_path.parent / .video_cut_tmp`
- Reason: Same-filesystem efficiency (no cross-mount copy)
- After concat(), all temp files deleted (shutil.rmtree)

### FPS Parsing
- FFprobe returns `r_frame_rate` in format "24000/1001" (rational)
- `_parse_fps()` splits and divides numerator/denominator
- Used for frame-count calculation in progress display

## Build & Release

### Build Locally
```bash
./build.sh
# → Binary: dist/video_cut (11MB, one-file ELF binary)
```

### Build with Docker (reproducible)
```bash
./build_with_docker.sh
# → Debian:bookworm, Python 3.12, same binary as GitHub Actions
```

### GitHub Actions Release Pipeline
- **Trigger**: `git tag v*` (e.g. `git tag v0.2.0 && git push origin v0.2.0`)
- **Workflow**: `.github/workflows/release.yml`
- **Output**: `video_cut-linux-x64` in GitHub Release
- **Spec file**: `video_cut.spec` (versioned, uses `collect_all('opentimelineio')`)

## Testing

### Available Test Files
- `test_sample.otio` — 3 cuts, total 2 minutes
- `hdr10.mkv` — HDR10 sample with BT.2020 primaries

### VSCode Debug Configurations
- Analyze (test_sample.otio)
- Cut Stream-Copy (test_sample.otio → hdr10.mkv)
- Cut Reencode (test_sample.otio → hdr10.mkv with --reencode)
- Cut Dry-Run
- Version, Help

All defined in `.vscode/launch.json`.

## Definition of Done

A feature/bug fix is complete when:
1. ✅ Code written and tested locally
2. ✅ VSCode debug configuration (if relevant) updated
3. ✅ No syntax/type errors (Python 3.10+)
4. ✅ Git commit with descriptive message
5. ✅ For large features: local build tested with `./build.sh`

## Common Errors & Solutions

**"No space left on device" during re-encoding**
- Cause: Temp dir in /tmp on different filesystem
- Fix: Create temp dir in `output_path.parent`

**Progress bar shows no ETA/Speed/FPS**
- Cause: _ProgressAccumulator parses only single lines instead of complete blocks
- Fix: Accumulator collects until `progress=continue`, then read all keys

**FFmpeg LD_LIBRARY_PATH conflict**
- Fix: `_clean_env()` removes LD_LIBRARY_PATH before subprocess start

**Subtitles missing after cut**
- Fix: `-map 0:s?` in ffmpeg cmd (optional subtitles)

## Preferences & Feedback

### Code Style
- No unnecessary comments — code should be self-explanatory
- Type hints are required (Python 3.10+ features allowed)
- Short functions, clear callbacks (closures okay for contexts like progress)
- No premature abstraction — 3 similar lines is fine

### Commit Messages
- Short, concise, imperative ("Implement", "Fix", "Update")
- German or English (user prefers German)
- For larger changes: bullet points in body

### Testing & Verification
- Always test locally with `./dist/video_cut` or VSCode debug
- Progress bar: Verify visually (6-line terminal UI)
- Re-encoding: Confirm frame accuracy with keyframe comparison

## Next Steps (if needed)

- [ ] Refine dry-run mode (more segment details)
- [ ] Make codec conversion optional (currently x265 only for reencode)
- [ ] More HDR profiles (Rec. 2100-PQ, Rec. 2100-HLG)
- [ ] Batch processing multiple timelines
- [ ] Better error handling for corrupt OTIO files

---

**Last Updated**: 2026-05-03  
**Version**: 0.1.0 (PyInstaller + GitHub Actions implemented)
