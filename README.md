# VideoSlicer

**English** · [Italiano](README.it.md)

Splits a video, or a range of it, into single frames **without quality
loss**, with a preview on a timeline that zooms down to the single frame,
in/out markers, frame-by-frame navigation and saving of the single frame at
full resolution.

**Author: Andrea Cumini — [www.osintinfo.net](https://www.osintinfo.net) — andrea@osintinfo.net**

The interface is written in Python with **customtkinter**, in the same style
as AndrOsint and TagFaces (the Seity dark theme). Decoding is done by
**ffmpeg**, run as a separate program.

## Requirements

- Windows 10/11 (on other systems it runs with the standard title bar)
- Python 3.10 or later (with Tkinter, included in the official installer)
- ffmpeg, as a **standalone** program: VideoSlicer downloads it into the
  `tools/ffmpeg/` folder next to the program (see *FFmpeg* below); an
  ffmpeg already in the PATH is used too

Python dependencies (`requirements.txt`): `customtkinter` and `pillow`.

```bash
python -m pip install -r requirements.txt
```

## Running

```bash
python VideoSlicer.py
```

Or double-click `Avvia.bat` (it starts without a console window and uses the
`.venv` virtualenv if present). The video to open can be passed as an
argument: `python VideoSlicer.py movie.mp4`.

## Single executable

To get a single `VideoSlicer.exe` that runs without Python installed:

```bash
.venv\Scripts\python.exe scripts\build_exe.py
```

The script installs PyInstaller into the virtualenv if it is missing and
writes `dist\VideoSlicer.exe` (one file, no console window, "VS" icon and
file properties). ffmpeg is deliberately left out of the bundle: the
executable looks for it in `tools\ffmpeg\` next to itself and offers to
download it. Next to the executable also go `config.json` and `tools\`. To
distribute, ship the `.exe` with `LICENSE` and `NOTICE`; `scripts\` is
development tooling only.

## FFmpeg

ffmpeg is not included: it is a separate program under its own license. On
the first start, if no ffmpeg is found, the **Configuration** page opens on
the *FFmpeg* box: **Download / Update** takes the official Windows build
("release essentials") from <https://www.gyan.dev/ffmpeg/builds/>, the one
linked from the FFmpeg site, and keeps only `ffmpeg.exe`, `LICENSE` and
`README.txt` in `tools/ffmpeg/`. About 110 MB, with progress bar and
**Cancel**. No installation, no change to the PATH, no administrator rights.

**Check for updates** compares the release written at the last download
with the latest one published and offers to download it. **Check** rereads
where ffmpeg is and its version. ffmpeg is looked up in this order:
`tools/ffmpeg/ffmpeg.exe`, the system PATH, and, if the optional Python
package `imageio-ffmpeg` is installed, its bundled binary.

To distribute the program, copy the folder without `tools/`: every user
downloads ffmpeg with one click.

## Language

The interface is in **English** (default) or **Italian**. Switch with the
**EN / IT** buttons in the *Language* box of the **Configuration** page:
the change is immediate, with no restart, and the choice is saved in
`config.json`. Only the log keeps the lines already written in the language
they were produced in.

In the code the texts are in English; the Italian translation is in
`videoslicer/translations.py` (keys are the English texts).

## Usage

The interface has two pages, in the side bar (Ctrl+1 / Ctrl+2):
**Configuration** (open video, destination folder and output format,
language, credits) and **Extraction** (preview, timeline, extraction). The
preview takes the whole width of the page and grows with the window:
maximize it to see it large.

1. **Open video…** (or Ctrl+O, or the icon in the VIDEO box at the top). The
   *Source* box shows duration, number of frames, resolution, codec and color
   depth.
2. Choose the range on the **timeline**:
   - **Ctrl+wheel** zooms in and out around the mouse, down to the single
     frames; **+** / **−** / **All** / **Selection** do the same from the
     buttons. The **wheel** scrolls; the bar at the bottom shows the whole
     video and can be dragged.
   - Clicking or dragging on the film strip moves the **cursor** and updates
     the preview. **← →** step one frame, **Shift+← →** ten, **Home / End**
     go to the first and last frame; Shift+wheel over the preview does the
     same. The *CURSOR* field accepts a time (`1:23.456`, `83.4`) or a frame
     (`f2000`).
   - In the **preview** the wheel zooms around the mouse (up to 32 pixels per
     video pixel; above 3x the real pixels are shown without smoothing),
     dragging pans, double-click fits the frame again. Zooming in requests
     the frame at full resolution; the zoom is kept when stepping frames.
   - **In [I]** and **Out [O]** put the markers at the cursor; the **I** and
     **O** flags can also be dragged directly, and the IN / OUT fields accept
     a time or a frame.
3. In **Output** choose folder, format (PNG, TIFF, BMP), color depth
   (automatic: 16 bits per channel when the source is 10-bit or more),
   prefix, digits, numbering (frame number in the video or sequential from 1)
   and step (1 = every frame, 5 = one every five).
4. **Extract frames** (Extraction page): progress is in the *Extraction*
   box, which also summarizes format and file names; **Cancel** stops,
   **Open folder** shows the result. The log appears below when the window
   is tall enough.
5. **Save frame** (or Ctrl+S) writes the single frame shown in the preview at
   full resolution, in the same lossless format.

## Lossless: what it means

A compressed video (H.264, HEVC, VP9…) does not contain "original" pictures:
it contains the data from which the decoder rebuilds every frame.
VideoSlicer takes exactly that decoded frame and writes it in a format that
does not recompress with loss:

- **PNG** (lossless compression, recommended), **TIFF** (LZW, lossless),
  **BMP** (uncompressed, 8 bits per channel only);
- the conversion from the video pixel format (e.g. `yuv420p`) to RGB uses
  ffmpeg's full-resolution chroma interpolation and accurate rounding
  (`accurate_rnd+full_chroma_int`);
- **10/12-bit** sources come out at **16 bits per channel** (PNG `rgb48`,
  TIFF `rgb48`), so no depth is lost; the alpha channel, if any, is kept;
- no frame is duplicated or dropped (`-fps_mode passthrough`): the count is
  exact and the numbering matches the frame in the video.

With variable frame rate (VFR) videos the frame number is computed from the
average frame rate, so the time/frame correspondence is approximate.

## Layout

| File | Content |
| --- | --- |
| `VideoSlicer.py` | entry point |
| `videoslicer/app.py` | main window |
| `videoslicer/timeline.py` | timeline with thumbnails, zoom and markers |
| `videoslicer/shell.py` | side navigation bar between the pages |
| `videoslicer/ffmpeg.py` | video information, previews, extraction |
| `videoslicer/tools.py` | ffmpeg lookup, download and update in `tools/` |
| `videoslicer/i18n.py`, `translations.py` | interface language and Italian translation |
| `videoslicer/theme.py`, `widgets.py`, `frameless.py` | dark theme, components, frameless window |
| `videoslicer/tasks.py` | background jobs and delivery to the GUI |
| `videoslicer/config.py` | settings in `config.json` |
| `scripts/build_exe.py` | builds the single `VideoSlicer.exe` with PyInstaller |

## License

GNU GPL v3 with additional author-attribution terms: see
[LICENSE](LICENSE) and [NOTICE](NOTICE). The line

    Andrea Cumini - andrea@osintinfo.net - www.osintinfo.net

must be kept in the interface (window footer and Credits box) and in the
documentation. The name "VideoSlicer", the logo and the "VS" icon identify
the original program: a modified version distributed to others must use a
different name and logo.

ffmpeg is a separate program under its own license (LGPL/GPL): see
<https://ffmpeg.org/legal.html>.
