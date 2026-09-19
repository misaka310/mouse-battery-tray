param(
    [Parameter(Mandatory=$true)][string]$ArtifactDirectory,
    [Parameter(Mandatory=$true)][string]$TargetId,
    [Parameter(Mandatory=$true)][string]$TargetRef,
    [Parameter(Mandatory=$true)][string]$ResolvedCommitSha
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-True {
    param([bool]$Condition,[string]$Name)
    if (-not $Condition) { throw "FAIL $Name" }
}

function Wait-SettingsWindow {
    param(
        [Parameter(Mandatory=$true)][Diagnostics.Process]$Process,
        [int]$TimeoutSeconds = 25
    )

    Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class WindowProbe {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
}
"@

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        if ($Process.HasExited) { throw 'Mouse Battery Tray exited before Settings became visible' }
        $found = $false
        [WindowProbe]::EnumWindows({
            param($hWnd,$lParam)
            if (-not [WindowProbe]::IsWindowVisible($hWnd)) { return $true }
            $pidValue = [uint32]0
            [void][WindowProbe]::GetWindowThreadProcessId($hWnd,[ref]$pidValue)
            if ([int]$pidValue -ne $Process.Id) { return $true }
            $builder = [Text.StringBuilder]::new(512)
            [void][WindowProbe]::GetWindowText($hWnd,$builder,$builder.Capacity)
            if ($builder.ToString() -eq 'Mouse Battery Tray Settings') {
                $script:settingsHwnd = $hWnd
                $found = $true
                return $false
            }
            return $true
        },[IntPtr]::Zero) | Out-Null
        if ($found -or $null -ne $script:settingsHwnd) { return $script:settingsHwnd }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)

    throw 'Mouse Battery Tray Settings window did not become visible'
}

function Save-DesktopScreenshot {
    param([Parameter(Mandatory=$true)][string]$Path)
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap $bounds.Width,$bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try { $graphics.CopyFromScreen($bounds.Location,[System.Drawing.Point]::Empty,$bounds.Size) }
    finally { $graphics.Dispose() }
    try { $bitmap.Save($Path,[System.Drawing.Imaging.ImageFormat]::Png) }
    finally { $bitmap.Dispose() }
}

if ($TargetId -ne 'mouse-battery-tray') { throw "unexpected target id: $TargetId" }
if ($ResolvedCommitSha -notmatch '^[a-fA-F0-9]{40}$') { throw 'ResolvedCommitSha is invalid' }

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
[IO.Directory]::CreateDirectory($ArtifactDirectory) | Out-Null
$resultPath = Join-Path $ArtifactDirectory 'result.json'
$screenshotPath = Join-Path $ArtifactDirectory 'screenshot.png'
$evidencePath = Join-Path $ArtifactDirectory 'mouse-battery-evidence.json'
$stdoutPath = Join-Path $ArtifactDirectory 'stdout.log'
$stderrPath = Join-Path $ArtifactDirectory 'stderr.log'
$logPath = Join-Path $ArtifactDirectory 'target.log'
Set-Content -LiteralPath $stdoutPath -Value '' -Encoding UTF8
Set-Content -LiteralPath $stderrPath -Value '' -Encoding UTF8

$started = [DateTime]::UtcNow
$appProcess = $null
$script:settingsHwnd = $null

try {
    Push-Location $repoRoot
    try {
        & (Join-Path $repoRoot 'scripts\setup.ps1') *> $logPath
        & (Join-Path $repoRoot 'scripts\build.ps1') *>> $logPath
    }
    finally {
        Pop-Location
    }

    $exePath = Join-Path $repoRoot 'dist\Mouse-Battery-Tray\Mouse-Battery-Tray.exe'
    Assert-True (Test-Path -LiteralPath $exePath -PathType Leaf) 'packaged exe exists'

    $smoke = Start-Process -FilePath $exePath -ArgumentList '--smoke-test' -WorkingDirectory (Split-Path -Parent $exePath) -Wait -PassThru
    Assert-True ($smoke.ExitCode -eq 0) 'packaged smoke test'

    $appProcess = Start-Process -FilePath $exePath -ArgumentList '--show-settings' -WorkingDirectory (Split-Path -Parent $exePath) -PassThru
    $settingsHwnd = Wait-SettingsWindow -Process $appProcess
    Start-Sleep -Milliseconds 500

    $duplicate = Start-Process -FilePath $exePath -WorkingDirectory (Split-Path -Parent $exePath) -PassThru
    [void]$duplicate.WaitForExit(10000)
    $matching = @(Get-Process -Name 'Mouse-Battery-Tray' -ErrorAction SilentlyContinue)
    Assert-True ($matching.Count -eq 1) 'single instance after duplicate launch'
    Assert-True (-not $appProcess.HasExited) 'primary tray process remains running'

    Save-DesktopScreenshot -Path $screenshotPath

    $evidence = [ordered]@{
        settingsWindowVisible = $true
        settingsWindowHandle = [int64]$settingsHwnd
        primaryProcessAlive = (-not $appProcess.HasExited)
        processCount = $matching.Count
        duplicateExited = $duplicate.HasExited
        packagedSmokeExitCode = $smoke.ExitCode
        inputInjectionUsed = $false
    }
    $evidence | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $evidencePath -Encoding UTF8

    $result = [ordered]@{
        status = 'PASS'
        targetId = $TargetId
        requestedRef = $TargetRef
        resolvedCommitSha = $ResolvedCommitSha.ToLowerInvariant()
        executableSha256 = (Get-FileHash -LiteralPath $exePath -Algorithm SHA256).Hash.ToLowerInvariant()
        startTimestamp = $started.ToString('o')
        endTimestamp = [DateTime]::UtcNow.ToString('o')
        interactiveSessionId = [int]$appProcess.SessionId
        guiProcessId = [int]$appProcess.Id
        screenshot = 'screenshot.png'
        evidence = 'mouse-battery-evidence.json'
        stdout = 'stdout.log'
        stderr = 'stderr.log'
        log = 'target.log'
    }
    $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Output ("PASS Hyper-V GUI CI artifact={0}" -f $ArtifactDirectory)
}
finally {
    if ($null -ne $appProcess -and -not $appProcess.HasExited) {
        Stop-Process -Id $appProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
