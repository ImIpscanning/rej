@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    start "REJ Desktop" pyw -3 -m rej gui
) else (
    where pythonw >nul 2>nul
    if %errorlevel%==0 (
        start "REJ Desktop" pythonw -m rej gui
    ) else (
        echo Python 3.11+ with Tkinter required.
        echo https://www.python.org/downloads/windows/
        pause
    )
)
