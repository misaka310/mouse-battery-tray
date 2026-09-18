# scripts/e2e.ps1
$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Set-Location $repoRoot

Write-Host "Running E2E tests..." -ForegroundColor Cyan

Write-Host "`n1. Running Setup..." -ForegroundColor Cyan
.\scripts\setup.ps1

$python = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ".venv\Scripts\python.exe"))
if (-not (Test-Path $python)) {
    $python = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ".venv\Scripts\python"))
}
if (-not (Test-Path $python)) {
    throw "Virtual-environment Python was not found: $python"
}

Write-Host "`n2. Running Unit Tests..." -ForegroundColor Cyan
$env:PYTHONPATH = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "src"))
$unitTests = Start-Process -FilePath $python -ArgumentList @("-m", "pytest", "tests/") -NoNewWindow -Wait -PassThru
if ($unitTests.ExitCode -ne 0) {
    throw "Unit tests failed with exit code $($unitTests.ExitCode)!"
}

Write-Host "`n3. Testing HID Protocol (Real Device Battery Read)..." -ForegroundColor Cyan
$deviceCheck = Start-Process -FilePath $python -ArgumentList @("scripts/check_real_device.py") -NoNewWindow -Wait -PassThru
if ($deviceCheck.ExitCode -ne 0) {
    throw "Real device HID check failed with exit code $($deviceCheck.ExitCode)!"
}

Write-Host "`n4. Building EXE..." -ForegroundColor Cyan
.\scripts\build.ps1

$exePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "dist\Mouse-Battery-Tray\Mouse-Battery-Tray.exe"))
Write-Host "`n5. Checking EXE existence at $exePath..." -ForegroundColor Cyan
if (-not (Test-Path $exePath)) {
    throw "EXE was not generated at expected path: $exePath"
}

Write-Host "`n6. Running Smoke Test on built EXE..." -ForegroundColor Cyan
$smoke = Start-Process -FilePath $exePath -ArgumentList @("--smoke-test") -NoNewWindow -Wait -PassThru
if ($smoke.ExitCode -eq 0) {
    Write-Host "Smoke test passed!" -ForegroundColor Green
} else {
    throw "Smoke test failed with exit code $($smoke.ExitCode)!"
}

Write-Host "`nE2E complete! All steps passed." -ForegroundColor Green
