# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Esecuzione in background e consegna dei risultati al thread dell'interfaccia.

Nessuna chiamata a ffmpeg deve girare nel thread della GUI: anche la piu'
breve avvia un processo e si sente come uno scatto. I lavori vanno qui;
l'esito torna alla GUI attraverso una coda, svuotata a intervalli brevi.
"""

from __future__ import annotations

import queue
import threading
import time
import traceback
from typing import Any, Callable

ACTIVE_MS = 8     # intervallo di svuotamento mentre ci sono lavori in corso
IDLE_MS = 40      # a riposo
BUDGET_S = 0.012  # tempo massimo per giro, per non rubare fotogrammi alla GUI


class _Lane:
    """Coda servita da thread dedicati; con un solo thread i lavori restano in ordine."""

    def __init__(self, name: str, workers: int) -> None:
        self._jobs: queue.SimpleQueue = queue.SimpleQueue()
        for index in range(workers):
            threading.Thread(target=self._loop, name=f"vs-{name}-{index}", daemon=True).start()

    def submit(self, job: Callable[[], None]) -> None:
        self._jobs.put(job)

    def _loop(self) -> None:
        while True:
            self._jobs.get()()


class Tasks:
    def __init__(
        self,
        root,
        on_crash: Callable[[BaseException], None],
        on_bug: Callable[[str], None],
    ) -> None:
        self._root = root
        self._on_crash = on_crash  # lavoro fallito senza un gestore proprio
        self._on_bug = on_bug      # eccezione dentro una callback della GUI
        self._events: queue.SimpleQueue = queue.SimpleQueue()
        self._pool = _Lane("pool", 4)
        self._lanes: dict[str, _Lane] = {}
        self._pending = 0
        self._closed = False
        self._timer = root.after(IDLE_MS, self._drain)

    @property
    def busy(self) -> bool:
        return self._pending > 0

    def run(
        self,
        func: Callable[[], Any],
        on_ok: Callable[[Any], None] | None = None,
        on_error: Callable[[BaseException], None] | None = None,
        lane: str | None = None,
    ) -> None:
        """Esegue `func` in background; on_ok/on_error vengono chiamate nella GUI.

        Con `lane` i lavori dello stesso nome vengono eseguiti uno alla volta e
        nell'ordine di richiesta; senza, vanno al pool.
        """

        def job() -> None:
            try:
                result = func()
            except BaseException as exc:  # noqa: BLE001 - riportato all'utente
                self._events.put((on_error or self._on_crash, exc, True))
            else:
                self._events.put((on_ok, result, True))

        self._pending += 1
        if self._pending == 1 and not self._closed:
            self._root.after_cancel(self._timer)
            self._timer = self._root.after(ACTIVE_MS, self._drain)
        if lane is None:
            self._pool.submit(job)
            return
        target = self._lanes.get(lane)
        if target is None:
            target = self._lanes[lane] = _Lane(lane, 1)
        target.submit(job)

    def post(self, callback: Callable[..., None], *args: Any) -> None:
        """Consegna una chiamata alla GUI da un qualsiasi thread."""
        self._events.put((lambda _payload: callback(*args), None, False))

    def close(self) -> None:
        self._closed = True

    def _drain(self) -> None:
        if self._closed:
            return
        deadline = time.perf_counter() + BUDGET_S
        try:
            while True:
                callback, payload, finished = self._events.get_nowait()
                if finished:
                    self._pending -= 1
                if callback is not None:
                    try:
                        callback(payload)
                    except Exception:  # noqa: BLE001 - un errore non deve fermare la coda
                        self._on_bug(traceback.format_exc())
                if time.perf_counter() > deadline:
                    break
        except queue.Empty:
            pass
        waiting = self._pending > 0 or not self._events.empty()
        self._timer = self._root.after(ACTIVE_MS if waiting else IDLE_MS, self._drain)
