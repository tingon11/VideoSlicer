# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Impostazioni salvate in config.json accanto al programma."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def app_dir() -> Path:
    """Cartella base dell'applicazione: accanto all'eseguibile se impacchettata con PyInstaller.

    In un bundle --onefile __file__ sta in una cartella temporanea che sparisce
    alla chiusura: config.json e tools/ devono invece restare accanto all'exe.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


APP_DIR = app_dir()
CONFIG_FILE = APP_DIR / "config.json"

DEFAULTS: dict[str, Any] = {
    "language": "en",
    "geometry": "",
    "last_video_dir": "",
    "output_dir": "",
    "format": "PNG",
    "depth": "Auto",
    "prefix": "frame_",
    "digits": 6,
    "numbering": "video",     # "video" = numero del fotogramma nel video, "one" = da 1
    "step": 1,
    "subfolder": True,
}


class Config:
    def __init__(self) -> None:
        self._data = dict(DEFAULTS)
        try:
            loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self._data.update({k: v for k, v in loaded.items() if k in DEFAULTS})
        except (OSError, ValueError):
            pass

    def get(self, key: str) -> Any:
        return self._data.get(key, DEFAULTS.get(key))

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def save(self) -> None:
        try:
            CONFIG_FILE.write_text(json.dumps(self._data, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
        except OSError:
            pass
