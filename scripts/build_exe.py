# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Compila VideoSlicer in un unico eseguibile Windows e, a richiesta, prepara e pubblica la release.

    .venv\\Scripts\\python.exe scripts\\build_exe.py              solo dist/VideoSlicer.exe
    .venv\\Scripts\\python.exe scripts\\build_exe.py --release    + zip e note di rilascio in dist/
    .venv\\Scripts\\python.exe scripts\\build_exe.py --publish    + release su GitHub con lo zip allegato

L'eseguibile e' un solo file, senza finestra console, con l'icona «VS» e le
proprieta' del file (versione, autore) compilate. Dentro ci sono Python, le
librerie, il logo e l'icona; ffmpeg no: l'eseguibile lo cerca nella cartella
tools/ accanto a se' e, se manca, propone di scaricarlo. Il pacchetto
imageio-ffmpeg, se e' installato nel virtualenv, viene escluso di proposito.

--release produce dist/VideoSlicer-<versione>-windows-x64.zip (exe, LICENSE,
NOTICE, README) e dist/release-notes-<versione>.md, con le novita' prese dalla
sezione piu' recente di CHANGELOG.md e l'impronta SHA-256 dello zip.

--publish (che include --release) crea su GitHub la release «v<versione>» con
quelle note e vi allega lo zip. Il repository e' quello del remote «origin»;
serve un token con permesso di scrittura sui contenuti, letto dalla variabile
d'ambiente GITHUB_TOKEN oppure chiesto al momento (non viene salvato). La tag
viene creata da GitHub sul commit corrente del ramo, che quindi deve essere
gia' stato inviato con git push. Se una release con la stessa tag esiste gia',
lo script si ferma: alza la versione in videoslicer/__init__.py.
"""

from __future__ import annotations

import getpass
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from videoslicer import APP_NAME, AUTHOR, AUTHOR_EMAIL, AUTHOR_URL, COPYRIGHT, __version__  # noqa: E402

ASSETS = ROOT / "videoslicer" / "assets"
ICON = ASSETS / "videoslicer.ico"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
CHANGELOG = ROOT / "CHANGELOG.md"
EXE = DIST / f"{APP_NAME}.exe"
ZIP = DIST / f"{APP_NAME}-{__version__}-windows-x64.zip"
NOTES = DIST / f"release-notes-{__version__}.md"
TAG = f"v{__version__}"
ZIP_FILES = ("LICENSE", "NOTICE", "README.md", "README.it.md")

# Proprieta' del file mostrate da Esplora risorse (lingua 0x0409 = inglese).
VERSION_INFO = """\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={numbers}, prodvers={numbers},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0),
  ),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', {author!r}),
      StringStruct('FileDescription', {description!r}),
      StringStruct('FileVersion', {version!r}),
      StringStruct('InternalName', {name!r}),
      StringStruct('LegalCopyright', {copyright!r}),
      StringStruct('OriginalFilename', {exe!r}),
      StringStruct('ProductName', {name!r}),
      StringStruct('ProductVersion', {version!r}),
    ])]),
    VarFileInfo([VarStruct('Translation', [0x0409, 1200])]),
  ],
)
"""

RELEASE_NOTES = """\
{intro}

## What's new in {version}

{changes}

## Download

**{zip}** is the standalone program for Windows 10/11 (64-bit). Python is
not needed: unzip it anywhere and run `{exe}`.

Updating from a previous version: replace `{exe}` with the new one. Your
`tools` folder (ffmpeg) and `config.json` stay as they are.

## First start

- The interface starts in English; switch to Italian with **EN / IT** in the
  Configuration page.
- ffmpeg is not included: at first start the program offers to download the
  official Windows build into a `tools` folder next to the executable.
- The executable is not signed, so Windows SmartScreen may show a warning the
  first time it runs.

## Verify the download

SHA-256 of `{zip}`:

```
{sha256}
```

## License

Free software under the GNU General Public License version 3 with additional
terms (author attribution): see `LICENSE` and `NOTICE`, included in the zip.

