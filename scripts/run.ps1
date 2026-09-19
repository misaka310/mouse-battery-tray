$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonw = Join-Path $repoRoot ".venv\Scripts\pythonw.exe"
if (-not (Test-Path -LiteralPath $pythonw -PathType Leaf)) {
    throw "pythonw.exe was not found. Run scripts\setup.ps1 first."
}

$env:PYTHONPATH = Join-Path $repoRoot "src"
Push-Location $repoRoot
try {
    & $pythonw -m mouse_battery_tray
}
finally {
    Pop-Location
}
