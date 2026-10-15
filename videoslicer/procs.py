# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Avvio dei processi figli (ffmpeg) legati alla vita dell'applicazione.

Ogni processo viene messo in un Job Object di Windows con il limite
KILL_ON_JOB_CLOSE: quando il processo dell'app termina, in qualunque modo
(chiusura normale, eccezione, crash, kill forzato), il sistema chiude l'handle
del job e uccide tutti i processi dentro. In piu' si tiene l'elenco dei
processi vivi per chiuderli esplicitamente all'uscita (kill_all), anche su
sistemi senza Job Object.
"""

from __future__ import annotations

import atexit
import ctypes
import subprocess
import sys
import threading
import weakref

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JobObjectExtendedLimitInformation = 9

_live: weakref.WeakSet = weakref.WeakSet()
_lock = threading.Lock()
_job = None
_job_failed = False

if sys.platform == "win32":
    from ctypes import wintypes

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class _BASIC_LIMIT(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _EXTENDED_LIMIT(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BASIC_LIMIT),
            ("IoInfo", _IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    _kernel32 = ctypes.windll.kernel32
    _kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    _kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    _kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _kernel32.SetInformationJobObject.restype = wintypes.BOOL
    _kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _kernel32.AssignProcessToJobObject.restype = wintypes.BOOL


def _job_handle():
    """Il job dell'applicazione, creato alla prima richiesta; None se non disponibile."""
    global _job, _job_failed
    if sys.platform != "win32" or _job_failed:
        return None
    if _job is None:
        handle = _kernel32.CreateJobObjectW(None, None)
        if not handle:
            _job_failed = True
            return None
        info = _EXTENDED_LIMIT()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not _kernel32.SetInformationJobObject(handle, JobObjectExtendedLimitInformation,
                                                 ctypes.byref(info), ctypes.sizeof(info)):
            _job_failed = True
            return None
        _job = handle
    return _job


def popen(cmd: list[str], **kwargs) -> subprocess.Popen:
    """Come subprocess.Popen, ma il processo muore con l'applicazione."""
    kwargs.setdefault("stdin", subprocess.DEVNULL)
    kwargs.setdefault("creationflags", CREATE_NO_WINDOW)
    proc = subprocess.Popen(cmd, **kwargs)
    job = _job_handle()
    if job is not None:
        # Se fallisce (processo gia' in un job senza job annidati, Windows 7) resta
        # comunque l'elenco dei processi vivi chiuso da kill_all.
        _kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(int(proc._handle)))  # type: ignore[attr-defined]
    with _lock:
        _live.add(proc)
    return proc


def run(cmd: list[str], timeout: float | None = None) -> subprocess.CompletedProcess:
    """Come subprocess.run con stdout/stderr catturati; allo scadere del tempo il processo viene ucciso."""
    proc = popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


def kill_all() -> None:
    """Uccide i processi figli ancora vivi: alla chiusura dell'app e all'uscita dell'interprete."""
    with _lock:
        procs = list(_live)
    for proc in procs:
        try:
            if proc.poll() is None:
                proc.kill()
        except OSError:
            pass


atexit.register(kill_all)
