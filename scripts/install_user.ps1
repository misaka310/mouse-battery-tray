param(
    [switch]$EnableStartup
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$AppName = "Mouse-Battery-Tray"
$DisplayName = "Mouse Battery Tray"
$SourceDir = Join-Path $RepoRoot "dist\$AppName"
$SourceExe = Join-Path $SourceDir "$AppName.exe"

if (-not (Test-Path -LiteralPath $SourceExe)) {
    throw "Built application not found: $SourceExe. Run scripts/build.ps1 first."
}

$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\Mouse Battery Tray"
$InstallExe = Join-Path $InstallDir "$AppName.exe"

foreach ($ProcessName in @("Mouse-Battery-Tray", "SPRIME-PM1-Battery-Tray")) {
    $Running = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($Running) {
        $Running | Stop-Process -Force
        Start-Sleep -Milliseconds 500
    }
}

if (Test-Path -LiteralPath $InstallDir) {
    Remove-Item -LiteralPath $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Copy-Item -Path (Join-Path $SourceDir "*") -Destination $InstallDir -Recurse -Force

$ProgramsDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$StartMenuShortcut = Join-Path $ProgramsDir "$DisplayName.lnk"
$LegacyStartMenuShortcut = Join-Path $ProgramsDir "SPRIME PM1 Battery Tray.lnk"
$LegacyStartupShortcut = Join-Path $ProgramsDir "Startup\SPRIME PM1 Battery Tray.lnk"

New-Item -ItemType Directory -Path $ProgramsDir -Force | Out-Null

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($StartMenuShortcut)
$Shortcut.TargetPath = $InstallExe
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.IconLocation = "$InstallExe,0"
$Shortcut.Description = "Wireless mouse battery tray monitor"
$Shortcut.Save()

Remove-Item -LiteralPath $LegacyStartMenuShortcut -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $LegacyStartupShortcut -Force -ErrorAction SilentlyContinue

$ConfigDir = Join-Path $env:APPDATA "MouseBatteryTray"
$ConfigPath = Join-Path $ConfigDir "config.json"
$LegacyConfigPath = Join-Path $env:APPDATA "SprimePM1BatteryTray\config.json"
$StartOnBoot = $false
$Config = $null

foreach ($Candidate in @($ConfigPath, $LegacyConfigPath)) {
    if (Test-Path -LiteralPath $Candidate) {
        try {
            $Config = Get-Content -LiteralPath $Candidate -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($null -ne $Config.start_on_boot) {
                $StartOnBoot = [bool]$Config.start_on_boot
            }
            break
        }
        catch {
            Write-Warning "Existing config could not be read from $Candidate."
        }
    }
}

if ($EnableStartup) {
    $StartOnBoot = $true
}

New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
if ($null -eq $Config) {
    $Config = [pscustomobject]@{}
}
if ($Config.PSObject.Properties.Name -contains "start_on_boot") {
    $Config.start_on_boot = $StartOnBoot
}
else {
    $Config | Add-Member -NotePropertyName "start_on_boot" -NotePropertyValue $StartOnBoot
}
if ($Config.PSObject.Properties.Name -contains "config_version") {
    $Config.config_version = 4
}
else {
    $Config | Add-Member -NotePropertyName "config_version" -NotePropertyValue 4
}
$ConfigJson = $Config | ConvertTo-Json -Depth 10
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($ConfigPath, $ConfigJson, $Utf8NoBom)

$RunKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
if ($StartOnBoot) {
    Set-ItemProperty -Path $RunKey -Name $DisplayName -Value ('"' + $InstallExe + '"')
}
else {
    Remove-ItemProperty -Path $RunKey -Name $DisplayName -ErrorAction SilentlyContinue
}
Remove-ItemProperty -Path $RunKey -Name "SPRIME PM1 Battery Tray" -ErrorAction SilentlyContinue

Write-Output "INSTALL_EXE=$InstallExe"
Write-Output "START_MENU_SHORTCUT=$StartMenuShortcut"
Write-Output "STARTUP_ENABLED=$StartOnBoot"
