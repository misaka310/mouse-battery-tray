# scripts/setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "Setting up Python virtual environment..." -ForegroundColor Cyan

function Remove-DirectoryWithRetry {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [int]$Retries = 5
    )

    for ($attempt = 1; $attempt -le $Retries; $attempt++) {
        if (-not (Test-Path -LiteralPath $Path)) {
            return
        }

        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            return
        }
        catch {
            if ($attempt -lt $Retries) {
                Start-Sleep -Milliseconds 500
            }
        }
    }

    if (Test-Path -LiteralPath $Path) {
        $quotedPath = '"' + [System.IO.Path]::GetFullPath($Path) + '"'
        $process = Start-Process -FilePath "cmd.exe" -ArgumentList @("/d", "/c", "rd /s /q $quotedPath") -NoNewWindow -Wait -PassThru
        if ($process.ExitCode -ne 0 -or (Test-Path -LiteralPath $Path)) {
            throw "Failed to remove stale virtual environment: $Path"
        }
    }
}

function Get-PythonHome {
    param([Parameter(Mandatory = $true)][string]$Executable)

    $scriptsDir = Split-Path -Parent $Executable
    if ((Split-Path -Leaf $scriptsDir) -ieq "Scripts") {
        $venvRoot = Split-Path -Parent $scriptsDir
        $configPath = Join-Path $venvRoot "pyvenv.cfg"
        if (Test-Path $configPath) {
            $homeLine = Get-Content -LiteralPath $configPath |
                Where-Object { $_ -match "^home\s*=" } |
                Select-Object -First 1
            if ($homeLine) {
                return ($homeLine -replace "^home\s*=\s*", "").Trim()
            }
        }
    }

    return Split-Path -Parent $Executable
}

function Test-PythonRuntime {
    param([Parameter(Mandatory = $true)][string]$Executable)

    if (-not (Test-Path -LiteralPath $Executable)) {
        return $false
    }

    try {
        $version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($Executable)
        if ($version.FileMajorPart -lt 3 -or ($version.FileMajorPart -eq 3 -and $version.FileMinorPart -lt 10)) {
            return $false
        }

        $pythonHome = Get-PythonHome -Executable $Executable
        $tkinterInit = Join-Path $pythonHome "Lib\tkinter\__init__.py"
        return Test-Path -LiteralPath $tkinterInit
    }
    catch {
        return $false
    }
}

function Resolve-Python {
    $candidatePaths = @()

    $pathPython = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pathPython -and $pathPython.Source -and $pathPython.Source -notmatch "\\WindowsApps\\") {
        $candidatePaths += $pathPython.Source
    }

    $localPythonRoot = Join-Path $env:LOCALAPPDATA "Programs\Python"
    if (Test-Path $localPythonRoot) {
        $candidatePaths += Get-ChildItem -Path $localPythonRoot -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch "\\.venv\\" -and
                $_.FullName -notmatch "\\WindowsApps\\"
            } |
            Sort-Object FullName -Descending |
            Select-Object -ExpandProperty FullName
    }

    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher -and $launcher.Source) {
        $launchedPython = & $launcher.Source -3 -c "import sys; print(sys.executable)" 2>$null
        if ($launchedPython) {
            $candidatePaths += $launchedPython.Trim()
        }
    }

    foreach ($candidate in $candidatePaths | Select-Object -Unique) {
        if (Test-PythonRuntime -Executable $candidate) {
            return $candidate
        }
    }

    throw "Python 3.10+ with Tkinter was not found. Install the standard Windows Python distribution with Tcl/Tk support."
}

function Invoke-ProcessChecked {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $process = Start-Process -FilePath $Executable -ArgumentList $Arguments -NoNewWindow -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "$Executable failed with exit code $($process.ExitCode)."
    }
}

$venvDir = ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (Test-Path $venvPython) {
    if (-not (Test-PythonRuntime -Executable $venvPython)) {
        Write-Host "Existing .venv does not provide a usable Tkinter runtime; rebuilding it..." -ForegroundColor Yellow
        Remove-DirectoryWithRetry -Path $venvDir
    }
}

if (-not (Test-Path $venvPython)) {
    $python = Resolve-Python
    Write-Host "Using Python: $python" -ForegroundColor DarkGray
    Invoke-ProcessChecked -Executable $python -Arguments @("-m", "venv", $venvDir)
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python was not created: $venvPython"
}

Write-Host "Installing dependencies..." -ForegroundColor Cyan
Invoke-ProcessChecked -Executable $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-ProcessChecked -Executable $venvPython -Arguments @("-m", "pip", "install", "-r", "requirements.txt")

Write-Host "Setup complete." -ForegroundColor Green
