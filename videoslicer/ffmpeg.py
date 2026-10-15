# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Tutto cio' che passa da ffmpeg: informazioni sul video, anteprime, estrazione.

ffmpeg viene cercato nel PATH; se manca si usa il binario portato dal pacchetto
Python imageio-ffmpeg. L'estrazione e' senza perdita: i fotogrammi decodificati
vengono scritti in PNG, TIFF o BMP (formati non compressi o a compressione
lossless), a 8 o 16 bit per canale secondo la profondita' della sorgente.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image

from . import procs
from .i18n import tr

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

# formato -> (estensione, codec, pix_fmt 8 bit, pix_fmt 8 bit con alfa, pix_fmt 16 bit, 16 bit con alfa)
FORMATS: dict[str, tuple[str, str, str, str, str | None, str | None]] = {
    "PNG": ("png", "png", "rgb24", "rgba", "rgb48be", "rgba64be"),
    "TIFF": ("tiff", "tiff", "rgb24", "rgba", "rgb48le", "rgba64le"),
    "BMP": ("bmp", "bmp", "bgr24", "bgra", None, None),
}
DEPTHS = ("Auto", "8 bit", "16 bit")

VIDEO_EXTENSIONS = (
    "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.mts *.m2ts *.ts *.wmv *.flv *.3gp *.mpg *.mpeg *.mxf *.y4m"
)


class FFmpegError(RuntimeError):
    """ffmpeg assente o fallito."""


class Cancelled(Exception):
    """Estrazione interrotta dall'utente."""


_exe: str | None = None
_lock = threading.Lock()


def ffmpeg_exe() -> str:
    """Percorso di ffmpeg: tools/ffmpeg/, PATH o pacchetto imageio-ffmpeg (vedi tools.find)."""
    global _exe
    with _lock:
        if _exe:
            return _exe
        from . import tools  # import tardivo: tools importa questo modulo? no, ma evita cicli futuri

        found, _source = tools.find()
        if found is None:
            raise FFmpegError(tr(
                "ffmpeg not found. Download it from the FFmpeg box of the Configuration page, "
                "or install it and put it in the PATH."
            ))
        _exe = str(found)
        return _exe


def reset() -> None:
    """Dimentica il percorso trovato: dopo un download o un aggiornamento."""
    global _exe
    with _lock:
        _exe = None


def version() -> str:
    """Prima riga di `ffmpeg -version`, ripulita."""
    out = _run([ffmpeg_exe(), "-version"]).stdout.decode("utf-8", "replace")
    first = out.splitlines()[0] if out else "ffmpeg"
    match = re.search(r"ffmpeg version (\S+)", first)
    return f"ffmpeg {match.group(1)}" if match else first.strip()


def _run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    result = procs.run(cmd)  # legato alla vita dell'app: muore con lei
    if check and result.returncode != 0:
        raise FFmpegError(result.stderr.decode("utf-8", "replace").strip() or tr("ffmpeg: exit code {code}").format(code=result.returncode))
    return result


# ------------------------------------------------------------ informazioni

@dataclass
class VideoInfo:
    path: Path
    duration: float      # secondi
    fps: float
    width: int           # dimensioni come vengono mostrate (rotazione applicata)
    height: int
    codec: str
    pix_fmt: str
    rotation: int = 0

    @property
    def frames(self) -> int:
        """Numero di fotogrammi stimato da durata e frequenza."""
        return max(1, int(round(self.duration * self.fps)))

    @property
    def bit_depth(self) -> int:
        match = re.search(r"(\d{1,2})(?:le|be)?$", self.pix_fmt)
        if match:
            bits = int(match.group(1))
            if bits in (9, 10, 12, 14, 16):
                return bits
        return 8

    @property
    def has_alpha(self) -> bool:
        return bool(re.search(r"yuva|rgba|bgra|argb|abgr|gbrap|^ya\d|ya16", self.pix_fmt))

    @property
    def frame_time(self) -> float:
        return 1.0 / self.fps


_DURATION = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_VIDEO = re.compile(r"Stream #\d+:\d+.*?:\s*Video:\s*(.*)")
_SIZE = re.compile(r",\s*(\d{2,5})x(\d{2,5})")
_FPS = re.compile(r"([\d.]+)\s*fps")
_TBR = re.compile(r"([\d.]+)\s*tbr")
_ROTATION = re.compile(r"rotation of (-?[\d.]+) degrees")


