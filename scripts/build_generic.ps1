$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Set-Location $repoRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Virtual-environment Python was not found: $python" }

$appDir = Join-Path $repoRoot "mouse_battery_tray"
$entry = Join-Path $appDir "battery_tray.pyw"
$dist = Join-Path $repoRoot "dist\Mouse-Battery-Tray"
$buildDir = Join-Path $repoRoot "build\Mouse-Battery-Tray"
$spec = Join-Path $repoRoot "Mouse-Battery-Tray.spec"

Remove-Item $dist -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $buildDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $spec -Force -ErrorAction SilentlyContinue

& $python -m PyInstaller --noconfirm --onedir --windowed --name "Mouse-Battery-Tray" --paths $appDir $entry
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed with exit code $LASTEXITCODE" }

$exe = Join-Path $dist "Mouse-Battery-Tray.exe"
if (-not (Test-Path $exe)) { throw "EXE not generated: $exe" }
Write-Host "Built: $exe"
