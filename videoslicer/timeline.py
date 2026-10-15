# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Timeline del video: righello, pellicola di anteprime, segnaposto di inizio e fine.

Si ingrandisce con Ctrl+rotellina (o i pulsanti) fino al singolo fotogramma e
si scorre con la rotellina o trascinando la finestra nella barra in basso. I
segnaposto IN e OUT e il cursore si trascinano col mouse. I tempi interni sono
sempre numeri di fotogramma: niente derive di arrotondamento.
"""

from __future__ import annotations

import math
import threading
import tkinter as tk
from collections import OrderedDict
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageTk

from . import theme
from .ffmpeg import VideoInfo, grab, grab_run
from .i18n import tr

TICK_STEPS = (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 30,
              60, 120, 300, 600, 900, 1800, 3600, 7200)


def format_time(seconds: float, ms: bool = True, hours: bool | None = None) -> str:
    """hh:mm:ss.mmm (le ore solo se servono o se richieste)."""
    seconds = max(0.0, seconds)
    total_ms = int(round(seconds * 1000))
    h, rest = divmod(total_ms, 3_600_000)
    m, rest = divmod(rest, 60_000)
    s, milli = divmod(rest, 1000)
    text = f"{m:02d}:{s:02d}"
    if hours or (hours is None and h):
        text = f"{h:d}:{text}"
    if ms:
        text += f".{milli:03d}"
    return text


def parse_time(text: str, fps: float) -> int | None:
    """Da "1:02:03.456", "62.5", "f1234" (fotogramma) al numero di fotogramma; None se illeggibile."""
    text = text.strip().lower().replace(",", ".")
    if not text:
        return None
    if text.startswith("f") or text.startswith("#"):
        try:
            return max(0, int(text[1:]))
        except ValueError:
            return None
    parts = text.split(":")
    if len(parts) > 3:
        return None
    try:
        values = [float(p) if p else 0.0 for p in parts]
    except ValueError:
        return None
    seconds = 0.0
    for value in values:
        seconds = seconds * 60 + value
    return max(0, int(round(seconds * fps)))


class Thumbnails:
    """Anteprime della pellicola, generate in background con ffmpeg.

    `want()` sostituisce ogni volta l'elenco delle anteprime desiderate: i
    thread servono prima quelle vicine al centro della vista e lasciano
    perdere quelle che nel frattempo sono uscite di scena.
    """

    WORKERS = 3
    CACHE_MAX = 1200
    RUN_GAP = 4      # fotogrammi non richiesti tollerati dentro un lotto
    RUN_MAX = 32     # fotogrammi per lotto

    def __init__(self, post: Callable[[Callable[[], None]], None]) -> None:
        self._post = post
        self._cond = threading.Condition()
        self._wanted: dict[int, float] = {}
        self._pending: set[int] = set()   # in lavorazione: non vanno richieste di nuovo
        self._cache: OrderedDict[int, Image.Image] = OrderedDict()
        self._failed: set[int] = set()
        self._center = 0
        self._accurate = True
        self._video: VideoInfo | None = None
        self._height = 64
        self._generation = 0
        self.on_ready: Callable[[], None] | None = None
        for index in range(self.WORKERS):
            threading.Thread(target=self._loop, name=f"vs-thumb-{index}", daemon=True).start()

    def set_video(self, info: VideoInfo | None, height: int) -> None:
        with self._cond:
            self._video = info
            self._height = height
            self._wanted.clear()
            self._pending.clear()
            self._cache.clear()
            self._failed.clear()
            self._generation += 1

    def get(self, frame: int) -> Image.Image | None:
        with self._cond:
            image = self._cache.get(frame)
            if image is not None:
                self._cache.move_to_end(frame)
            return image

    def want(self, frames: dict[int, float], center: int, accurate: bool) -> None:
        with self._cond:
            self._wanted = {f: t for f, t in frames.items()
                            if f not in self._cache and f not in self._failed and f not in self._pending}
            self._center = center
            self._accurate = accurate
            self._cond.notify_all()

    def _loop(self) -> None:
        while True:
            with self._cond:
                while not self._wanted:
                    self._cond.wait()
                frame = min(self._wanted, key=lambda f: abs(f - self._center))
                video, height, accurate, generation = (
                    self._video, self._height, self._accurate, self._generation)
                # Lotto: i fotogrammi voluti vicini a `frame` si decodificano in un passaggio
                # solo (una sola decodifica dal keyframe invece di una per miniatura).
                run = [frame]
                if accurate:
                    ordered = sorted(self._wanted)
                    lo = hi = ordered.index(frame)
                    while (lo > 0 and ordered[lo - 1] >= ordered[lo] - self.RUN_GAP
                           and ordered[hi] - ordered[lo - 1] < self.RUN_MAX):
                        lo -= 1
                    while (hi < len(ordered) - 1 and ordered[hi + 1] <= ordered[hi] + self.RUN_GAP
                           and ordered[hi + 1] - ordered[lo] < self.RUN_MAX):
                        hi += 1
                    run = ordered[lo:hi + 1]
                times = {f: self._wanted.pop(f) for f in run}
                self._pending.update(run)
            if video is None:
                continue
            results: dict[int, Image.Image] = {}
            try:
                if len(run) > 1:
                    first = run[0]
                    images = grab_run(video, first, run[-1] - first + 1, height=height)
                    results = {first + index: image for index, image in enumerate(images)}
                else:
                    results = {frame: grab(video.path, times[frame], height=height, accurate=accurate)}
            except Exception:  # noqa: BLE001 - le anteprime restano vuote
                results = {}
            with self._cond:
                self._pending.difference_update(run)
                if generation != self._generation:
                    continue
                for f in run:
                    if f not in results:
                        self._failed.add(f)
                # anche i fotogrammi intermedi del lotto: sono gia' decodificati, costano 30 KB l'uno
                for f, image in results.items():
                    self._cache[f] = image
                while len(self._cache) > self.CACHE_MAX:
                    self._cache.popitem(last=False)
            self._post(self._notify)

    def _notify(self) -> None:
        if self.on_ready is not None:
            self.on_ready()


class Timeline(ctk.CTkFrame):
    """Righello + pellicola + barra di panoramica, disegnati su un Canvas."""

    HIT = 8  # px di tolleranza per afferrare un segnaposto

    def __init__(
        self,
        master,
        fonts: theme.Fonts,
        thumbs: Thumbnails,
        on_playhead: Callable[[int], None],
        on_range: Callable[[int, int], None],
        on_view: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, fg_color=theme.PANEL, corner_radius=4, border_width=1,
                         border_color=theme.BORDER)
        self._fonts = fonts
        self._thumbs = thumbs
        self._on_playhead = on_playhead
        self._on_range = on_range
        self._on_view = on_view
        thumbs.on_ready = self._schedule

        s = theme.scaling(self)
        self._s = s
        self.RULER = int(26 * s)
        self.STRIP = int(72 * s)
        self.GAP = int(8 * s)
        self.OVER = int(12 * s)
        height = self.RULER + self.STRIP + self.GAP + self.OVER + int(8 * s)
        self._label_font = (theme.mono_font(), 8)
        self._flag_font = (theme.mono_font(), 8, "bold")

        self.canvas = tk.Canvas(self, height=height, bg=theme.PANEL, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True, padx=1, pady=1)

        self.info: VideoInfo | None = None
        self.fps = 25.0
        self.frames = 1
        self.duration = 0.0
        self.v0 = 0.0
        self.v1 = 1.0
        self.in_f = 0
        self.out_f = 0
        self.play_f = 0
        self._drag: str | None = None
        self._drag_offset = 0.0
        self._photos: dict[int, ImageTk.PhotoImage] = {}
        self._job: str | None = None
        self._play_items: dict[str, int] = {}   # elementi del cursore, spostati senza ridisegnare tutto
        self.hover_frame: int | None = None

        c = self.canvas
        c.bind("<Configure>", lambda _e: self._schedule())
        c.bind("<ButtonPress-1>", self._press)
        c.bind("<B1-Motion>", self._motion)
        c.bind("<ButtonRelease-1>", self._release)
        c.bind("<Motion>", self._hover)
        c.bind("<Leave>", self._leave)
        c.bind("<MouseWheel>", self._wheel)
        c.bind("<Shift-MouseWheel>", self._wheel)
        c.bind("<Control-MouseWheel>", self._wheel)
        c.bind("<Double-Button-1>", self._double)
        self._schedule()

    # ---------------------------------------------------------------- stato

    def set_video(self, info: VideoInfo | None) -> None:
        self.info = info
        self._photos.clear()
        if info is None:
            self.fps, self.frames, self.duration = 25.0, 1, 0.0
            self.v0, self.v1 = 0.0, 1.0
            self.in_f = self.out_f = self.play_f = 0
            self._thumbs.set_video(None, self.STRIP)
        else:
            self.fps = info.fps
            self.frames = info.frames
            self.duration = self.frames / self.fps
            self.v0, self.v1 = 0.0, self.duration
            self.in_f, self.out_f, self.play_f = 0, self.frames - 1, 0
            self._thumbs.set_video(info, self.STRIP)
        self._schedule()

    @property
    def span(self) -> float:
        return max(1e-6, self.v1 - self.v0)

    @property
    def min_span(self) -> float:
        return max(6 / self.fps, 0.02)

    def _clamp_frame(self, frame: int) -> int:
        return max(0, min(self.frames - 1, int(frame)))

    def set_playhead(self, frame: int, notify: bool = True, reveal: bool = True) -> None:
        frame = self._clamp_frame(frame)
        changed = frame != self.play_f
        self.play_f = frame
        view = (self.v0, self.v1)
        if reveal:
            self.reveal(frame / self.fps)
        if (self.v0, self.v1) != view or self._job is not None or not self._play_items:
            self._schedule()
        else:
            self._move_playhead()  # solo il cursore: niente ridisegno di miniature e righello
        if notify and changed:
            self._on_playhead(frame)

    def set_in(self, frame: int, notify: bool = True) -> None:
        frame = self._clamp_frame(frame)
        self.in_f = frame
        if self.out_f < frame:
            self.out_f = frame
        self._schedule()
        if notify:
            self._on_range(self.in_f, self.out_f)

    def set_out(self, frame: int, notify: bool = True) -> None:
        frame = self._clamp_frame(frame)
        self.out_f = frame
        if self.in_f > frame:
            self.in_f = frame
        self._schedule()
        if notify:
            self._on_range(self.in_f, self.out_f)

    def step(self, frames: int) -> None:
        self.set_playhead(self.play_f + frames)

    # ----------------------------------------------------------------- vista

    def zoom(self, factor: float, anchor: float | None = None) -> None:
        """factor > 1 ingrandisce; `anchor` (secondi) resta fermo sullo schermo."""
        if self.info is None:
            return
        span = self.span
        new = max(self.min_span, min(self.duration, span / factor))
        if anchor is None:
            anchor = self.play_f / self.fps
            if not (self.v0 <= anchor <= self.v1):
                anchor = (self.v0 + self.v1) / 2
        ratio = (anchor - self.v0) / span
        self._set_view(anchor - ratio * new, new)

    def zoom_fit(self) -> None:
        self._set_view(0.0, self.duration)

    def zoom_selection(self) -> None:
        if self.info is None:
            return
        start = self.in_f / self.fps
        length = (self.out_f + 1 - self.in_f) / self.fps
        margin = length * 0.08
        self._set_view(start - margin, max(self.min_span, length + 2 * margin))

    def pan(self, dt: float) -> None:
        self._set_view(self.v0 + dt, self.span)

    def reveal(self, t: float) -> None:
        """Scorre il minimo necessario perche' l'istante `t` sia visibile."""
        if t < self.v0:
            self._set_view(t - self.span * 0.1, self.span)
        elif t > self.v1:
            self._set_view(t - self.span * 0.9, self.span)

    def _set_view(self, v0: float, span: float) -> None:
        span = max(self.min_span, min(self.duration, span)) if self.duration else span
        v0 = max(0.0, min(v0, self.duration - span))
        if abs(v0 - self.v0) < 1e-9 and abs(span - self.span) < 1e-9:
            return
        self.v0, self.v1 = v0, v0 + span
        self._schedule()
        if self._on_view is not None:
            self._on_view()

    # ------------------------------------------------------------ coordinate

    def _width(self) -> int:
        return max(1, self.canvas.winfo_width())

    def x_of(self, t: float) -> float:
        return (t - self.v0) / self.span * self._width()

    def t_of(self, x: float) -> float:
        return self.v0 + x / self._width() * self.span

    def frame_at(self, x: float) -> int:
        return self._clamp_frame(math.floor(self.t_of(x) * self.fps + 1e-6))

    # ----------------------------------------------------------------- eventi

    def _zone(self, y: float) -> str:
        if y < self.RULER:
            return "ruler"
        if y < self.RULER + self.STRIP:
            return "strip"
        if y >= self.RULER + self.STRIP + self.GAP:
            return "overview"
        return "gap"

    def _marker_x(self) -> tuple[float, float]:
        return self.x_of(self.in_f / self.fps), self.x_of((self.out_f + 1) / self.fps)

    def _hit_marker(self, x: float, y: float) -> str | None:
        if self.info is None or self._zone(y) == "overview":
            return None
        xi, xo = self._marker_x()
        hit = self.HIT * self._s
        near_in, near_out = abs(x - xi) <= hit, abs(x - xo) <= hit
        if near_in and near_out:
            return "in" if x < (xi + xo) / 2 else "out"
        if near_in:
            return "in"
        if near_out:
            return "out"
        return None

    def _press(self, event) -> None:
        if self.info is None:
            return
        self.canvas.focus_set()
        zone = self._zone(event.y)
        if zone == "overview":
            w = self._width()
            vx0, vx1 = self.v0 / self.duration * w, self.v1 / self.duration * w
            if vx0 <= event.x <= vx1:
                self._drag = "view"
                self._drag_offset = event.x / w * self.duration - self.v0
            else:
                self._drag = "view"
                self._drag_offset = self.span / 2
                self._set_view(event.x / w * self.duration - self.span / 2, self.span)
            return
        marker = self._hit_marker(event.x, event.y)
        if marker is not None:
            self._drag = marker
            return
        self._drag = "play"
        self.set_playhead(self.frame_at(event.x), reveal=False)

    def _motion(self, event) -> None:
        if self.info is None or self._drag is None:
            return
        if self._drag == "view":
            self._set_view(event.x / self._width() * self.duration - self._drag_offset, self.span)
        elif self._drag == "play":
            self.set_playhead(self.frame_at(event.x), reveal=False)
        elif self._drag == "in":
            self.set_in(min(self.frame_at(event.x), self.out_f))
        elif self._drag == "out":
            # il segnaposto di fine sta alla FINE del fotogramma: x corrisponde a out+1
            frame = self._clamp_frame(int(round(self.t_of(event.x) * self.fps)) - 1)
            self.set_out(max(frame, self.in_f))

    def _release(self, _event) -> None:
        self._drag = None

    def _double(self, event) -> None:
        if self.info is None:
            return
        if self._zone(event.y) == "ruler":
            self.zoom_fit()

    def _hover(self, event) -> None:
        if self.info is None:
            return
        marker = self._hit_marker(event.x, event.y)
        zone = self._zone(event.y)
        if marker is not None:
            cursor = "sb_h_double_arrow"
        elif zone == "overview":
            cursor = "hand2"
        else:
            cursor = "crosshair"
        if self.canvas.cget("cursor") != cursor:
            self.canvas.configure(cursor=cursor)
        self.hover_frame = self.frame_at(event.x) if zone in ("ruler", "strip") else None

    def _leave(self, _event) -> None:
        self.hover_frame = None

    def _wheel(self, event) -> None:
        if self.info is None:
            return
        ticks = event.delta / 120 if event.delta else 0
        if not ticks:
            return
        if event.state & 0x0004:  # Ctrl
            self.zoom(1.3 ** ticks, anchor=self.t_of(event.x))
        else:
            self.pan(-ticks * self.span * 0.12)

    # ---------------------------------------------------------------- disegno

    def _schedule(self) -> None:
        if self._job is None:
            self._job = self.after_idle(self._paint)

    def _playhead_coords(self) -> tuple[float, float, float, float]:
        """x del cursore, x della fine del suo fotogramma, x nella panoramica e larghezza."""
        w = self._width()
        xp = self.x_of(self.play_f / self.fps)
        xp1 = self.x_of((self.play_f + 1) / self.fps)
        px = self.play_f / self.fps / self.duration * w if self.duration else 0.0
        return xp, xp1, px, w

    def _move_playhead(self) -> None:
        c, s, items = self.canvas, self._s, self._play_items
        xp, xp1, px, _w = self._playhead_coords()
        y_strip0, y_strip1 = self.RULER, self.RULER + self.STRIP
        y_over0 = y_strip1 + self.GAP
        c.coords(items["box"], xp, y_strip0, xp1, y_strip1)
        c.itemconfigure(items["box"], state="normal" if xp1 - xp >= 6 else "hidden")
        c.coords(items["line"], xp, 0, xp, y_strip1)
        c.coords(items["head"], xp - 6 * s, 0, xp + 6 * s, 0, xp, 8 * s)
        c.coords(items["over"], px, y_over0 - 2, px, y_over0 + self.OVER + 2)

    def _tick_steps(self) -> tuple[float, float]:
        """Passo delle tacche con etichetta e di quelle minori, in secondi."""
        pps = self._width() / self.span  # pixel per secondo
        frame_dt = 1 / self.fps
        minimum = 76 * self._s
        if pps * frame_dt * 10 >= minimum:
            # zoom a livello di fotogramma: tacche su multipli di fotogrammi
            for n in (1, 2, 5, 10, 20, 50, 100):
                if pps * frame_dt * n >= minimum:
                    minor = frame_dt if n > 1 else frame_dt
                    return frame_dt * n, minor
        for step in TICK_STEPS:
            if step * pps >= minimum:
                minor = step / 3 if step in (15, 30, 900, 1800) else step / 5
                return step, minor
        return TICK_STEPS[-1], TICK_STEPS[-1] / 5

    def _paint(self) -> None:
        self._job = None
        c = self.canvas
        c.delete("all")
        w = self._width()
        y_strip0 = self.RULER
        y_strip1 = self.RULER + self.STRIP
        y_over0 = y_strip1 + self.GAP
        y_over1 = y_over0 + self.OVER
        s = self._s

        c.create_rectangle(0, y_strip0, w, y_strip1, fill=theme.PANEL_2, outline="")
        self._play_items = {}
        if self.info is None:
            c.create_text(w / 2, y_strip0 + self.STRIP / 2, text=tr("Open a video to see the timeline"),
                          fill=theme.TEXT_FAINT, font=(theme.ui_font(), 11))
            c.create_rectangle(0, y_over0, w, y_over1, fill=theme.PANEL_3, outline="")
            return

        self._paint_thumbs(y_strip0, y_strip1)

        xi, xo = self._marker_x()
        # fuori dalla selezione la pellicola si attenua
        if xi > 0:
            c.create_rectangle(0, y_strip0, max(0, xi), y_strip1, fill=theme.BG,
                               stipple="gray50", outline="")
        if xo < w:
            c.create_rectangle(min(w, xo), y_strip0, w, y_strip1, fill=theme.BG,
                               stipple="gray50", outline="")

        # righello
        c.create_rectangle(0, 0, w, self.RULER, fill=theme.PANEL, outline="")
        c.create_rectangle(xi, 0, xo, self.RULER, fill=theme.ACCENT_BG, outline="")
        major, minor = self._tick_steps()
        show_hours = self.duration >= 3600
        show_ms = major < 1
        t = math.floor(self.v0 / minor) * minor
        while t <= self.v1 + minor:
            x = self.x_of(t)
            if 0 <= x <= w:
                is_major = abs(t / major - round(t / major)) < 1e-6
                if is_major:
                    c.create_line(x, self.RULER - 10 * s, x, self.RULER, fill=theme.TEXT_DIM)
                    label = format_time(t, ms=show_ms, hours=show_hours)
                    if major < 1 / self.fps * 1.5 or (major <= 1 / self.fps * 100 and show_ms):
                        label += f"  f{int(round(t * self.fps))}"
                    c.create_text(x + 3 * s, 3 * s, text=label, anchor="nw",
                                  fill=theme.TEXT_DIM, font=self._label_font)
                else:
                    c.create_line(x, self.RULER - 5 * s, x, self.RULER, fill=theme.BORDER_STRONG)
            t += minor
        c.create_line(0, self.RULER - 1, w, self.RULER - 1, fill=theme.BORDER)

        # segnaposto IN e OUT: linea per tutta l'altezza e bandierina nel righello
        flag_w, flag_h = 14 * s, self.RULER - 2
        c.create_line(xi, 0, xi, y_strip1, fill=theme.MARK_IN, width=2)
        c.create_polygon(xi, 0, xi + flag_w, 0, xi + flag_w, flag_h * 0.75, xi, flag_h,
                         fill=theme.MARK_IN, outline="")
        c.create_text(xi + flag_w / 2 - 1, flag_h * 0.42, text="I", fill=theme.BG, font=self._flag_font)
        c.create_line(xo, 0, xo, y_strip1, fill=theme.MARK_OUT, width=2)
        c.create_polygon(xo, 0, xo - flag_w, 0, xo - flag_w, flag_h * 0.75, xo, flag_h,
                         fill=theme.MARK_OUT, outline="")
        c.create_text(xo - flag_w / 2 + 1, flag_h * 0.42, text="O", fill=theme.BG, font=self._flag_font)

        # cursore (gli elementi restano identificati: set_playhead li sposta senza ridisegnare)
        xp, xp1, px, _w = self._playhead_coords()
        self._play_items = {
            "box": c.create_rectangle(xp, y_strip0, xp1, y_strip1, outline=theme.ACCENT, width=2,
                                      state="normal" if xp1 - xp >= 6 else "hidden"),
            "line": c.create_line(xp, 0, xp, y_strip1, fill=theme.ACCENT, width=2),
            "head": c.create_polygon(xp - 6 * s, 0, xp + 6 * s, 0, xp, 8 * s, fill=theme.ACCENT, outline=""),
        }

        # panoramica: tutto il video, con selezione e finestra visibile
        c.create_rectangle(0, y_over0, w, y_over1, fill=theme.PANEL_3, outline="")
        ox0 = self.in_f / self.fps / self.duration * w
        ox1 = (self.out_f + 1) / self.fps / self.duration * w
        c.create_rectangle(ox0, y_over0, ox1, y_over1, fill=theme.ACCENT_DIM, outline="")
        vx0, vx1 = self.v0 / self.duration * w, self.v1 / self.duration * w
        c.create_rectangle(vx0, y_over0, max(vx0 + 2, vx1), y_over1, fill=theme.TEXT_FAINT,
                           stipple="gray25", outline=theme.TEXT_SOFT)
        self._play_items["over"] = c.create_line(px, y_over0 - 2, px, y_over1 + 2, fill=theme.ACCENT, width=2)

    def _paint_thumbs(self, y0: int, y1: int) -> None:
        assert self.info is not None
        c = self.canvas
        w = self._width()
        aspect = self.info.width / max(1, self.info.height)
        tw = max(16, int(round(self.STRIP * aspect)))
        pps = w / self.span
        frame_dt = 1 / self.fps
        slot_dt = tw / pps
        frame_level = slot_dt < frame_dt
        if frame_level:
            slot_dt = frame_dt
        wanted: dict[int, float] = {}
        k0, k1 = int(math.floor(self.v0 / slot_dt)), int(math.floor(self.v1 / slot_dt))
        for k in range(k0, k1 + 1):
            t = k * slot_dt
            if frame_level:
                frame = int(round(t * self.fps))
            else:
                frame = int(math.floor(t * self.fps + 1e-6))
            if frame < 0 or frame >= self.frames:
                continue
            x0, x1 = self.x_of(t), self.x_of(t + slot_dt)
            image = self._thumbs.get(frame)
            if image is None:
                wanted[frame] = frame / self.fps if frame_level else t
                c.create_rectangle(x0, y0, x1, y1, fill=theme.PANEL_3, outline=theme.BORDER)
                continue
            photo = self._photo(frame, image)
            if frame_level:
                c.create_image((x0 + x1) / 2, y0, anchor="n", image=photo)
                c.create_line(x0, y0, x0, y1, fill=theme.BORDER)
            else:
                c.create_image(x0, y0, anchor="nw", image=photo)
        center = self.play_f if self.v0 <= self.play_f / self.fps <= self.v1 else int(
            (self.v0 + self.v1) / 2 * self.fps)
        self._thumbs.want(wanted, center, accurate=slot_dt < 2.0)

    def _photo(self, frame: int, image: Image.Image) -> ImageTk.PhotoImage:
        photo = self._photos.get(frame)
        if photo is None:
            photo = self._photos[frame] = ImageTk.PhotoImage(image)
            if len(self._photos) > 400:
                for key in list(self._photos)[:100]:
                    del self._photos[key]
        return photo
