$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$TestScript = Join-Path $PSScriptRoot "test.ps1"

function Invoke-CheckedPython {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    & $VenvPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    python -m venv (Join-Path $ProjectRoot ".venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to create the project virtual environment (exit code $LASTEXITCODE)."
    }
}

$RunningApp = Get-Process -Name "ScreenOCR" -ErrorAction SilentlyContinue
if ($RunningApp) {
    $ProcessIds = ($RunningApp.Id -join ", ")
    throw "ScreenOCR is running (process ID: $ProcessIds). Exit it before building so Windows can replace the portable files."
}

Invoke-CheckedPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-CheckedPython -Arguments @("-m", "pip", "install", "-e", "$ProjectRoot[dev]")
Invoke-CheckedPython -Arguments @((Join-Path $PSScriptRoot "prepare_models.py"))
& $TestScript
Invoke-CheckedPython -Arguments @(
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    (Join-Path $ProjectRoot "screen_ocr.spec")
)

Write-Host "Portable build: $ProjectRoot\dist\ScreenOCR"
