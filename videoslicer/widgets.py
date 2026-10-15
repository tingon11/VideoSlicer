# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Componenti riusati dall'interfaccia: riquadri, pulsanti, note e dialoghi."""

from __future__ import annotations

import tkinter as tk
import weakref
from typing import Callable

import customtkinter as ctk

from . import frameless, theme
from .i18n import N_, Text, again, tr

_tooltips: weakref.WeakSet = weakref.WeakSet()  # per ritradurre i suggerimenti


class Card(ctk.CTkFrame):
    """Riquadro bordato con titolo in maiuscolo; il contenuto va dentro `body`."""

    def __init__(self, parent, title: str, fonts: theme.Fonts) -> None:
        super().__init__(parent, fg_color=theme.PANEL, border_width=1,
                         border_color=theme.BORDER, corner_radius=4)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        head.grid(row=0, column=0, sticky="ew", padx=theme.PAD, pady=(theme.PAD - 2, 0))
        # barretta d'accento accanto al titolo
        ctk.CTkFrame(head, fg_color=theme.ACCENT, width=2, height=11, corner_radius=0).pack(
            side="left", padx=(0, 7))
        self._title = title
        self.title_label = ctk.CTkLabel(head, text=title.upper(), font=fonts.title,
                                        text_color=theme.TEXT_DIM, anchor="w", height=14)
        self.title_label.pack(side="left", fill="x")
        # spazio a destra del titolo per eventuali comandi
        # width/height 1: un CTkFrame vuoto chiederebbe 200x200 px
        self.head_right = ctk.CTkFrame(head, fg_color="transparent", corner_radius=0, width=1, height=1)
        self.head_right.pack(side="right")

        self.body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.body.grid(row=1, column=0, sticky="nsew", padx=theme.PAD, pady=(theme.GAP, theme.PAD))

    def retranslate(self) -> None:
        self._title = again(self._title)
        self.title_label.configure(text=self._title.upper())


def button(
    parent, text: str, command, primary: bool = False, width: int = 0, danger: bool = False, **kwargs
) -> ctk.CTkButton:
    """Pulsante principale (accento), secondario (neutro) o distruttivo (bordo rosso)."""
    if danger:
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("hover_color", theme.HOVER)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", theme.ERR)
        kwargs.setdefault("text_color", theme.ERR)
    elif not primary:
        kwargs.setdefault("fg_color", theme.NEUTRAL)
        kwargs.setdefault("hover_color", theme.NEUTRAL_HOVER)
        kwargs.setdefault("text_color", theme.TEXT)
    kwargs.setdefault("font", (theme.ui_font(), 12, "bold"))
    kwargs.setdefault("height", 30)
    if width:
        kwargs["width"] = width
    return ctk.CTkButton(parent, text=text, command=command, **kwargs)


def link(parent, text: str, command) -> ctk.CTkButton:
    """Pulsante dall'aspetto di collegamento, per aprire un sito."""
    return ctk.CTkButton(
        parent, text=text, command=command, height=26, width=0, fg_color="transparent",
        hover_color=theme.HOVER, text_color=theme.ACCENT, font=(theme.ui_font(), 12, "bold"),
    )


def icon_button(parent, glyph: str, fallback: str, command, fonts: theme.Fonts,
                width: int = 34, tooltip: str = "") -> ctk.CTkButton:
    """Pulsante quadrato con un glifo di Segoe Fluent Icons (o un carattere di riserva)."""
    has_icons = bool(theme.icon_font())
    item = ctk.CTkButton(
        parent, text=glyph if has_icons else fallback, command=command, width=width, height=30,
        corner_radius=4, fg_color=theme.NEUTRAL, hover_color=theme.NEUTRAL_HOVER,
        text_color=theme.TEXT, font=fonts.icon(13) if has_icons else fonts.bold,
    )
    if tooltip:
        Tooltip(item, tooltip, fonts)
    return item


def note(parent, text: str, fonts: theme.Fonts, wraplength: int = 0) -> ctk.CTkLabel:
    """Testo esplicativo attenuato."""
    return ctk.CTkLabel(
        parent, text=text, font=fonts.small, text_color=theme.TEXT_DIM,
        anchor="w", justify="left", wraplength=wraplength,
    )


class Caption(ctk.CTkLabel):
    """Etichetta maiuscola piccola sopra un campo; conserva il testo per ritradurlo."""

    def __init__(self, parent, text: str, fonts: theme.Fonts, **kwargs) -> None:
        self._source = text
        kwargs.setdefault("text_color", theme.TEXT_FAINT)
        super().__init__(parent, text=text.upper(), font=fonts.caption, anchor="w", **kwargs)

    def retranslate(self) -> None:
        self._source = again(self._source)
        self.configure(text=self._source.upper())


