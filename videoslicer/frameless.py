# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Finestra senza barra del titolo (solo Windows), stile Seity.

La barra viene rimossa intercettando WM_NCCALCSIZE sulla finestra di Tk: la
finestra resta NATIVA, quindi ridimensionamento dai bordi, Aero Snap, ombra,
animazioni, taskbar e Alt+Tab continuano a funzionare. Spostamento e
ridimensionamento dal bordo superiore vengono delegati al sistema con
WM_NCLBUTTONDOWN. Su altri sistemi le funzioni non fanno nulla e resta la
decorazione standard.

Per le finestre secondarie (dialoghi) non si toglie la barra: se ne colora
soltanto la cornice con DWM (Windows 11), cosi' si fondono con il tema.
"""

from __future__ import annotations

import ctypes
import sys

IS_WINDOWS = sys.platform.startswith("win")

WM_NCCALCSIZE = 0x0083
WM_NCLBUTTONDOWN = 0x00A1
GWLP_WNDPROC = -4
HTCAPTION = 2
HTTOP = 12
SM_CYSIZEFRAME = 33
SM_CXPADDEDBORDER = 92
SWP_FLAGS = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020  # NOSIZE|NOMOVE|NOZORDER|NOACTIVATE|FRAMECHANGED
DWMWA_BORDER_COLOR = 34
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36
RESIZE_BAND = 5  # px dal bordo superiore in cui si ridimensiona invece di spostare

_hooks: dict = {}  # hwnd -> (callback, vecchia wndproc): i riferimenti evitano il garbage collector

if IS_WINDOWS:
    from ctypes import wintypes

    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT,
                                 wintypes.WPARAM, wintypes.LPARAM)

    class NCCALCSIZE_PARAMS(ctypes.Structure):
        _fields_ = [("rgrc", wintypes.RECT * 3), ("lppos", ctypes.c_void_p)]

    user32 = ctypes.windll.user32
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
    user32.SetWindowLongPtrW.restype = ctypes.c_void_p
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_void_p
    user32.CallWindowProcW.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT,
                                       wintypes.WPARAM, wintypes.LPARAM]
    user32.CallWindowProcW.restype = LRESULT
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                                    wintypes.LPARAM]
    user32.IsZoomed.argtypes = [wintypes.HWND]
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int, wintypes.UINT]


def _hwnd(root):
    return user32.GetParent(root.winfo_id()) or root.winfo_id()


def _colorref(color: str):
    rgb = color.lstrip("#")
    return ctypes.c_uint(int(rgb[4:6] + rgb[2:4] + rgb[0:2], 16))  # COLORREF = 0x00BBGGRR


def _dwm_color(hwnd, attribute: int, color: str) -> None:
    try:
        ref = _colorref(color)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(ref),
                                                   ctypes.sizeof(ref))
    except (AttributeError, OSError):
        pass  # Windows 10 o precedenti: ignorato


def make_frameless(root, border_color: str | None = None) -> bool:
    """Rimuove la barra del titolo mantenendo la finestra nativa.

    Restituisce False se non applicabile: in quel caso resta la barra standard.
    """
    if not IS_WINDOWS:
        return False
    try:
        root.update_idletasks()
        hwnd = _hwnd(root)
        if hwnd in _hooks:
            # Windows riusa gli handle: si considera agganciata solo se la
            # procedura attiva e' davvero la nostra.
            current = user32.GetWindowLongPtrW(hwnd, GWLP_WNDPROC)
            if current == ctypes.cast(_hooks[hwnd][0], ctypes.c_void_p).value:
                return True
            del _hooks[hwnd]

        def wndproc(handle, msg, wparam, lparam):
            if msg == WM_NCCALCSIZE and wparam:
                params = NCCALCSIZE_PARAMS.from_address(lparam)
                top = params.rgrc[0].top
                result = user32.CallWindowProcW(old, handle, msg, wparam, lparam)
                if result == 0:
                    # il sistema calcola bordi laterali e inferiore (invisibili, per il
                    # resize); in alto niente barra
                    params.rgrc[0].top = top
                    if user32.IsZoomed(handle):
                        params.rgrc[0].top += (user32.GetSystemMetrics(SM_CYSIZEFRAME)
                                               + user32.GetSystemMetrics(SM_CXPADDEDBORDER))
                return result
            return user32.CallWindowProcW(old, handle, msg, wparam, lparam)

        callback = WNDPROC(wndproc)
        old = user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, ctypes.cast(callback, ctypes.c_void_p))
        if not old:
            return False
        _hooks[hwnd] = (callback, old)
        if border_color:
            _dwm_color(hwnd, DWMWA_BORDER_COLOR, border_color)
        user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, SWP_FLAGS)
        return True
    except Exception:  # noqa: BLE001 - qualunque intoppo: resta la barra standard
        return False


def enable_drag(root, widget) -> None:
    """Il widget si comporta come una barra del titolo.

    Trascina la finestra, doppio clic massimizza, il bordo alto ridimensiona.
    """
    if not IS_WINDOWS:
        return

    def at_top_edge(event) -> bool:
        return root.state() != "zoomed" and event.y_root - root.winfo_rooty() < RESIZE_BAND

    def on_motion(event) -> None:
        try:
            event.widget.configure(cursor="sb_v_double_arrow" if at_top_edge(event) else "")
        except Exception:  # noqa: BLE001 - widget senza cursore configurabile
            pass

    def on_press(event) -> None:
        hit = HTTOP if at_top_edge(event) else HTCAPTION
        point = ((event.y_root & 0xFFFF) << 16) | (event.x_root & 0xFFFF)
        user32.ReleaseCapture()
        # PostMessage, non SendMessage: il ciclo modale di spostamento deve partire dal
        # mainloop di Tk. Avviato dentro questa callback, Tk rientrerebbe in Python
        # senza stato del thread e l'app andrebbe in crash.
        user32.PostMessageW(_hwnd(root), WM_NCLBUTTONDOWN, hit, point)

    def on_double(event) -> None:
        if not at_top_edge(event):
            toggle_maximize(root)

    widget.bind("<Motion>", on_motion, add=True)
    widget.bind("<ButtonPress-1>", on_press, add=True)
    widget.bind("<Double-Button-1>", on_double, add=True)


def toggle_maximize(root) -> None:
    root.state("normal" if root.state() == "zoomed" else "zoomed")


def style_titlebar(window, caption: str, text: str, border: str) -> None:
    """Colora barra, testo e bordo di una finestra con cornice (Windows 11)."""
    if not IS_WINDOWS:
        return
    try:
        hwnd = _hwnd(window)
    except Exception:  # noqa: BLE001 - finestra gia' distrutta
        return
    _dwm_color(hwnd, DWMWA_CAPTION_COLOR, caption)
    _dwm_color(hwnd, DWMWA_TEXT_COLOR, text)
    _dwm_color(hwnd, DWMWA_BORDER_COLOR, border)
