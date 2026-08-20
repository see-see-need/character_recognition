$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    python -m venv (Join-Path $ProjectRoot ".venv")
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e "$ProjectRoot[dev]"
& $VenvPython (Join-Path $PSScriptRoot "prepare_models.py")
& $VenvPython -m pytest
& $VenvPython -m PyInstaller --noconfirm --clean (Join-Path $ProjectRoot "screen_ocr.spec")

Write-Host "Portable build: $ProjectRoot\dist\ScreenOCR"