def follow_width(label: ctk.CTkLabel, container, margin: int = 0) -> None:
    """Fa andare a capo il testo secondo la larghezza del contenitore."""

    def resize(event) -> None:
        # <Configure> riporta pixel reali, wraplength vuole unita' non scalate.
        label.configure(wraplength=max(120, int(event.width / theme.scaling(label)) - margin))

    container.bind("<Configure>", resize, add="+")


def caption(parent, text: str, fonts: theme.Fonts, **kwargs) -> Caption:
    """Etichetta maiuscola piccola sopra un campo."""
    return Caption(parent, text, fonts, **kwargs)


def rule(parent, horizontal: bool) -> ctk.CTkFrame:
    """Filetto di separazione da un pixel."""
    size = {"height": 1} if horizontal else {"width": 1}
    return ctk.CTkFrame(parent, fg_color=theme.BORDER, corner_radius=0, **size)


class Tooltip:
    """Suggerimento che compare sotto il widget al passaggio del mouse."""

    def __init__(self, widget, text: str, fonts: theme.Fonts, delay_ms: int = 500) -> None:
        self._widget = widget
        self._text = text
        self._fonts = fonts
        self._delay = delay_ms
        self._job: str | None = None
        self._tip: ctk.CTkToplevel | None = None
        _tooltips.add(self)
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def retranslate(self) -> None:
        self._text = again(self._text)

    def _schedule(self, _event=None) -> None:
        self._cancel()
        self._job = self._widget.after(self._delay, self._show)

    def _cancel(self) -> None:
        if self._job is not None:
            self._widget.after_cancel(self._job)
            self._job = None

    def _show(self) -> None:
        self._job = None
        if self._tip is not None:
            return
        try:
            tip = ctk.CTkToplevel(self._widget)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            tip.configure(fg_color=theme.BORDER)
            ctk.CTkLabel(
                tip, text=f"  {self._text}  ", font=self._fonts.small, text_color=theme.TEXT,
                fg_color=theme.PANEL_2, corner_radius=0, height=24,
            ).pack(padx=1, pady=1)
            x = self._widget.winfo_rootx()
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
            tip.geometry(f"+{x}+{y}")
            self._tip = tip
        except tk.TclError:
            self._tip = None

    def _hide(self, _event=None) -> None:
        self._cancel()
        tip, self._tip = self._tip, None
        if tip is not None:
            try:
                tip.destroy()
            except tk.TclError:
                pass


# ----------------------------------------------------------------- dialoghi

_ACCENT = {"info": theme.ACCENT, "question": theme.ACCENT, "warning": theme.WARN, "error": theme.ERR}
_LABEL = {"info": "INFO", "question": N_("CONFIRM"), "warning": N_("WARNING"), "error": N_("ERROR")}
_OK = [("OK", True, theme.BTN, theme.BTN_HOVER)]
_YESNO = [(N_("Yes"), True, theme.BTN, theme.BTN_HOVER), ("No", False, "ghost", theme.HOVER)]


