# VideoSlicer — estrazione di fotogrammi da video.  Copyright (C) 2026 Andrea Cumini <andrea@osintinfo.net>
# SPDX-License-Identifier: GPL-3.0-only
# GNU GPL v3 con termini aggiuntivi (attribuzione dell'autore): vedi LICENSE e NOTICE.
"""Traduzione italiana dei testi dell'interfaccia.

La chiave e' il testo inglese cosi' come compare nel codice (in tr() e N_()),
il valore la sua traduzione. I segnaposto tra graffe vanno lasciati identici.
Le chiavi non tradotte restano in inglese.
"""

from __future__ import annotations

IT: dict[str, str] = {
    # ---------------------------------------------------------------- avvio
    "Cannot start the interface: {error}\n\n"
    "Install the dependencies with:\n"
    "    python -m pip install -r requirements.txt":
        "Impossibile avviare l'interfaccia: {error}\n\n"
        "Installa le dipendenze con:\n"
        "    python -m pip install -r requirements.txt",

    # --------------------------------------------------------------- ffmpeg
    "ffmpeg not found. Download it from the FFmpeg box of the Configuration page, "
    "or install it and put it in the PATH.":
        "ffmpeg non trovato. Scaricalo dal riquadro FFmpeg della pagina Configurazione, "
        "oppure installalo e mettilo nel PATH.",
    "Cannot check the latest ffmpeg version: {error}": "Impossibile verificare l'ultima versione di ffmpeg: {error}",
    "Unexpected answer from the ffmpeg download site.": "Risposta inattesa dal sito di download di ffmpeg.",
    "Downloading {label}": "Scaricamento di {label}",
    "Download of {label} failed: {error}": "Scaricamento di {label} non riuscito: {error}",
    "Invalid archive: suspicious path '{member}'.": "Archivio non valido: percorso sospetto '{member}'.",
    "The downloaded file is not a valid zip archive.": "Il file scaricato non è un archivio zip valido.",
    "The downloaded package does not contain {name}.": "Il pacchetto scaricato non contiene {name}.",
    "Cannot update '{name}': files in use. Wait for the running extraction and try again.":
        "Impossibile aggiornare '{name}': file in uso. Attendi la fine dell'estrazione e riprova.",
    "Automatic download is available on Windows only: install ffmpeg with the "
    "system package manager.":
        "Il download automatico è disponibile solo su Windows: installa ffmpeg con il "
        "gestore dei pacchetti del sistema.",
    "Extracting ffmpeg": "Estrazione di ffmpeg",
    "The downloaded ffmpeg does not run on this PC.": "L'ffmpeg scaricato non si avvia su questo PC.",
    "{name} is missing after extraction.": "{name} manca dopo l'estrazione.",

    # ------------------------------------------------------- riquadro FFmpeg
    "Checking…": "Verifica…",
    "Check": "Verifica",
    "Check for updates": "Cerca aggiornamenti",
    "Download / Update": "Scarica / Aggiorna",
    "ffmpeg is a separate program (LGPL/GPL). The download takes the official Windows "
    "build from {url} and keeps only ffmpeg.exe, LICENSE and README in the tools\\ffmpeg "
    "folder next to the program: no installation, no changes to the PATH.":
        "ffmpeg è un programma separato (LGPL/GPL). Il download prende il build ufficiale per "
        "Windows da {url} e tiene solo ffmpeg.exe, LICENSE e README nella cartella tools\\ffmpeg "
        "accanto al programma: nessuna installazione, nessuna modifica al PATH.",
    "ffmpeg check failed": "Verifica di ffmpeg non riuscita",
    "tools folder": "cartella tools",
    "system PATH": "PATH di sistema",
    "Python package": "pacchetto Python",
    "OK  ·  ffmpeg {version}  ·  {source}  ·  {path}": "OK  ·  ffmpeg {version}  ·  {source}  ·  {path}",
    "Engine: ffmpeg {version} ({path})": "Motore: ffmpeg {version} ({path})",
    "Missing: download it with the button on the right.": "Mancante: scaricalo con il pulsante a destra.",
    "ffmpeg not found: download it from the FFmpeg box of the Configuration page.":
        "ffmpeg non trovato: scaricalo dal riquadro FFmpeg della pagina Configurazione.",
    "ffmpeg missing: download it from the FFmpeg box.": "ffmpeg mancante: scaricalo dal riquadro FFmpeg.",
    "Checking the latest ffmpeg version…": "Verifica dell'ultima versione di ffmpeg…",
    "ffmpeg {version} is up to date.": "ffmpeg {version} è aggiornato.",
    "Latest release: {latest}. Installed: {installed}. Download it now?":
        "Ultima release: {latest}. Installata: {installed}. Scaricarla adesso?",
    "Update check failed": "Controllo aggiornamenti non riuscito",
    "Wait for the running extraction, then try again.": "Attendi la fine dell'estrazione in corso, poi riprova.",
    "Downloading ffmpeg…": "Scaricamento di ffmpeg…",
    "Downloading ffmpeg from {url}": "Scaricamento di ffmpeg da {url}",
    "ffmpeg downloaded into {path}": "ffmpeg scaricato in {path}",
    "Download cancelled.": "Scaricamento annullato.",
    "ffmpeg download failed": "Scaricamento di ffmpeg non riuscito",
    "ffmpeg: exit code {code}": "ffmpeg: codice di uscita {code}",
    "File not found: {path}": "File non trovato: {path}",
    "The file has no recognizable video track.": "Il file non contiene una traccia video riconoscibile.",
    "Video size not recognized.": "Dimensioni del video non riconosciute.",
    "Frame rate not recognized.": "Frequenza dei fotogrammi non riconosciuta.",
    "Invalid frame rate.": "Frequenza dei fotogrammi non valida.",
    "Unknown video duration (stream or damaged file).":
        "Durata del video sconosciuta (flusso o file danneggiato).",
    "Zero video duration.": "Durata del video nulla.",
    "No frame at {seconds:.3f} s.": "Nessun fotogramma all'istante {seconds:.3f} s.",
    "ffmpeg did not write the file.": "ffmpeg non ha scritto il file.",
    "ffmpeg ended with exit code {code}": "ffmpeg terminato con codice {code}",

    # -------------------------------------------------------------- dialoghi
    "CONFIRM": "CONFERMA",
    "WARNING": "ATTENZIONE",
    "ERROR": "ERRORE",
    "Yes": "Sì",

    # ----------------------------------------------------------- navigazione
    "PAGES": "PAGINE",
    "Configuration": "Configurazione",
    "Extraction": "Estrazione",
    "Preview, timeline and extraction": "Anteprima, timeline ed estrazione",
    "{app}  /  PAGE {index:02d}": "{app}  /  PAGINA {index:02d}",

    # ---------------------------------------------------------- intestazione
    "none": "nessuno",
    "Open video… (Ctrl+O)": "Apri video… (Ctrl+O)",
    "No video": "Nessun video",
    "Reading…": "Lettura…",
    "Ready": "Pronto",
    "Error": "Errore",
    "Extracting…": "Estrazione…",

    # ------------------------------------------------------------- anteprima
    "Preview": "Anteprima",
    "Open a video to see the preview": "Apri un video per vedere l'anteprima",
    "First frame (Home)": "Primo fotogramma (Home)",
    "Back 10 frames (Shift+←)": "Indietro di 10 fotogrammi (Shift+←)",
    "Previous frame (←)": "Fotogramma precedente (←)",
    "Next frame (→)": "Fotogramma successivo (→)",
    "Forward 10 frames (Shift+→)": "Avanti di 10 fotogrammi (Shift+→)",
    "Last frame (End)": "Ultimo fotogramma (End)",
    "Save frame": "Salva fotogramma",
    "Save the shown frame at full resolution, lossless (Ctrl+S)":
        "Salva il fotogramma mostrato a piena risoluzione, senza perdita (Ctrl+S)",
    "Preview unavailable: {error}": "Anteprima non disponibile: {error}",
    "wheel: zoom  ·  drag: pan  ·  double-click: fit  ·  Shift+wheel: frames":
        "rotellina: zoom  ·  trascina: sposta  ·  doppio clic: adatta  ·  Shift+rotellina: fotogrammi",

    # -------------------------------------------------------------- sorgente
    "Source": "Sorgente",
    "Open video…": "Apri video…",
    "Duration": "Durata",
    "Frames": "Fotogrammi",
    "Resolution": "Risoluzione",
    "Codec": "Codec",
    "  (rotated {degrees}°)": "  (ruotato {degrees}°)",
    "Open video": "Apri video",
    "Videos": "Video",
    "All files": "Tutti i file",
    "Reading {name}…": "Lettura di {name}…",
    "Cannot open the video": "Impossibile aprire il video",
    "{name}: {frames} frames, {duration}.": "{name}: {frames} fotogrammi, {duration}.",
    "Opened {path} — {width}x{height}, {fps} fps, {codec} {pix_fmt} ({bits} bit), {duration}":
        "Aperto {path} — {width}x{height}, {fps} fps, {codec} {pix_fmt} ({bits} bit), {duration}",

    # ---------------------------------------------------------------- uscita
    "Output": "Uscita",
    "Destination folder": "Cartella di destinazione",
    "Subfolder named after the video": "Sottocartella con il nome del video",
    "Browse…": "Sfoglia…",
    "Format": "Formato",
    "Color depth": "Profondità colore",
    "Step (1 = all)": "Passo (1 = tutti)",
    "Prefix": "Prefisso",
    "Digits": "Cifre",
    "Numbering": "Numerazione",
    "Frame number in the video": "N. fotogramma nel video",
    "Sequential from 1": "Progressiva da 1",
    "Example: {name}": "Esempio: {name}",
    "{count} files: {first} … {last}  ·  {pix_fmt} ({bits}/channel)":
        "{count} file: {first} … {last}  ·  {pix_fmt} ({bits}/canale)",
    "Ready to extract {count} frames (f{first} → f{last}{step}).":
        "Pronto a estrarre {count} fotogrammi (f{first} → f{last}{step}).",
    ", step {step}": ", passo {step}",

    # ---------------------------------------------------------------- lingua
    "Language": "Lingua",
    "Credits": "Crediti",
    "Free software under the GNU GPL v3 with author attribution: see the LICENSE and "
    "NOTICE files. Video decoding by FFmpeg, a separate program under its own license.":
        "Software libero sotto GNU GPL v3 con attribuzione dell'autore: vedi i file LICENSE e "
        "NOTICE. La decodifica video è di FFmpeg, programma separato con la propria licenza.",
    "Interface language. The change is immediate and is saved for the next start.":
        "Lingua dell'interfaccia. Il cambio è immediato e viene ricordato al prossimo avvio.",

    # -------------------------------------------------------------- timeline
    "Ctrl+wheel: zoom  ·  wheel: scroll  ·  drag I / O and the cursor  ·  double-click the ruler: all":
        "Ctrl+rotellina: zoom  ·  rotellina: scorri  ·  trascina I / O e il cursore  ·  doppio clic sul righello: tutto",
    "In  [I]": "Inizio  [I]",
    "Out  [O]": "Fine  [O]",
    "Sets the start of the selection at the cursor (key I)":
        "Mette l'inizio della selezione sul cursore (tasto I)",
    "Sets the end of the selection at the cursor (key O)":
        "Mette la fine della selezione sul cursore (tasto O)",
    "Moves the cursor to the start of the selection": "Porta il cursore all'inizio della selezione",
    "Moves the cursor to the end of the selection": "Porta il cursore alla fine della selezione",
    "CURSOR": "CURSORE",
    "Time (1:23.456, 83.4) or frame (f2000), then Enter":
        "Tempo (1:23.456, 83.4) o fotogramma (f2000), poi Invio",
    "Zoom out (−)": "Riduci (−)",
    "Zoom in (+)": "Ingrandisci (+)",
    "All": "Tutto",
    "Selection": "Selezione",
    "Selection: f{first} → f{last}  ·  {count} frames  ·  {seconds:.3f} s":
        "Selezione: f{first} → f{last}  ·  {count} fotogrammi  ·  {seconds:.3f} s",
    "View: {start} → {end}  ({seconds:.3f} s, {frames:.1f} frames)":
        "Vista: {start} → {end}  ({seconds:.3f} s, {frames:.1f} fotogrammi)",
    "Time not recognized: use mm:ss.mmm, seconds or f<number>.":
        "Tempo non riconosciuto: usa mm:ss.mmm, secondi oppure f<numero>.",
    "Open a video to see the timeline": "Apri un video per vedere la timeline",

    # ------------------------------------------------------------ estrazione
    "Open a video and choose the range to extract.": "Apri un video e scegli l'intervallo da estrarre.",
    "Open folder": "Apri cartella",
    "Cancel": "Annulla",
    "Extract frames": "Estrai fotogrammi",
    "Open a video first.": "Apri prima un video.",
    "Warning: BMP is 8 bits per channel; the source has more. Use PNG or TIFF for 16 bits.":
        "Avviso: BMP è a 8 bit per canale; la sorgente ne ha di più. Usa PNG o TIFF per i 16 bit.",
    "Folder not usable": "Cartella non utilizzabile",
    "Existing files": "File esistenti",
    "The folder {folder} already contains {pattern} files: those with the same number will be "
    "overwritten. Continue?":
        "Nella cartella {folder} ci sono già file {pattern}: quelli con lo stesso numero verranno "
        "sovrascritti. Continuare?",
    "Extracting {count} frames into «{folder}»…": "Estrazione di {count} fotogrammi in «{folder}»…",
    "Extraction in progress…": "Estrazione in corso…",
    "Extraction: f{first} → f{last}, step {step}, {count} {format} files ({pix_fmt}) into {folder}":
        "Estrazione: f{first} → f{last}, passo {step}, {count} file {format} ({pix_fmt}) in {folder}",
    "{done} / {total} frames  ·  {rate:.1f} per second  ·  about {eta} left":
        "{done} / {total} fotogrammi  ·  {rate:.1f} al secondo  ·  restano circa {eta}",
    "Done: {count} frames in «{folder}» ({seconds:.1f} s).":
        "Completato: {count} fotogrammi in «{folder}» ({seconds:.1f} s).",
    "Extracted {count} frames in {seconds:.1f} s.": "Estratti {count} fotogrammi in {seconds:.1f} s.",
    "Done: {count} frames in {seconds:.1f} s": "Completato: {count} fotogrammi in {seconds:.1f} s",
    "Extraction cancelled.": "Estrazione annullata.",
    "Extraction cancelled by the user": "Estrazione annullata dall'utente",
    "Extraction failed: see the log.": "Estrazione fallita: vedi il registro.",
    "Extraction failed": "Estrazione fallita",
    "The folder does not exist yet.": "La cartella non esiste ancora.",
    "Cannot open the folder": "Impossibile aprire la cartella",
    "Extraction in progress": "Estrazione in corso",
    "The extraction is still running. Stop it and close?":
        "L'estrazione è ancora in corso. Interromperla e chiudere?",

    # ------------------------------------------------- salvataggio fotogramma
    "{format} (lossless)": "{format} (senza perdita)",
    "Saving frame {frame}…": "Salvataggio del fotogramma {frame}…",
    "Saved {path}": "Salvato {path}",
    "Frame f{frame} saved to {path} ({pix_fmt})": "Fotogramma f{frame} salvato in {path} ({pix_fmt})",
    "Save failed": "Salvataggio fallito",

    # ------------------------------------------------------------------ piede
    "Ready.": "Pronto.",
    "Ctrl+1/2  page   ·   ← →  frame   ·   I / O  markers   ·   Ctrl+S  save":
        "Ctrl+1/2  pagina   ·   ← →  fotogramma   ·   I / O  segnaposto   ·   Ctrl+S  salva",
    "ffmpeg missing": "ffmpeg mancante",
    "Operation failed": "Operazione fallita",
    "ERROR - {title}: {message}": "ERRORE - {title}: {message}",
    "Error: {title}": "Errore: {title}",
    "INTERNAL ERROR": "ERRORE INTERNO",
    "Internal error: details in the log.": "Errore interno: dettagli nel registro.",
}