def probe(path: str | os.PathLike) -> VideoInfo:
    """Legge durata, frequenza, dimensioni e formato dal rapporto di `ffmpeg -i`."""
    path = Path(path)
    if not path.is_file():
        raise FFmpegError(tr("File not found: {path}").format(path=path))
    result = _run([ffmpeg_exe(), "-hide_banner", "-nostdin", "-i", str(path)])
    text = result.stderr.decode("utf-8", "replace")

    stream = next((m for m in _VIDEO.finditer(text)), None)
    if stream is None:
        raise FFmpegError(tr("The file has no recognizable video track."))
    line = stream.group(1)
    # i campi sono separati da virgole; dentro le parentesi le virgole non contano
    fields = [f.strip() for f in re.split(r",(?![^(]*\))", line)]
    codec = re.split(r"[\s(]", fields[0], maxsplit=1)[0] if fields else "?"
    pix_fmt = ""
    for field in fields[1:]:
        base = re.split(r"[\s(]", field, maxsplit=1)[0]
        if re.match(r"^(yuv|yuyv|uyvy|rgb|bgr|gray|gbr|nv\d|p0|p2|p4|ya|pal|monob|x2|0rgb|0bgr|bayer)", base):
            pix_fmt = base
            break
    size = _SIZE.search(line)
    if size is None:
        raise FFmpegError(tr("Video size not recognized."))
    width, height = int(size.group(1)), int(size.group(2))

    fps_match = _FPS.search(line) or _TBR.search(line)
    if fps_match is None:
        raise FFmpegError(tr("Frame rate not recognized."))
    fps = float(fps_match.group(1))
    if fps <= 0:
        raise FFmpegError(tr("Invalid frame rate."))

    duration_match = _DURATION.search(text)
    if duration_match is None:
        raise FFmpegError(tr("Unknown video duration (stream or damaged file)."))
    h, m, s = duration_match.groups()
    duration = int(h) * 3600 + int(m) * 60 + float(s)
    if duration <= 0:
        raise FFmpegError(tr("Zero video duration."))

    rotation = 0
    rot = _ROTATION.search(text[stream.end():stream.end() + 600])
    if rot is not None:
        rotation = int(round(float(rot.group(1)))) % 360
        if rotation in (90, 270):
            width, height = height, width  # ffmpeg ruota in uscita: le anteprime escono cosi'

    return VideoInfo(path=path, duration=duration, fps=fps, width=width, height=height,
                     codec=codec, pix_fmt=pix_fmt or "?", rotation=rotation)


# ------------------------------------------------------------------ anteprime

def grab(path: str | os.PathLike, t: float, width: int | None = None, height: int | None = None,
         accurate: bool = True) -> Image.Image:
    """Il fotogramma all'istante `t`, come immagine RGB (ridotta se si chiede una misura).

    Con `accurate` ffmpeg decodifica dal keyframe precedente e scarta fino a
    `t`: esatto al fotogramma. Senza, si ferma al keyframe: molto piu' veloce,
    va bene per le anteprime della pellicola a bassi ingrandimenti.
    """
    path = Path(path)
    attempts = (t, max(0.0, t - 0.2), max(0.0, t - 1.0))
    last_error = ""
    for seek in attempts:
        cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-nostdin"]
        if not accurate:
            cmd.append("-noaccurate_seek")
        cmd += ["-ss", f"{seek:.6f}", "-i", str(path), "-an", "-sn", "-dn", "-map", "0:v:0",
                "-frames:v", "1", "-sws_flags", "accurate_rnd+full_chroma_int"]
        if width or height:
            cmd += ["-vf", f"scale={width or -1}:{height or -1}:flags=area"]
        cmd += ["-f", "image2pipe", "-c:v", "bmp", "-"]
        result = _run(cmd)
        if result.stdout:
            image = Image.open(io.BytesIO(result.stdout))
            image.load()
            return image.convert("RGB")
        last_error = result.stderr.decode("utf-8", "replace").strip()
        if seek == 0.0:
            break
    raise FFmpegError(last_error or tr("No frame at {seconds:.3f} s.").format(seconds=t))


def run_size(info: VideoInfo, width: int | None = None, height: int | None = None) -> tuple[int, int]:
    """Misura esatta dei fotogrammi di grab_run: serve a dividere il flusso raw."""
    if width is None and height is None:
        return info.width, info.height
    if height is not None:
        return max(2, int(round(info.width * height / info.height))), height
    assert width is not None
    return width, max(2, int(round(info.height * width / info.width)))


