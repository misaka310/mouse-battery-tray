# Reset Mouse Battery Tray configuration to defaults
$configDir = Join-Path $env:APPDATA "MouseBatteryTray"
$configFile = Join-Path $configDir "config.json"

if (Test-Path $configFile) {
    Write-Host "Removing existing configuration at $configFile" -ForegroundColor Yellow
    Remove-Item $configFile -Force
    Write-Host "Configuration reset successfully. Next start will use default settings." -ForegroundColor Green
}
else {
    Write-Host "Configuration file not found. Nothing to reset." -ForegroundColor Cyan
}
