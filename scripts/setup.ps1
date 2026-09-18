# scripts/setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "Setting up Python virtual environment..." -ForegroundColor Cyan

function Resolve-Python {
    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        return $launcher.Source
    }

    $localPythonRoot = Join-Path $env:LOCALAPPDATA "Programs\Python"
    if (Test-Path $localPythonRoot) {
        $candidate = Get-ChildItem -Path $localPythonRoot -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "\\.venv\\" } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($candidate) {
            return $candidate.FullName
        }
    }

    throw "Python was not found. Install Python 3.10+ or add python.exe to PATH."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    $python = Resolve-Python
    if ([System.IO.Path]::GetFileName($python) -ieq "py.exe") {
        & $python -3 -m venv .venv
    }
    else {
        & $python -m venv .venv
    }
}

$venvPython = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python was not created: $venvPython"
}

Write-Host "Installing dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

Write-Host "Setup complete." -ForegroundColor Green
