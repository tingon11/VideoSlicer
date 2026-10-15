# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Lingua dell'interfaccia: inglese (predefinita) oppure italiano.

Nel codice i testi sono in inglese e fanno da chiave; la traduzione italiana
sta in translations.py. tr() traduce nel momento in cui il testo serve: una
costante di modulo, valutata prima che la lingua sia nota, resta in inglese
(marcata con N_) e va passata a tr() quando si costruisce il widget.

La lingua si cambia a programma aperto. tr() restituisce una stringa che
ricorda la propria chiave (Text): again() la ritraduce, senza che chi l'ha
messa in un widget debba tenerne traccia.
"""

from __future__ import annotations

from .translations import IT

LANGUAGES = {"en": "English", "it": "Italiano"}
DEFAULT = "en"

_CATALOGS: dict[str, dict[str, str]] = {"en": {}, "it": IT}
_current = DEFAULT


class Text(str):
    """Testo tradotto: una normale stringa, che in piu' sa da quale chiave viene.

    format() conserva chiave e valori dei segnaposto, quindi si ritraduce anche
    un testo gia' composto. Maiuscole, concatenazioni e f-string danno invece
    una stringa semplice, che resta nella lingua in cui e' nata.
    """

    msgid: str
    args: tuple
    values: dict

    def __new__(cls, value: str, msgid: str, args: tuple = (), values: dict | None = None) -> Text:
        self = super().__new__(cls, value)
        self.msgid = msgid
        self.args = args
        self.values = values or {}
        return self

    def format(self, *args, **values) -> Text:
        return Text(super().format(*args, **values), self.msgid, args, values)


def set_language(code: object) -> str:
    """Sceglie la lingua; un codice sconosciuto riporta a quella predefinita."""
    global _current
    _current = code if code in LANGUAGES else DEFAULT
    return _current


def language() -> str:
    return _current


def tr(text: str) -> Text:
    """Testo nella lingua in uso; senza traduzione resta l'inglese."""
    key = text.msgid if isinstance(text, Text) else text
    return Text(_CATALOGS[_current].get(key, key), key)


def again(value):
    """Ritraduce nella lingua in uso un testo nato da tr(); ogni altro valore torna com'e'."""
    if not isinstance(value, Text):
        return value
    fresh = tr(value.msgid)
    if not value.args and not value.values:
        return fresh
    return fresh.format(
        *(again(item) for item in value.args),
        **{name: again(item) for name, item in value.values.items()},
    )


def N_(text: str) -> str:
    """Marca un testo che verra' tradotto piu' tardi con tr(): per le costanti di modulo."""
    return text
