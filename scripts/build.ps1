# scripts/build.ps1
$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Set-Location $repoRoot

Write-Host "Building EXE with PyInstaller..." -ForegroundColor Cyan

$python = [System.IO.Path]::GetFullPath((Join-Path $repoRoot ".venv\Scripts\python.exe"))
if (-not (Test-Path $python)) {
    throw "Virtual-environment Python was not found: $python"
}

$appName = "Mouse-Battery-Tray"
$distDir = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "dist\$appName"))
$buildDir = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "build\$appName"))
$specFile = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "$appName.spec"))
$srcDir = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "src"))
$entryPoint = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "pyinstaller_entry.py"))

function Stop-ExistingApp {
    $processes = Get-Process -Name $appName -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "Stopping running $appName process before build..." -ForegroundColor Yellow
        $processes | Stop-Process -Force
        Start-Sleep -Seconds 1
    }
}

function Remove-PathWithRetry {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [int]$Retries = 5
    )

    if (-not (Test-Path $Path)) {
        return
    }

    for ($i = 1; $i -le $Retries; $i++) {
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            return
        } catch {
            if ($i -eq $Retries) {
                throw "Failed to remove '$Path'. Close any running app/window or Explorer preview using it, then retry. Original error: $($_.Exception.Message)"
            }
            Write-Host "Retrying cleanup for $Path ($i/$Retries)..." -ForegroundColor Yellow
            Start-Sleep -Seconds 1
        }
    }
}

Stop-ExistingApp
Remove-PathWithRetry -Path $distDir
Remove-PathWithRetry -Path $buildDir
Remove-PathWithRetry -Path $specFile

$env:PYTHONPATH = $srcDir
$arguments = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name", $appName,
    "--paths", $srcDir,
    "--add-data", "$srcDir\mouse_battery_tray;mouse_battery_tray/",
    "--collect-all", "customtkinter",
    $entryPoint
)
$build = Start-Process -FilePath $python -ArgumentList $arguments -NoNewWindow -Wait -PassThru
if ($build.ExitCode -ne 0) {
    throw "PyInstaller build failed with exit code $($build.ExitCode)."
}

$exePath = Join-Path $distDir "$appName.exe"
if (-not (Test-Path $exePath)) {
    throw "Build finished but EXE was not generated at expected path: $exePath"
}

Write-Host "Build complete. EXE is in dist\Mouse-Battery-Tray\" -ForegroundColor Green
