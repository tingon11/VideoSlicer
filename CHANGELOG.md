# Changelog

The most recent section is used by `scripts/build_exe.py --release` as the
release notes: first a one-line introduction, then the list of changes.

## 1.0.0

First public release: split a video, or a range of it, into single frames without quality loss.

- **Lossless extraction** to PNG, TIFF or BMP, at 8 or 16 bits per channel (automatic for 10-bit sources), with exact frame numbering and no duplicated or dropped frames.
- **Zoomable timeline** with film-strip thumbnails, in/out markers that can be dragged, and a cursor that can be moved frame by frame.
- **Preview** with mouse-wheel zoom down to the real pixels and drag to pan; **Save frame** writes the shown frame at full resolution.
- **Two pages**: Configuration (source, output options, ffmpeg, language, credits) and Extraction (preview, timeline, extraction).
- **ffmpeg downloader**: the official Windows build is fetched into a `tools` folder next to the program, with update check; nothing is installed on the system.
- **English and Italian** interface, switchable at any time.
- Every ffmpeg process is tied to the application and ends with it, also after a crash.
