# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""VideoSlicer - punto di ingresso.

Scompone un video, o un suo intervallo, in singoli fotogrammi senza perdita di
qualita' (PNG / TIFF / BMP), con anteprima su timeline e salvataggio del
singolo fotogramma a piena risoluzione.

    python VideoSlicer.py [video]
"""

from __future__ import annotations

import sys


def _fail(message: str) -> int:
    """Segnala un avvio impossibile anche senza console (Avvia.bat usa pythonw)."""
    if sys.stderr is not None:
        print(message, file=sys.stderr)
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, "VideoSlicer", 0x10)
    return 1


def main() -> int:
    from videoslicer import i18n
    from videoslicer.config import Config

    i18n.set_language(Config().get("language"))
    try:
        from videoslicer.app import run
    except ImportError as exc:  # pragma: no cover - ambiente incompleto
        return _fail(
            i18n.tr(
                "Cannot start the interface: {error}\n\n"
                "Install the dependencies with:\n"
                "    python -m pip install -r requirements.txt"
            ).format(error=exc)
        )
    run(sys.argv[1] if len(sys.argv) > 1 else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
