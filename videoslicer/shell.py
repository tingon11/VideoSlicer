# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Barra di navigazione laterale (stile Seity / AndrOsint) tra le pagine dell'applicazione."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

import customtkinter as ctk

from . import theme
from .i18n import again, tr

GLYPH_MENU = ""


class NavRail(ctk.CTkFrame):
    """Voci di navigazione verticali, in una barra che si comprime sulle finestre strette.

    `items` e' una lista di (chiave, etichetta, glifo). Compressa, la barra
    mostra solo le icone e il nome compare accanto al passaggio del mouse.
    """

    OPEN = 212
    CLOSED = 58

    def __init__(
        self,
        master,
        fonts: theme.Fonts,
        items: list[tuple[str, str, str]],
        on_select: Callable[[str], None],
        title: str = "",
    ) -> None:
        super().__init__(master, fg_color=theme.PANEL, corner_radius=0, width=self.OPEN)
        self._fonts = fonts
        self._on_select = on_select
        self._rows: dict[str, dict] = {}
        self._labels = {key: label for key, label, _glyph in items}
        self._current = ""
        self._has_icons = bool(theme.icon_font())
        self._tip: ctk.CTkToplevel | None = None
        self.collapsed = False
        self.user_choice: bool | None = None  # None = automatico, True/False = scelto a mano

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._title = ctk.CTkLabel(self, text=title or tr("PAGES"), anchor="w", font=fonts.caption,
                                   text_color=theme.TEXT_FAINT)
        self._title.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))

        self._list = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._list.grid(row=1, column=0, sticky="nsew")
        self._list.grid_columnconfigure(0, weight=1)
        for index, (key, label, glyph) in enumerate(items):
            self._add_row(index, key, label, glyph)

        ctk.CTkButton(
            self, text=GLYPH_MENU if self._has_icons else "≡", width=34, height=30,
            corner_radius=4, fg_color="transparent", hover_color=theme.HOVER,
            text_color=theme.TEXT_DIM, font=fonts.icon(13), command=self._toggle,
        ).grid(row=2, column=0, sticky="w", padx=12, pady=12)

    # ------------------------------------------------------------------ voci

    def _add_row(self, index: int, key: str, label: str, glyph: str) -> None:
        row = ctk.CTkFrame(self._list, fg_color="transparent", corner_radius=4, height=38)
        row.grid(row=index, column=0, sticky="ew", padx=8, pady=1)
        row.grid_propagate(False)
        row.grid_columnconfigure(2, weight=1)
        row.grid_rowconfigure(0, weight=1)
        bar = ctk.CTkFrame(row, fg_color="transparent", width=3, corner_radius=2)
        bar.grid(row=0, column=0, sticky="ns", pady=8)
        icon = ctk.CTkLabel(
            row, text=glyph if self._has_icons else label[:2].upper(), width=36,
            font=self._fonts.icon(15) if self._has_icons else self._fonts.caption,
            text_color=theme.TEXT_DIM,
        )
        icon.grid(row=0, column=1, padx=(6, 2))
        text = ctk.CTkLabel(row, text=label, anchor="w", font=self._fonts.body,
                            text_color=theme.TEXT_DIM)
        text.grid(row=0, column=2, sticky="ew", padx=(4, 8))
        self._rows[key] = {"row": row, "bar": bar, "icon": icon, "label": text, "hover": False}
        for widget in (row, icon, text):
            widget.bind("<Button-1>", lambda _e, k=key: self._on_select(k))
            widget.bind("<Enter>", lambda _e, k=key: self._hover(k, True))
            widget.bind("<Leave>", lambda _e, k=key: self._hover(k, False))
            widget.configure(cursor="hand2")

    def select(self, key: str) -> None:
        """Evidenzia la voce della pagina corrente."""
        previous, self._current = self._current, key
        self._hide_tip()
        if previous in self._rows:
            self._paint(previous)
        self._paint(key)

    def retranslate(self) -> None:
        """I nomi mostrati accanto alle icone, a barra compressa, seguono la lingua."""
        self._labels = {key: again(label) for key, label in self._labels.items()}

    def _hover(self, key: str, on: bool) -> None:
        item = self._rows[key]
        item["hover"] = on
        self._paint(key)
        if on and self.collapsed:
            self._show_tip(key, item["row"])
        else:
            self._hide_tip()

    def _paint(self, key: str) -> None:
        item = self._rows[key]
        if key == self._current:
            item["row"].configure(fg_color=theme.ACCENT_BG)
            item["bar"].configure(fg_color=theme.ACCENT)
            item["icon"].configure(text_color=theme.ACCENT)
            item["label"].configure(text_color=theme.TEXT, font=self._fonts.bold)
        else:
            soft = theme.TEXT_SOFT if item["hover"] else theme.TEXT_DIM
            item["row"].configure(fg_color=theme.HOVER if item["hover"] else "transparent")
            item["bar"].configure(fg_color="transparent")
            item["icon"].configure(text_color=soft)
            item["label"].configure(text_color=soft, font=self._fonts.body)

    def _show_tip(self, key: str, anchor) -> None:
        self._hide_tip()
        try:
            tip = ctk.CTkToplevel(self)
            tip.overrideredirect(True)
            tip.attributes("-topmost", True)
            tip.configure(fg_color=theme.BORDER)
            ctk.CTkLabel(
                tip, text=f"  {self._labels[key]}  ", font=self._fonts.bold, text_color=theme.TEXT,
                fg_color=theme.PANEL_2, corner_radius=0, height=26,
            ).pack(padx=1, pady=1)
            x = anchor.winfo_rootx() + anchor.winfo_width() + 8
            y = anchor.winfo_rooty() + (anchor.winfo_height() - 28) // 2
            tip.geometry(f"+{x}+{y}")
            self._tip = tip
        except tk.TclError:
            self._tip = None

    def _hide_tip(self) -> None:
        tip, self._tip = self._tip, None
        if tip is not None:
            try:
                tip.destroy()
            except tk.TclError:
                pass

    # ---------------------------------------------------------- compressione

    def _toggle(self) -> None:
        self.user_choice = not self.collapsed
        self.set_collapsed(self.user_choice)

    def set_collapsed(self, collapsed: bool) -> None:
        if collapsed == self.collapsed:
            return
        self.collapsed = collapsed
        self.configure(width=self.CLOSED if collapsed else self.OPEN)
        for item in self._rows.values():
            if collapsed:
                item["label"].grid_remove()
            else:
                item["label"].grid()
        if collapsed:
            self._title.grid_remove()
        else:
            self._title.grid()
