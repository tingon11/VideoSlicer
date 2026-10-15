@echo off
rem Avvia VideoSlicer senza finestra console.
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "VideoSlicer.py"
) else (
    start "" pythonw "VideoSlicer.py"
)