def _show(kind: str, title: str, message: str, buttons, parent=None):
    master = parent or tk._default_root
    win = ctk.CTkToplevel(master)
    win.title(title or "")
    win.configure(fg_color=theme.BG)
    win.resizable(False, False)
    theme.set_icon(win)
    # CustomTkinter reimposta icona e barra dopo ~200 ms: si ripassa dopo.
    win.after(250, lambda: theme.set_icon(win) if win.winfo_exists() else None)
    win.after(320, lambda: frameless.style_titlebar(
        win, caption=theme.BG, text=theme.TEXT_DIM, border=theme.BORDER) if win.winfo_exists() else None)

    result = {"value": None}

    def close(value) -> None:
        result["value"] = value
        try:
            win.grab_release()
        except tk.TclError:
            pass
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", lambda: close(None))

    outer = ctk.CTkFrame(win, fg_color=theme.PANEL, border_width=1,
                         border_color=theme.BORDER, corner_radius=4)
    outer.pack(fill="both", expand=True, padx=10, pady=10)
    accent = _ACCENT.get(kind, theme.ACCENT)
    ctk.CTkFrame(outer, height=2, corner_radius=0, border_width=0, fg_color=accent).pack(
        fill="x", padx=1, pady=(1, 0))

    head = ctk.CTkFrame(outer, fg_color="transparent", border_width=0)
    head.pack(fill="x", padx=16, pady=(12, 2))
    ctk.CTkLabel(head, text="●", font=(theme.mono_font(), 11), text_color=accent).pack(side="left")
    ctk.CTkLabel(head, text=tr(_LABEL.get(kind, "INFO")), font=(theme.mono_font(), 9, "bold"),
                 text_color=theme.TEXT_DIM).pack(side="left", padx=(6, 10))
    ctk.CTkLabel(head, text=title or "", font=(theme.ui_font(), 13, "bold"),
                 text_color=theme.TEXT, anchor="w").pack(side="left", fill="x")

    ctk.CTkLabel(outer, text=message, font=(theme.ui_font(), 12), text_color=theme.TEXT_SOFT,
                 justify="left", anchor="w", wraplength=460).pack(fill="x", padx=16, pady=(6, 16))

    row = ctk.CTkFrame(outer, fg_color="transparent", border_width=0)
    row.pack(fill="x", padx=16, pady=(0, 14))
    first = None
    for text, value, color, hover in reversed(buttons):
        ghost = color == "ghost"
        item = ctk.CTkButton(
            row, text=tr(text), width=96, height=30, corner_radius=4,
            font=(theme.ui_font(), 12, "bold"),
            fg_color="transparent" if ghost else color,
            hover_color=theme.HOVER if ghost else hover,
            border_width=1 if ghost else 0, border_color=theme.BORDER_STRONG,
            text_color=theme.TEXT if ghost else theme.BTN_TEXT,
            command=lambda v=value: close(v),
        )
        item.pack(side="right", padx=(8, 0))
        first = item
    win.bind("<Escape>", lambda _e: close(None if len(buttons) > 1 else True))
    win.bind("<Return>", lambda _e: close(buttons[0][1]))

    # al centro della finestra madre
    win.update_idletasks()
    try:
        mx, my = master.winfo_rootx(), master.winfo_rooty()
        mw, mh = master.winfo_width(), master.winfo_height()
        x = mx + (mw - win.winfo_width()) // 2
        y = my + (mh - win.winfo_height()) // 2
        win.geometry(f"+{max(0, x)}+{max(0, y)}")
    except tk.TclError:
        pass
    win.transient(master)
    win.grab_set()
    if first is not None:
        first.focus_set()
    master.wait_window(win)
    return result["value"]


class messagebox:
    """Stessa firma di tkinter.messagebox, aspetto del tema."""

    @staticmethod
    def showinfo(title: str, message: str, parent=None) -> None:
        _show("info", title, message, _OK, parent)

    @staticmethod
    def showwarning(title: str, message: str, parent=None) -> None:
        _show("warning", title, message, _OK, parent)

    @staticmethod
    def showerror(title: str, message: str, parent=None) -> None:
        _show("error", title, message, _OK, parent)

    @staticmethod
    def askyesno(title: str, message: str, parent=None) -> bool:
        return bool(_show("question", title, message, _YESNO, parent))


def retranslate_all(widget) -> None:
    """Porta nella lingua in uso i testi di `widget` e di tutto cio' che contiene.

    Un widget conserva il testo ricevuto: se viene da tr() ha con se' la propria
    chiave e basta ritradurlo. Chi il testo lo compone (titoli in maiuscolo,
    suggerimenti) espone un metodo retranslate().
    """
    for option in ("text", "placeholder_text"):
        try:
            value = widget.cget(option)
        except (ValueError, AttributeError, KeyError, tk.TclError):
            continue  # il widget non ha questa opzione
        if isinstance(value, Text):
            widget.configure(**{option: again(value)})
    own = getattr(widget, "retranslate", None)
    if callable(own):
        own()
    for child in widget.winfo_children():
        retranslate_all(child)
    if widget is widget.winfo_toplevel():
        for tip in list(_tooltips):
            tip.retranslate()


class LanguageSwitch(ctk.CTkFrame):
    """Scelta della lingua: una sigla per lingua, evidenziata quella in uso."""

    def __init__(
        self, master, fonts: theme.Fonts, codes: list[str], current: str,
        on_change: Callable[[str], None],
    ) -> None:
        super().__init__(master, fg_color=theme.PANEL, corner_radius=4, border_width=1,
                         border_color=theme.BORDER)
        self._buttons: dict[str, ctk.CTkButton] = {}
        for column, code in enumerate(codes):
            item = ctk.CTkButton(
                self, text=code.upper(), width=44, height=26, corner_radius=3, font=fonts.caption,
                command=lambda c=code: on_change(c),
            )
            item.grid(row=0, column=column, padx=(3 if column == 0 else 0, 3), pady=3)
            self._buttons[code] = item
        self.select(current)

    def select(self, code: str) -> None:
        for key, item in self._buttons.items():
            if key == code:
                item.configure(fg_color=theme.ACCENT_BG, hover_color=theme.ACCENT_BG,
                               text_color=theme.ACCENT)
            else:
                item.configure(fg_color="transparent", hover_color=theme.HOVER,
                               text_color=theme.TEXT_DIM)
