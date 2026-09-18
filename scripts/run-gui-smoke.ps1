param([switch]$SkipDependencyInstall)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$requirements = Join-Path $root 'tests\windows\requirements-gui-smoke.txt'
$test = Join-Path $root 'tests\windows\hosted_tray_uia_smoke.py'
$exe = Join-Path $root 'dist\SPRIME-PM1-Battery-Tray\SPRIME-PM1-Battery-Tray.exe'

if (-not [Environment]::UserInteractive) {
    throw 'Windows GUI smoke requires a logged-in interactive desktop session.'
}

if (-not (Test-Path $python)) {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -ne $py) {
        & $py.Source -3 -m venv (Join-Path $root '.venv')
    } else {
        $systemPython = Get-Command python.exe -ErrorAction Stop
        & $systemPython.Source -m venv (Join-Path $root '.venv')
    }
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create the Python virtual environment.' }
}

if (-not $SkipDependencyInstall) {
    & $python -m pip install --disable-pip-version-check --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'Failed to update pip.' }
    & $python -m pip install --disable-pip-version-check -r (Join-Path $root 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Failed to install application dependencies.' }
    & $python -m pip install --disable-pip-version-check -r $requirements
    if ($LASTEXITCODE -ne 0) { throw 'Failed to install GUI smoke dependencies.' }
}

Push-Location $root
try {
    & (Join-Path $root 'scripts\build.ps1')
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $exe)) {
        throw 'The packaged Mouse-Battery-Tray.exe was not built.'
    }

    $env:GUI_SMOKE_EXE = $exe
    & $python $test
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
