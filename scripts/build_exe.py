# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Compila VideoSlicer in un unico eseguibile Windows con PyInstaller.

Il risultato e' dist/VideoSlicer.exe: un solo file, senza finestra console, con
l'icona «VS» e le proprieta' del file (versione, autore) compilate. Dentro ci
sono Python, le librerie, il logo e l'icona; ffmpeg no: l'eseguibile lo cerca
nella cartella tools/ accanto a se' e, se manca, propone di scaricarlo dalla
pagina Configuration. Accanto all'eseguibile finiscono anche config.json e
tools/. La cartella scripts/ serve solo allo sviluppo e non entra nel bundle.

PyInstaller viene installato nel virtualenv se non c'e'. Il pacchetto
imageio-ffmpeg, se e' installato nel virtualenv, viene escluso di proposito:
porterebbe nel bundle un ffmpeg da 100 MB che l'eseguibile non deve avere.

    .venv\\Scripts\\python.exe scripts\\build_exe.py
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from videoslicer import APP_NAME, AUTHOR, COPYRIGHT, __version__  # noqa: E402

ASSETS = ROOT / "videoslicer" / "assets"
ICON = ASSETS / "videoslicer.ico"
BUILD = ROOT / "build"
DIST = ROOT / "dist"

# Proprieta' del file mostrate da Esplora risorse (lingua 0x0409 = inglese).
VERSION_INFO = """\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={numbers}, prodvers={numbers},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0),
  ),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', {author!r}),
      StringStruct('FileDescription', {description!r}),
      StringStruct('FileVersion', {version!r}),
      StringStruct('InternalName', {name!r}),
      StringStruct('LegalCopyright', {copyright!r}),
      StringStruct('OriginalFilename', {exe!r}),
      StringStruct('ProductName', {name!r}),
      StringStruct('ProductVersion', {version!r}),
    ])]),
    VarFileInfo([VarStruct('Translation', [0x0409, 1200])]),
  ],
)
"""


def ensure_icon() -> None:
    if not ICON.is_file():
        sys.exit(f"Icona assente: {ICON}")


def ensure_pyinstaller() -> None:
    if importlib.util.find_spec("PyInstaller") is None:
        print("PyInstaller non presente: lo installo nel virtualenv…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def version_file() -> Path:
    parts = [int(p) for p in __version__.split(".") if p.isdigit()][:4]
    numbers = tuple(parts + [0] * (4 - len(parts)))
    target = BUILD / "version_info.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        VERSION_INFO.format(
            numbers=numbers, author=AUTHOR, name=APP_NAME, version=__version__,
            description=f"{APP_NAME} - lossless video frame extractor",
            copyright=COPYRIGHT, exe=f"{APP_NAME}.exe",
        ),
        encoding="utf-8",
    )
    return target


def main() -> int:
    if sys.platform != "win32":
        sys.exit("VideoSlicer si compila solo su Windows.")
    ensure_icon()
    ensure_pyinstaller()

    argv = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile", "--windowed",
        "--name", APP_NAME,
        "--icon", str(ICON),
        "--version-file", str(version_file()),
        # logo e icona: il programma li cerca accanto a theme.py
        "--add-data", f"{ASSETS}{os.pathsep}videoslicer/assets",
        # temi e caratteri di customtkinter sono file di dati, non moduli
        "--collect-data", "customtkinter",
        "--hidden-import", "PIL._tkinter_finder",
        # ffmpeg resta fuori: sta in tools/ accanto all'exe, non nel bundle
        "--exclude-module", "imageio_ffmpeg",
        "--exclude-module", "imageio",
        "--distpath", str(DIST),
        "--workpath", str(BUILD),
        "--specpath", str(BUILD),
        str(ROOT / "VideoSlicer.py"),
    ]
    code = subprocess.call(argv, cwd=ROOT)
    if code != 0:
        return code

    exe = DIST / f"{APP_NAME}.exe"
    print(f"\n{exe}  ({exe.stat().st_size / 1024 / 1024:.1f} MB)")
    print("Distribuisci l'exe da solo (con LICENSE e NOTICE): ffmpeg lo scarica l'utente in tools/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
