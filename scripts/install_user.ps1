param(
    [switch]$EnableStartup
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SourceDir = Join-Path $RepoRoot "dist\Mouse-Battery-Tray"
$SourceExe = Join-Path $SourceDir "Mouse-Battery-Tray.exe"

if (-not (Test-Path -LiteralPath $SourceExe)) {
    throw "Built application not found: $SourceExe. Run scripts/build.ps1 first."
}

$AppName = "Mouse-Battery-Tray"
$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\Mouse Battery Tray"
$InstallExe = Join-Path $InstallDir "$AppName.exe"

$Running = Get-Process -Name $AppName -ErrorAction SilentlyContinue
if ($Running) {
    $Running | Stop-Process -Force
    Start-Sleep -Milliseconds 500
}

if (Test-Path -LiteralPath $InstallDir) {
    Remove-Item -LiteralPath $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Copy-Item -Path (Join-Path $SourceDir "*") -Destination $InstallDir -Recurse -Force

$ProgramsDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$StartMenuShortcut = Join-Path $ProgramsDir "Mouse Battery Tray.lnk"

New-Item -ItemType Directory -Path $ProgramsDir -Force | Out-Null

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($StartMenuShortcut)
$Shortcut.TargetPath = $InstallExe
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.IconLocation = "$InstallExe,0"
$Shortcut.Description = "Mouse battery monitor"
$Shortcut.Save()

$ConfigDir = Join-Path $env:APPDATA "MouseBatteryTray"
$ConfigPath = Join-Path $ConfigDir "config.json"
$LegacyConfigPath = Join-Path $env:APPDATA "SprimePM1BatteryTray\config.json"
$StartOnBoot = $false
$Config = $null

if (-not (Test-Path -LiteralPath $ConfigPath) -and (Test-Path -LiteralPath $LegacyConfigPath)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    Copy-Item -LiteralPath $LegacyConfigPath -Destination $ConfigPath
}

if (Test-Path -LiteralPath $ConfigPath) {
    try {
        $Config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -ne $Config.start_on_boot) {
            $StartOnBoot = [bool]$Config.start_on_boot
        }
    }
    catch {
        Write-Warning "Existing config could not be read; leaving startup disabled unless -EnableStartup is specified."
    }
}

if ($EnableStartup) {
    $StartOnBoot = $true
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    if ($null -eq $Config) {
        $Config = [pscustomobject]@{}
    }
    if ($Config.PSObject.Properties.Name -contains "start_on_boot") {
        $Config.start_on_boot = $true
    }
    else {
        $Config | Add-Member -NotePropertyName "start_on_boot" -NotePropertyValue $true
    }
    $ConfigJson = $Config | ConvertTo-Json -Depth 10
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($ConfigPath, $ConfigJson, $Utf8NoBom)
}

$RunKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
if (-not (Test-Path $RunKey)) {
    New-Item -Path $RunKey -Force | Out-Null
}
if ($StartOnBoot) {
    Set-ItemProperty -Path $RunKey -Name "MouseBatteryTray" -Value ('"' + $InstallExe + '"')
}
else {
    Remove-ItemProperty -Path $RunKey -Name "MouseBatteryTray" -ErrorAction SilentlyContinue
}
Remove-ItemProperty -Path $RunKey -Name "SPRIME PM1 Battery Tray" -ErrorAction SilentlyContinue

$LegacyStartup = Join-Path $ProgramsDir "Startup\SPRIME PM1 Battery Tray.lnk"
Remove-Item -LiteralPath $LegacyStartup -Force -ErrorAction SilentlyContinue

Write-Output "INSTALL_EXE=$InstallExe"
Write-Output "START_MENU_SHORTCUT=$StartMenuShortcut"
Write-Output "STARTUP_ENABLED=$StartOnBoot"
