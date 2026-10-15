# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Ricerca, download e aggiornamento di ffmpeg nella cartella tools/.

ffmpeg e' un programma separato: viene cercato, nell'ordine, in
tools/ffmpeg/ffmpeg.exe accanto al programma, nel PATH di sistema e, se c'e',
nel pacchetto Python imageio-ffmpeg. Il download prende il build Windows
"release essentials" di gyan.dev, quello indicato dal sito ufficiale di FFmpeg
(https://ffmpeg.org/download.html#build-windows): dallo zip si tengono solo
ffmpeg.exe, LICENSE e README. Nessuna installazione globale, nessuna modifica
al PATH, nessun privilegio amministrativo: tutto resta dentro tools/.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import __version__, procs
from .config import APP_DIR
from .i18n import tr

TOOLS_DIR = APP_DIR / "tools"
FFMPEG_DIR = TOOLS_DIR / "ffmpeg"
FFMPEG_EXE = FFMPEG_DIR / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
VERSION_FILE = FFMPEG_DIR / "VERSION"

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
FFMPEG_VERSION_URL = "https://www.gyan.dev/ffmpeg/builds/release-version"
FFMPEG_PAGE = "https://www.gyan.dev/ffmpeg/builds/"
KEEP_FILES = ("LICENSE", "README.txt")

USER_AGENT = f"VideoSlicer/{__version__}"
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

ProgressCb = Callable[[str, int, int], None]


class ToolsError(RuntimeError):
    """Errore durante la verifica o il download di ffmpeg."""


class Cancelled(Exception):
    """Download interrotto dall'utente."""


@dataclass
class Status:
    path: Path | None
    source: str = ""      # "tools", "path", "package" o ""
    version: str = ""

    @property
    def present(self) -> bool:
        return self.path is not None


def find() -> tuple[Path | None, str]:
    """Percorso di ffmpeg e da dove viene: tools/, PATH o pacchetto imageio-ffmpeg."""
    if FFMPEG_EXE.is_file():
        return FFMPEG_EXE, "tools"
    found = shutil.which("ffmpeg")
    if found:
        return Path(found), "path"
    try:
        import imageio_ffmpeg  # dipendenza facoltativa

        return Path(imageio_ffmpeg.get_ffmpeg_exe()), "package"
    except Exception:  # noqa: BLE001 - pacchetto assente o binario non disponibile
        return None, ""


def version_of(exe: Path) -> str:
    """Versione stampata da `ffmpeg -version` (es. "7.1-essentials_build-www.gyan.dev")."""
    try:
        result = procs.run([str(exe), "-version"], timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    first = result.stdout.decode("utf-8", "replace").splitlines()[:1]
    if not first or not first[0].startswith("ffmpeg version "):
        return ""
    return first[0].split()[2]


def status() -> Status:
    """Stato corrente: dove sta ffmpeg e che versione e' (la lettura avvia un processo)."""
    path, source = find()
    if path is None:
        return Status(None)
    return Status(path, source, version_of(path))


def installed_release() -> str:
    """Versione di release scritta in tools/ffmpeg/VERSION dall'ultimo download ("" se non c'e')."""
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


# ----------------------------------------------------------------- download

def _open(url: str, timeout: float = 30.0):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(request, timeout=timeout)


def latest_release() -> str:
    """Ultima versione di release pubblicata da gyan.dev (es. "7.1")."""
    try:
        with _open(FFMPEG_VERSION_URL) as response:
            text = response.read(200).decode("utf-8", "replace").strip()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise ToolsError(tr("Cannot check the latest ffmpeg version: {error}").format(error=exc)) from exc
    if not text or len(text) > 40 or "\n" in text:
        raise ToolsError(tr("Unexpected answer from the ffmpeg download site."))
    return text


def _download(url: str, target: Path, label: str, progress: ProgressCb | None,
              cancel: threading.Event | None) -> None:
    """Scarica un file mostrando l'avanzamento; si ferma se `cancel` viene impostato."""
    try:
        with _open(url, timeout=60) as response:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            with target.open("wb") as handle:
                while True:
                    if cancel is not None and cancel.is_set():
                        raise Cancelled()
                    block = response.read(256 * 1024)
                    if not block:
                        break
                    handle.write(block)
                    done += len(block)
                    if progress:
                        progress(tr("Downloading {label}").format(label=label), done, total)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise ToolsError(tr("Download of {label} failed: {error}").format(label=label, error=exc)) from exc


def _extract_wanted(archive: Path, destination: Path) -> None:
    """Prende dallo zip solo ffmpeg.exe, LICENSE e README, rifiutando percorsi sospetti."""
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    wanted = {FFMPEG_EXE.name: "bin/" + FFMPEG_EXE.name}
    for name in KEEP_FILES:
        wanted[name] = name
    found: set[str] = set()
    try:
        with zipfile.ZipFile(archive) as zf:
            for member in zf.namelist():
                if not (root / member).resolve().is_relative_to(root):
                    raise ToolsError(tr("Invalid archive: suspicious path '{member}'.").format(member=member))
                parts = member.replace("\\", "/").split("/")
                for out_name, tail in wanted.items():
                    if "/".join(parts[-tail.count("/") - 1:]) == tail and out_name not in found:
                        with zf.open(member) as src, (destination / out_name).open("wb") as dst:
                            shutil.copyfileobj(src, dst, 1024 * 1024)
                        found.add(out_name)
    except zipfile.BadZipFile as exc:
        raise ToolsError(tr("The downloaded file is not a valid zip archive.")) from exc
    if FFMPEG_EXE.name not in found:
        raise ToolsError(tr("The downloaded package does not contain {name}.").format(name=FFMPEG_EXE.name))


def _replace_dir(source: Path, target: Path) -> None:
    """Sostituisce la cartella di destinazione con il contenuto scaricato."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        backup = target.with_name(target.name + ".old")
        shutil.rmtree(backup, ignore_errors=True)
        try:
            target.rename(backup)
        except OSError as exc:
            raise ToolsError(
                tr("Cannot update '{name}': files in use. Wait for the running extraction and try again.")
                .format(name=target.name)
            ) from exc
        shutil.rmtree(backup, ignore_errors=True)
    shutil.move(str(source), str(target))


def install(progress: ProgressCb | None = None, cancel: threading.Event | None = None) -> Path:
    """Scarica il build ufficiale e lascia ffmpeg.exe in tools/ffmpeg/. Restituisce l'eseguibile."""
    if sys.platform != "win32":
        raise ToolsError(tr("Automatic download is available on Windows only: install ffmpeg with the "
                            "system package manager."))
    release = ""
    try:
        release = latest_release()
    except ToolsError:
        pass  # la versione serve solo per i controlli futuri: il download puo' procedere lo stesso
    with tempfile.TemporaryDirectory(prefix="videoslicer-") as tmp:
        tmp_dir = Path(tmp)
        archive = tmp_dir / "ffmpeg.zip"
        _download(FFMPEG_URL, archive, "ffmpeg", progress, cancel)
        if progress:
            progress(tr("Extracting ffmpeg"), 0, 0)
        out = tmp_dir / "ffmpeg"
        _extract_wanted(archive, out)
        if not version_of(out / FFMPEG_EXE.name):
            raise ToolsError(tr("The downloaded ffmpeg does not run on this PC."))
        if release:
            (out / VERSION_FILE.name).write_text(release + "\n", encoding="utf-8")
        _replace_dir(out, FFMPEG_DIR)
    if not FFMPEG_EXE.is_file():
        raise ToolsError(tr("{name} is missing after extraction.").format(name=FFMPEG_EXE.name))
    return FFMPEG_EXE
