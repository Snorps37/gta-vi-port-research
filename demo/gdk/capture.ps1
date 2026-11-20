#requires -Version 7.4
param(
    [string]$Cache = (Join-Path $env:LOCALAPPDATA 'ProjectNative/gdk'),
    [string]$Output = (Join-Path $PSScriptRoot '../../docs/gdk-first-frame.png')
)
$ErrorActionPreference = 'Stop'
$release = Join-Path $Cache 'samples/Samples/IntroGraphics/SimpleTriangleDesktop/x64/Release'
$tempFrame = Join-Path $Cache ("frame-{0}.png" -f [guid]::NewGuid())
$process = Start-Process (Join-Path $release 'SimpleTriangleDesktop.exe') -WorkingDirectory $release -Environment @{NATIVE_FRAME_PNG=$tempFrame} -PassThru
try {
    $deadline = [datetime]::UtcNow.AddSeconds(30)
    do {
        if ($process.HasExited) { throw "Sample exited before capture ($($process.ExitCode))." }
        Start-Sleep -Milliseconds 150
        $process.Refresh()
    } until (((Test-Path $tempFrame) -and $process.MainWindowHandle) -or [datetime]::UtcNow -ge $deadline)
    if (!$process.MainWindowHandle -or !(Test-Path $tempFrame)) { throw 'Timed out waiting for the window and first frame.' }
    if (!$process.CloseMainWindow() -or !$process.WaitForExit(10000) -or $process.ExitCode -ne 0) {
        throw 'Sample failed to close cleanly.'
    }
    Add-Type -AssemblyName System.Drawing
    $image = [System.Drawing.Bitmap]::new($tempFrame)
    try {
        # Check the red top, green lower-right and blue lower-left inside the triangle.
        foreach ($probe in @(@(.50,.35,'R'), @(.65,.68,'G'), @(.35,.68,'B'))) {
            $pixel = $image.GetPixel([int]($image.Width*$probe[0]), [int]($image.Height*$probe[1]))
            $channel = $probe[2]
            foreach ($other in 'R','G','B') {
                if ($other -ne $channel -and $pixel.$channel -lt $pixel.$other + 40) {
                    throw "Unexpected $channel vertex color at $($probe[0]), $($probe[1]): $pixel"
                }
            }
        }
        Write-Host "Validated $($image.Width) x $($image.Height) frame and exit code 0."
    } finally { $image.Dispose() }
    Copy-Item -LiteralPath $tempFrame -Destination $Output -Force
} finally {
    if (!$process.HasExited) { $process.Kill(); $process.WaitForExit() }
    $process.Dispose()
    if (Test-Path $tempFrame) { Remove-Item -LiteralPath $tempFrame }
}
