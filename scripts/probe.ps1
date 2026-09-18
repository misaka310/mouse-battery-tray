# scripts/probe.ps1
$ErrorActionPreference = "Stop"

Write-Host "Probing HID devices..." -ForegroundColor Cyan

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = ".\.venv\Scripts\python"
}

# Add src to PYTHONPATH
$env:PYTHONPATH = "src"

& $python src/mouse_battery_tray/hid_scan.py

Write-Host "Probe complete. Logs saved in logs/ directory." -ForegroundColor Green
