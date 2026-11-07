# Build an unsigned Windows REJ Desktop executable using PyInstaller.
# Run on Windows, from the repository root. No downloaded JARs are executed.
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
python -m pip install --upgrade "pyinstaller==6.16.0"
if ($LASTEXITCODE -ne 0) { throw 'Failed installing PyInstaller' }
python -m PyInstaller --noconfirm --clean --onefile --windowed --name REJ-Desktop --collect-submodules tkinter rej_gui.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
Write-Host 'EXE ready: dist/REJ-Desktop.exe (unsigned; inspect it before distributing).'
