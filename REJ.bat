@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -m rej menu
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        python -m rej menu
    ) else (
        echo Python 3.11 or newer is required.
        echo Install Python from https://www.python.org/downloads/windows/
    )
)
echo.
pause
