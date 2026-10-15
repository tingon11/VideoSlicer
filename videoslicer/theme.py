# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Aspetto dell'interfaccia: tema scuro stile Seity (lo stesso di AndrOsint e TagFaces).

Palette, caratteri e tema CustomTkinter. Il tema e' solo scuro: apply() va
chiamata una volta, prima di creare qualsiasi widget.
"""

from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont

import customtkinter as ctk

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_FILE = ASSETS / "logo.png"
ICON_FILE = ASSETS / "videoslicer.ico"
APP_USER_MODEL_ID = "AndreaCumini.VideoSlicer"

PAD = 12
GAP = 8

# ------------------------------------------- palette: scuro, essenziale, un accento
BG = "#07090c"
PANEL = "#0d1117"
PANEL_2 = "#121821"
PANEL_3 = "#161d27"
BORDER = "#1c2530"
BORDER_STRONG = "#2a3644"
HOVER = "#18212c"
INPUT = "#0a0e13"
TEXT = "#d5dde6"
TEXT_SOFT = "#aab6c3"
TEXT_DIM = "#6e7b89"
TEXT_FAINT = "#3e4955"
# accento = colore della seconda parte del logo ("Slicer")
ACCENT = "#5cc8c0"
ACCENT_DIM = "#2f8f89"
ACCENT_BG = "#0f2423"
SELECT_BG = "#15332f"
OK = "#34d399"
WARN = "#fbbf24"
ERR = "#f87171"

# pulsanti pieni: testo chiaro leggibile su tutti
BTN = "#2f8f89"
BTN_HOVER = "#3aa9a1"
DANGER = "#b42335"
DANGER_HOVER = "#8f1c2a"
NEUTRAL = "#1f2a36"
NEUTRAL_HOVER = "#2a3746"
BTN_TEXT = "#f1f4fd"
CLOSE_HOVER = "#c42b1c"

# colori dei segnaposto sulla timeline
MARK_IN = OK
MARK_OUT = WARN

# ----------------------------------------------------------------- caratteri
UI_FONTS = ["Segoe UI Variable Text", "Segoe UI", "Inter", "Helvetica Neue", "DejaVu Sans"]
MONO_FONTS = ["Cascadia Mono", "JetBrains Mono", "Consolas", "DejaVu Sans Mono", "Menlo"]
ICON_FONTS = ["Segoe Fluent Icons", "Segoe MDL2 Assets"]
_picked: dict[str, str] = {}


def _pick(key: str, candidates: list[str], fallback: str) -> str:
    if key in _picked:
        return _picked[key]
    root = tk._default_root
    if root is None:
        return fallback  # nessuna finestra ancora: non si memorizza
    try:
        available = {name.lower(): name for name in tkfont.families(root)}
    except tk.TclError:
        return fallback
    _picked[key] = next((available[c.lower()] for c in candidates if c.lower() in available), fallback)
    return _picked[key]


def ui_font() -> str:
    return _pick("ui", UI_FONTS, "Segoe UI")


def mono_font() -> str:
    return _pick("mono", MONO_FONTS, "Consolas")


def icon_font() -> str:
    """Carattere delle icone di Windows; stringa vuota se non c'e'."""
    return _pick("icons", ICON_FONTS, "")


class Fonts:
    """Caratteri condivisi: vanno creati dopo la finestra principale."""

    def __init__(self) -> None:
        ui, mono = ui_font(), mono_font()
        self.body = ctk.CTkFont(family=ui, size=12)
        self.small = ctk.CTkFont(family=ui, size=11)
        self.bold = ctk.CTkFont(family=ui, size=12, weight="bold")
        self.title = ctk.CTkFont(family=mono, size=10, weight="bold")   # titoli dei riquadri
        self.page = ctk.CTkFont(family=ui, size=19, weight="bold")      # titolo della pagina
        self.button = ctk.CTkFont(family=ui, size=12, weight="bold")
        self.mono = ctk.CTkFont(family=mono, size=12)
        self.mono_big = ctk.CTkFont(family=mono, size=15, weight="bold")  # tempo corrente
        self.caption = ctk.CTkFont(family=mono, size=9, weight="bold")  # etichette maiuscole
        self.tiny = ctk.CTkFont(family=mono, size=9)

    def icon(self, size: int) -> ctk.CTkFont:
        return ctk.CTkFont(family=icon_font() or mono_font(), size=size)


# --------------------------------------------------------- tema CustomTkinter
_THEME = {
    "CTk": {"fg_color": [BG, BG]},
    "CTkToplevel": {"fg_color": [BG, BG]},
    "CTkFrame": {
        "corner_radius": 4, "border_width": 0,
        "fg_color": [PANEL, PANEL],
        "top_fg_color": [PANEL_2, PANEL_2],
        "border_color": [BORDER, BORDER],
    },
    "CTkButton": {
        "corner_radius": 4, "border_width": 0,
        "fg_color": [BTN, BTN],
        "hover_color": [BTN_HOVER, BTN_HOVER],
        "border_color": [BORDER, BORDER],
        "text_color": [BTN_TEXT, BTN_TEXT],
        "text_color_disabled": [TEXT_FAINT, TEXT_FAINT],
    },
    "CTkLabel": {
        "corner_radius": 0, "fg_color": "transparent",
        "text_color": [TEXT, TEXT],
    },
    "CTkEntry": {
        "corner_radius": 4, "border_width": 1,
        "fg_color": [INPUT, INPUT],
        "border_color": [BORDER, BORDER],
        "text_color": [TEXT, TEXT],
        "placeholder_text_color": [TEXT_FAINT, TEXT_FAINT],
    },
    "CTkCheckBox": {
        "corner_radius": 3, "border_width": 2,
        "fg_color": [ACCENT_DIM, ACCENT_DIM],
        "border_color": [BORDER_STRONG, BORDER_STRONG],
        "hover_color": [BTN_HOVER, BTN_HOVER],
        "checkmark_color": [BTN_TEXT, BTN_TEXT],
        "text_color": [TEXT, TEXT],
        "text_color_disabled": [TEXT_FAINT, TEXT_FAINT],
    },
    "CTkSwitch": {
        "corner_radius": 1000, "border_width": 3, "button_length": 0,
        "fg_color": [BORDER_STRONG, BORDER_STRONG],
        "progress_color": [ACCENT_DIM, ACCENT_DIM],
        "button_color": [TEXT_SOFT, TEXT_SOFT],
        "button_hover_color": ["#ffffff", "#ffffff"],
        "text_color": [TEXT, TEXT],
        "text_color_disabled": [TEXT_FAINT, TEXT_FAINT],
    },
    "CTkProgressBar": {
        "corner_radius": 1000, "border_width": 0,
        "fg_color": [PANEL_3, PANEL_3],
        "progress_color": [ACCENT, ACCENT],
        "border_color": [BORDER, BORDER],
    },
    "CTkOptionMenu": {
        "corner_radius": 4,
        "fg_color": [PANEL_2, PANEL_2],
        "button_color": [PANEL_3, PANEL_3],
        "button_hover_color": [HOVER, HOVER],
        "text_color": [TEXT, TEXT],
        "text_color_disabled": [TEXT_FAINT, TEXT_FAINT],
    },
    "CTkScrollbar": {
        "corner_radius": 1000, "border_spacing": 4, "fg_color": "transparent",
        "button_color": [BORDER, BORDER],
        "button_hover_color": [BORDER_STRONG, BORDER_STRONG],
    },
    "CTkTextbox": {
        "corner_radius": 4, "border_width": 0,
        "fg_color": [INPUT, INPUT],
        "border_color": [BORDER, BORDER],
        "text_color": [TEXT, TEXT],
        "scrollbar_button_color": [BORDER, BORDER],
        "scrollbar_button_hover_color": [BORDER_STRONG, BORDER_STRONG],
    },
    "DropdownMenu": {
        "fg_color": [PANEL_2, PANEL_2],
        "hover_color": [SELECT_BG, SELECT_BG],
        "text_color": [TEXT, TEXT],
    },
}


def _deep_update(target: dict, source: dict) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value


def apply() -> None:
    """Imposta il tema: va chiamata una volta, prima di creare qualsiasi widget."""
    if sys.platform == "win32":
        # Identita' propria nella barra di Windows: senza, le finestre finiscono
        # sotto python.exe con l'icona di Python.
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except (AttributeError, OSError):
            pass
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")  # base, poi sovrascritta
    _deep_update(ctk.ThemeManager.theme, _THEME)


def set_icon(window) -> None:
    """Icona dell'applicazione sulla finestra (e, per la principale, nella barra di Windows)."""
    if not ICON_FILE.is_file():
        return
    try:
        if isinstance(window, ctk.CTk):
            window.iconbitmap(default=str(ICON_FILE))
        window.iconbitmap(str(ICON_FILE))
    except tk.TclError:
        pass


def logo(height: int) -> ctk.CTkImage | None:
    """Logo alto `height` punti logici; None se il file manca."""
    try:
        from PIL import Image

        image = Image.open(LOGO_FILE).convert("RGBA")
    except (OSError, ImportError):
        return None
    width = round(image.width * height / image.height)
    return ctk.CTkImage(light_image=image, dark_image=image, size=(width, height))


def scaling(widget) -> float:
    return ctk.ScalingTracker.get_widget_scaling(widget)


def window_scaling(window) -> float:
    return ctk.ScalingTracker.get_window_scaling(window) or 1.0
