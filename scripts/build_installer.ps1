$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$CompilerCandidates = @(
    (Join-Path $ProjectRoot ".cache\inno-setup\ISCC.exe"),
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$Compiler = $CompilerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $Compiler) {
    throw "Inno Setup compiler not found. Install Inno Setup 6 or place its portable files in .cache\inno-setup."
}

$PortableExe = Join-Path $ProjectRoot "dist\ScreenOCR\ScreenOCR.exe"
if (-not (Test-Path -LiteralPath $PortableExe)) {
    throw "Portable build not found. Run scripts\build_portable.ps1 first."
}

& $Compiler (Join-Path $PSScriptRoot "screen_ocr.iss")
if ($LASTEXITCODE -ne 0) {
    throw "Installer build failed with exit code $LASTEXITCODE."
}

Write-Host "Installer build: $ProjectRoot\dist\installer\ScreenOCR-Setup-0.1.0.exe"