Author: {author} — [{url}](https://{url}) — {email}
"""


# ------------------------------------------------------------------- build

def ensure_icon() -> None:
    if not ICON.is_file():
        sys.exit(f"Icona assente: {ICON}")


def ensure_pyinstaller() -> None:
    if importlib.util.find_spec("PyInstaller") is None:
        print("PyInstaller non presente: lo installo nel virtualenv…")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def version_file() -> Path:
    parts = [int(p) for p in __version__.split(".") if p.isdigit()][:4]
    numbers = tuple(parts + [0] * (4 - len(parts)))
    target = BUILD / "version_info.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        VERSION_INFO.format(
            numbers=numbers, author=AUTHOR, name=APP_NAME, version=__version__,
            description=f"{APP_NAME} - lossless video frame extractor",
            copyright=COPYRIGHT, exe=EXE.name,
        ),
        encoding="utf-8",
    )
    return target


def build() -> None:
    ensure_icon()
    ensure_pyinstaller()
    argv = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile", "--windowed",
        "--name", APP_NAME,
        "--icon", str(ICON),
        "--version-file", str(version_file()),
        # logo e icona: il programma li cerca accanto a theme.py
        "--add-data", f"{ASSETS}{os.pathsep}videoslicer/assets",
        # temi e caratteri di customtkinter sono file di dati, non moduli
        "--collect-data", "customtkinter",
        "--hidden-import", "PIL._tkinter_finder",
        # ffmpeg resta fuori: sta in tools/ accanto all'exe, non nel bundle
        "--exclude-module", "imageio_ffmpeg",
        "--exclude-module", "imageio",
        "--distpath", str(DIST),
        "--workpath", str(BUILD),
        "--specpath", str(BUILD),
        str(ROOT / "VideoSlicer.py"),
    ]
    code = subprocess.call(argv, cwd=ROOT)
    if code != 0:
        sys.exit(code)
    print(f"\n{EXE}  ({EXE.stat().st_size / 1024 / 1024:.1f} MB)")


# ----------------------------------------------------------------- release

def changelog_section() -> tuple[str, str]:
    """Introduzione e novita' della versione corrente da CHANGELOG.md.

    Il file ha una sezione «## <versione>» per release; la prima riga di testo
    sotto il titolo fa da introduzione, il resto (elenco puntato) da novita'.
    """
    if not CHANGELOG.is_file():
        sys.exit(f"Manca {CHANGELOG.name}: scrivi la sezione «## {__version__}» con le novita'.")
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(__version__)}\b[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if match is None:
        sys.exit(f"{CHANGELOG.name} non ha la sezione «## {__version__}»: aggiungila con le novita'.")
    lines = [line.rstrip() for line in match.group(1).strip().splitlines()]
    intro = lines[0] if lines and not lines[0].startswith(("-", "*")) else f"{APP_NAME} {__version__}."
    body = lines[1:] if intro == lines[0] else lines
    changes = "\n".join(body).strip() or "- Maintenance release."
    return intro, changes


def package() -> None:
    if not EXE.is_file():
        sys.exit(f"Manca {EXE}: esegui prima il build.")
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(EXE, EXE.name)
        for name in ZIP_FILES:
            zf.write(ROOT / name, name)
    sha256 = hashlib.sha256(ZIP.read_bytes()).hexdigest()
    intro, changes = changelog_section()
    NOTES.write_text(
        RELEASE_NOTES.format(intro=intro, version=__version__, changes=changes, zip=ZIP.name,
                             exe=EXE.name, sha256=sha256, author=AUTHOR, url=AUTHOR_URL, email=AUTHOR_EMAIL),
        encoding="utf-8",
    )
    print(f"{ZIP}  ({ZIP.stat().st_size / 1024 / 1024:.1f} MB)\n{NOTES}\nSHA-256 {sha256}")


# ------------------------------------------------------------------ GitHub

def github_repo() -> tuple[str, str]:
    """(utente, repository) dal remote origin: https://github.com/u/r.git oppure git@github.com:u/r.git."""
    try:
        url = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("Nessun remote «origin»: collega prima il repository GitHub (git remote add origin …).")
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if match is None:
        sys.exit(f"Il remote origin non e' su GitHub: {url}")
    return match.group(1), match.group(2)


def github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("Serve un token GitHub con permesso di scrittura sui contenuti del repository")
        print("(Settings → Developer settings → Personal access tokens). Non viene salvato.")
        token = getpass.getpass("GITHUB_TOKEN: ").strip()
    if not token:
        sys.exit("Token assente.")
    return token


def github_call(method: str, url: str, token: str, data: bytes | None = None,
                content_type: str = "application/json") -> dict:
    request = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"{APP_NAME}-build/{__version__}",
        "Content-Type": content_type,
    })
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        sys.exit(f"GitHub ha risposto {exc.code} a {method} {url}:\n{detail}")
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        sys.exit(f"GitHub non raggiungibile: {exc}")


def publish() -> None:
    owner, repo = github_repo()
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() or "main"
    if subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        print("Attenzione: ci sono modifiche non ancora inviate con commit/push; la tag va sul commit corrente.")
    token = github_token()
    api = f"https://api.github.com/repos/{owner}/{repo}"

    # una release con questa tag non deve esistere: la versione va alzata
    request = urllib.request.Request(f"{api}/releases/tags/{TAG}", headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
        "User-Agent": f"{APP_NAME}-build/{__version__}"})
    try:
        with urllib.request.urlopen(request, timeout=30):
            sys.exit(f"La release {TAG} esiste gia' su GitHub: alza __version__ in videoslicer/__init__.py.")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            sys.exit(f"GitHub ha risposto {exc.code} controllando la release {TAG}.")

    release = github_call("POST", f"{api}/releases", token, json.dumps({
        "tag_name": TAG, "target_commitish": branch, "name": f"{APP_NAME} {__version__}",
        "body": NOTES.read_text(encoding="utf-8"), "draft": False, "prerelease": False,
    }).encode("utf-8"))
    upload_url = release["upload_url"].split("{")[0] + "?" + urllib.parse.urlencode({"name": ZIP.name})
    github_call("POST", upload_url, token, ZIP.read_bytes(), content_type="application/zip")
    print(f"\nRelease pubblicata: {release['html_url']}")


def main() -> int:
    if sys.platform != "win32":
        sys.exit(f"{APP_NAME} si compila solo su Windows.")
    args = set(sys.argv[1:])
    unknown = args - {"--release", "--publish", "--no-build"}
    if unknown:
        sys.exit(f"Opzione sconosciuta: {' '.join(sorted(unknown))}. Vedi l'intestazione dello script.")
    if "--no-build" not in args:
        build()
    if "--release" in args or "--publish" in args:
        package()
    if "--publish" in args:
        publish()
    elif "--release" in args:
        print(f"Per pubblicare: rileggi {NOTES.name}, poi scripts\\build_exe.py --publish --no-build")
    else:
        print("Distribuisci l'exe da solo (con LICENSE e NOTICE): ffmpeg lo scarica l'utente in tools/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
