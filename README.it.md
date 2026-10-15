# VideoSlicer

[English](README.md) · **Italiano**

Scompone un video, o un suo intervallo, in singoli fotogrammi **senza perdita
di qualità**, con anteprima su una timeline ingrandibile fino al singolo
fotogramma, segnaposto di inizio e fine, navigazione fotogramma per
fotogramma e salvataggio del singolo fotogramma a piena risoluzione.

**Autore: Andrea Cumini — [www.osintinfo.net](https://www.osintinfo.net) — andrea@osintinfo.net**

L'interfaccia è scritta in Python con **customtkinter**, nello stesso stile di
AndrOsint e TagFaces (tema scuro Seity). La decodifica è affidata a
**ffmpeg**, usato come programma separato.

## Requisiti

- Windows 10/11 (su altri sistemi funziona con la barra del titolo standard)
- Python 3.10 o successivo (con Tkinter, incluso nell'installer ufficiale)
- ffmpeg, come programma **separato**: VideoSlicer lo scarica nella cartella
  `tools/ffmpeg/` accanto al programma (vedi *FFmpeg* più sotto); un ffmpeg
  già nel PATH viene usato anche lui

Dipendenze Python (`requirements.txt`): `customtkinter` e `pillow`.

```bash
python -m pip install -r requirements.txt
```

## Avvio

```bash
python VideoSlicer.py
```

Oppure doppio clic su `Avvia.bat` (parte senza finestra console e usa il
virtualenv `.venv` se presente). Si può passare il video da aprire come
argomento: `python VideoSlicer.py film.mp4`.

## Eseguibile unico

Per ottenere un unico `VideoSlicer.exe` che gira senza Python installato:

```bash
.venv\Scripts\python.exe scripts\build_exe.py
```

Lo script installa PyInstaller nel virtualenv se manca e scrive
`dist\VideoSlicer.exe` (un solo file, senza finestra console, icona «VS» e
proprietà del file). ffmpeg resta volutamente fuori dal bundle: l'eseguibile
lo cerca in `tools\ffmpeg\` accanto a sé e propone di scaricarlo. Accanto
all'eseguibile finiscono anche `config.json` e `tools\`.

### Release

```bash
.venv\Scripts\python.exe scripts\build_exe.py --release
```

scrive anche `dist\VideoSlicer-<versione>-windows-x64.zip` (exe, LICENSE,
NOTICE, README) e `dist\release-notes-<versione>.md`, con le novità prese
dalla sezione più recente di `CHANGELOG.md` e l'impronta SHA-256 dello zip.

```bash
.venv\Scripts\python.exe scripts\build_exe.py --publish
```

fa tutto questo e poi crea su GitHub la release `v<versione>` sul repository
del remote `origin`, con quelle note e lo zip allegato. Serve un token GitHub
con permesso di scrittura sui contenuti del repository, dalla variabile
d'ambiente `GITHUB_TOKEN` o digitato al momento (non viene mai salvato).
Prima fai il push del commit: la tag viene creata sul ramo corrente. Per una
nuova release alza `__version__` in `videoslicer/__init__.py` e aggiungi una
sezione a `CHANGELOG.md`. `--no-build` riusa l'eseguibile già in `dist\`.

## FFmpeg

ffmpeg non è incluso: è un programma separato con la propria licenza. Al
primo avvio, se non viene trovato, si apre la pagina **Configurazione** sul
riquadro *FFmpeg*: **Scarica / Aggiorna** prende il build ufficiale per
Windows ("release essentials") da <https://www.gyan.dev/ffmpeg/builds/>,
quello indicato dal sito di FFmpeg, e tiene solo `ffmpeg.exe`, `LICENSE` e
`README.txt` in `tools/ffmpeg/`. Circa 110 MB, con barra di avanzamento e
**Annulla**. Nessuna installazione, nessuna modifica al PATH, nessun
privilegio di amministratore.

**Cerca aggiornamenti** confronta la release scritta all'ultimo download con
l'ultima pubblicata e propone di scaricarla. **Verifica** rilegge dove sta
ffmpeg e la sua versione. ffmpeg viene cercato in quest'ordine:
`tools/ffmpeg/ffmpeg.exe`, il PATH di sistema e, se è installato il pacchetto
Python facoltativo `imageio-ffmpeg`, il binario che porta con sé.

Per distribuire il programma copia la cartella senza `tools/`: ogni utente
scarica ffmpeg con un clic.

## Lingua

L'interfaccia è in **inglese** (predefinito) o **italiano**. Si cambia con i
pulsanti **EN / IT** nel riquadro *Lingua* della pagina **Configurazione**:
il cambio è immediato, senza riavvio, e la scelta è salvata in `config.json`.
Solo il registro conserva le righe già scritte nella lingua in cui sono nate.

Nel codice i testi sono in inglese; la traduzione italiana è in
`videoslicer/translations.py` (le chiavi sono i testi inglesi).

## Uso

L'interfaccia ha due pagine, nella barra laterale (Ctrl+1 / Ctrl+2):
**Configurazione** (video aperto, cartella e formato di uscita, lingua,
crediti) ed **Estrazione** (anteprima, timeline, estrazione). L'anteprima occupa tutta la
larghezza della pagina e cresce con la finestra: massimizzala per vederla
grande.

1. **Apri video…** (o Ctrl+O, o l'icona nel riquadro VIDEO in alto). Nel
   riquadro *Sorgente* compaiono durata, numero di fotogrammi, risoluzione,
   codec e profondità di colore.
2. Nella **timeline** scegli l'intervallo:
   - **Ctrl+rotellina** ingrandisce e riduce intorno al mouse, fino a vedere
     i singoli fotogrammi; **+** / **−** / **Tutto** / **Selezione** fanno lo
     stesso dai pulsanti. La **rotellina** scorre; la barra in basso mostra
     tutto il video e si trascina.
   - Clic o trascinamento sulla pellicola sposta il **cursore** e aggiorna
     l'anteprima. **← →** vanno di un fotogramma, **Shift+← →** di dieci,
     **Home / End** al primo e all'ultimo; Shift+rotellina sopra l'anteprima
     fa lo stesso. Nel campo *CURSORE* si scrive un tempo (`1:23.456`, `83.4`)
     o un fotogramma (`f2000`).
   - Nell'**anteprima** la rotellina ingrandisce intorno al mouse (fino a 32
     pixel per pixel del video; oltre 3x si vedono i pixel veri, senza
     sfocatura), il trascinamento sposta, il doppio clic riadatta il
     fotogramma. Ingrandendo, il fotogramma viene chiesto a piena
     risoluzione; lo zoom resta quando si cambia fotogramma.
   - **Inizio [I]** e **Fine [O]** mettono i segnaposto sul
     cursore; le bandierine **I** e **O** si trascinano anche direttamente,
     e i campi IN / OUT accettano un tempo o un fotogramma.
3. In **Uscita** scegli cartella, formato (PNG, TIFF, BMP), profondità di
   colore (automatica: 16 bit per canale se la sorgente è a 10 bit o più),
   prefisso, cifre, numerazione (numero del fotogramma nel video oppure
   progressiva da 1) e passo (1 = tutti i fotogrammi, 5 = uno ogni cinque).
4. **Estrai fotogrammi** (pagina Estrazione): l'avanzamento è nel riquadro
   *Estrazione*, che riassume anche formato e nome dei file; **Annulla**
   interrompe, **Apri cartella** mostra il risultato. Il registro compare
   sotto quando la finestra è abbastanza alta.
5. **Salva fotogramma** (o Ctrl+S) scrive il singolo fotogramma mostrato
   nell'anteprima a piena risoluzione, nello stesso formato senza perdita.

## Senza perdita: cosa significa

Un video compresso (H.264, HEVC, VP9…) non contiene immagini "originali":
contiene i dati da cui il decodificatore ricostruisce ogni fotogramma.
VideoSlicer prende esattamente quel fotogramma decodificato e lo scrive in
un formato che non ricomprime con perdita:

- **PNG** (compressione lossless, consigliato), **TIFF** (LZW, lossless),
  **BMP** (non compresso, solo 8 bit per canale);
- la conversione dal formato pixel del video (es. `yuv420p`) a RGB usa
  l'interpolazione del croma a piena risoluzione e l'arrotondamento esatto
  di ffmpeg (`accurate_rnd+full_chroma_int`);
- le sorgenti a **10/12 bit** escono a **16 bit per canale** (PNG `rgb48`,
  TIFF `rgb48`), così non si perde profondità; il canale alfa, se c'è,
  viene conservato;
- nessun fotogramma viene duplicato o saltato (`-fps_mode passthrough`): il
  conteggio è esatto e la numerazione corrisponde al fotogramma nel video.

Con video a frequenza variabile (VFR) il numero di fotogramma è calcolato
dalla frequenza media, quindi la corrispondenza tempo/fotogramma è
approssimata.

## Struttura

| File | Contenuto |
| --- | --- |
| `VideoSlicer.py` | punto di ingresso |
| `videoslicer/app.py` | finestra principale |
| `videoslicer/timeline.py` | timeline con anteprime, zoom e segnaposto |
| `videoslicer/shell.py` | barra di navigazione laterale tra le pagine |
| `videoslicer/ffmpeg.py` | informazioni sul video, anteprime, estrazione |
| `videoslicer/tools.py` | ricerca, download e aggiornamento di ffmpeg in `tools/` |
| `videoslicer/i18n.py`, `translations.py` | lingua dell'interfaccia e traduzione italiana |
| `videoslicer/theme.py`, `widgets.py`, `frameless.py` | tema scuro, componenti, finestra senza barra |
| `videoslicer/tasks.py` | lavori in background e consegna alla GUI |
| `videoslicer/config.py` | impostazioni in `config.json` |
| `scripts/build_exe.py` | compila `VideoSlicer.exe`; `--release` zip e note; `--publish` release su GitHub |
| `CHANGELOG.md` | novità per versione, usate per le note di rilascio |

## Licenza

GNU GPL v3 con termini aggiuntivi di attribuzione dell'autore: vedi
[LICENSE](LICENSE) e [NOTICE](NOTICE). La dicitura

    Andrea Cumini - andrea@osintinfo.net - www.osintinfo.net

va conservata nell'interfaccia (piede della finestra e riquadro Crediti) e nella
documentazione.
Il nome "VideoSlicer", il logo e l'icona "VS" identificano il programma
originale: una versione modificata distribuita ad altri deve usare nome e
logo diversi.

ffmpeg è un programma separato, sotto la propria licenza (LGPL/GPL): vedi
<https://ffmpeg.org/legal.html>.