def grab_run(info: VideoInfo, first: int, count: int, width: int | None = None,
             height: int | None = None) -> list[Image.Image]:
    """`count` fotogrammi consecutivi da `first`, decodificati in un solo passaggio.

    Un processo solo e una sola decodifica dal keyframe: per fotogrammi vicini
    costa quasi quanto un grab() singolo. Il flusso e' rawvideo RGB a misura
    nota, cosi' si taglia a pezzi fissi. Alla fine del video arrivano meno
    fotogrammi di quelli chiesti.
    """
    count = max(0, min(count, info.frames - first))
    if count <= 0:
        return []
    w, h = run_size(info, width, height)
    cmd = base_args(info, first) + [
        "-frames:v", str(count), "-fps_mode", "passthrough",
        "-vf", f"scale={w}:{h}:flags=area", "-pix_fmt", "rgb24", "-f", "rawvideo", "-",
    ]
    data = _run(cmd, check=True).stdout
    size = w * h * 3
    return [Image.frombytes("RGB", (w, h), data[i * size:(i + 1) * size]) for i in range(len(data) // size)]


# ------------------------------------------------------------------ estrazione

def choose_pix_fmt(info: VideoInfo, fmt: str, depth: str) -> str:
    """Formato pixel di uscita: 8 o 16 bit per canale, con alfa se la sorgente ce l'ha."""
    _ext, _codec, p8, p8a, p16, p16a = FORMATS[fmt]
    want16 = depth == "16 bit" or (depth == "Auto" and info.bit_depth > 8)
    if want16 and p16 is not None:
        return p16a if info.has_alpha else p16
    return p8a if info.has_alpha else p8


def output_args(info: VideoInfo, fmt: str, depth: str) -> list[str]:
    """Opzioni di codifica comuni a estrazione e salvataggio del singolo fotogramma."""
    _ext, codec, *_rest = FORMATS[fmt]
    args = ["-pix_fmt", choose_pix_fmt(info, fmt, depth), "-c:v", codec]
    if fmt == "TIFF":
        args += ["-compression_algo", "lzw"]
    return args


def seek_time(info: VideoInfo, frame: int) -> float:
    """Istante da cui partire perche' il primo fotogramma decodificato sia `frame`.

    A meta' strada tra il fotogramma precedente e quello voluto: cosi' gli
    arrotondamenti della base dei tempi non fanno saltare o ripetere un fotogramma.
    """
    return max(0.0, (frame - 0.5) * info.frame_time)


def base_args(info: VideoInfo, first_frame: int) -> list[str]:
    return [
        ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        "-ss", f"{seek_time(info, first_frame):.6f}", "-i", str(info.path),
        "-an", "-sn", "-dn", "-map", "0:v:0",
        # conversione colore della migliore qualita' (croma a piena risoluzione, arrotondamento esatto)
        "-sws_flags", "accurate_rnd+full_chroma_int",
    ]


def save_frame(info: VideoInfo, frame: int, target: str | os.PathLike, fmt: str, depth: str) -> Path:
    """Salva il singolo fotogramma `frame` a piena risoluzione, senza perdita."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = base_args(info, frame) + ["-frames:v", "1", "-fps_mode", "passthrough"]
    cmd += output_args(info, fmt, depth) + ["-f", "image2", str(target)]
    _run(cmd, check=True)
    if not target.is_file():
        raise FFmpegError(tr("ffmpeg did not write the file."))
    return target


@dataclass
class Job:
    info: VideoInfo
    first_frame: int
    last_frame: int       # compreso
    step: int
    out_dir: Path
    prefix: str
    digits: int
    fmt: str
    depth: str
    start_number: int

    @property
    def count(self) -> int:
        return (self.last_frame - self.first_frame) // self.step + 1

    @property
    def extension(self) -> str:
        return FORMATS[self.fmt][0]

    def pattern(self) -> Path:
        return self.out_dir / f"{self.prefix}%0{self.digits}d.{self.extension}"

    def example_name(self) -> str:
        return f"{self.prefix}{self.start_number:0{self.digits}d}.{self.extension}"


class Extractor:
    """Estrazione dei fotogrammi di un intervallo, con avanzamento e interruzione."""

    def __init__(self, job: Job) -> None:
        self.job = job
        self._proc: subprocess.Popen | None = None
        self._cancelled = False

    def command(self) -> list[str]:
        job = self.job
        cmd = base_args(job.info, job.first_frame)
        if job.step > 1:
            cmd += ["-vf", f"select=not(mod(n\\,{job.step}))"]
        cmd += ["-fps_mode", "passthrough", "-frames:v", str(job.count)]
        cmd += output_args(job.info, job.fmt, job.depth)
        cmd += ["-start_number", str(job.start_number), "-f", "image2",
                "-progress", "pipe:1", "-nostats", str(job.pattern())]
        return cmd

    def run(self, on_progress: Callable[[int], None]) -> int:
        """Esegue ffmpeg; `on_progress` riceve i fotogrammi scritti. Restituisce il totale."""
        self.job.out_dir.mkdir(parents=True, exist_ok=True)
        self._proc = procs.popen(self.command(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        errors: list[bytes] = []
        reader = threading.Thread(target=lambda: errors.append(self._proc.stderr.read()), daemon=True)
        reader.start()
        frames = 0
        assert self._proc.stdout is not None
        for raw in self._proc.stdout:
            line = raw.decode("utf-8", "replace").strip()
            if line.startswith("frame="):
                try:
                    frames = int(line[6:])
                except ValueError:
                    continue
                on_progress(frames)
        code = self._proc.wait()
        reader.join(timeout=2)
        if self._cancelled:
            raise Cancelled()
        if code != 0:
            message = b"".join(errors).decode("utf-8", "replace").strip()
            raise FFmpegError(message or tr("ffmpeg ended with exit code {code}").format(code=code))
        return frames

    def cancel(self) -> None:
        self._cancelled = True
        proc = self._proc
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
