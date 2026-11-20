#requires -Version 7.2
param(
    [string]$KitRoot = $env:GameDKCoreLatest,
    [string]$Cache = (Join-Path $env:LOCALAPPDATA 'ProjectNative/gdk')
)
$ErrorActionPreference = 'Stop'
$revision = 'b1e77b6ac10f95b07296025fda171ca2ddc42dbe'
$remote = 'https://github.com/microsoft/Xbox-GDK-Samples.git'
$repo = Join-Path $Cache 'samples'
if (!$KitRoot) { $KitRoot = Join-Path $Cache 'kit/Microsoft GDK/261000' }
if (!(Test-Path (Join-Path $KitRoot 'windows/include/grdk.h'))) {
    throw 'Supply -KitRoot pointing to the extracted or installed GDK edition directory.'
}
$env:GameDKCoreLatest = (Resolve-Path $KitRoot).Path.TrimEnd('\') + '\'
$env:GameDK = (Split-Path $env:GameDKCoreLatest.TrimEnd('\')) + '\'
$env:Path = (Join-Path (Split-Path $KitRoot.TrimEnd('\')) 'bin') + ';' + $env:Path
$vswhere = "${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
$msbuild = & $vswhere -latest -products '*' -version '[17,18)' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -find 'MSBuild\Current\Bin\amd64\MSBuild.exe' | Select-Object -First 1
if (!$msbuild) { throw 'Visual Studio 2022 MSBuild and x64 C++ tools are required.' }

function Invoke-Checked($Program, [string[]]$Arguments) {
    & $Program @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}

if (!(Test-Path $repo)) {
    Invoke-Checked git @('clone', '--filter=blob:none', '--no-checkout', $remote, $repo)
}
if ((git -C $repo remote get-url origin) -ne $remote) { throw 'Unexpected sample remote.' }
if ((git -C $repo ls-files).Length -gt 0 -and (git -C $repo diff --name-only HEAD)) { throw 'Tracked sample files have local changes.' }
Invoke-Checked git @('-C', $repo, 'sparse-checkout', 'set', 'Samples/IntroGraphics/SimpleTriangleDesktop', 'Kits/DirectXTK12', 'Kits/ATGTK', 'Kits/ATGTelemetry')
Invoke-Checked git @('-C', $repo, 'checkout', '--detach', $revision)
$sample = Join-Path $repo 'Samples/IntroGraphics/SimpleTriangleDesktop'
$solution = Join-Path $sample 'SimpleTriangleDesktop.sln'
$config = @('/p:Configuration=Release', '/p:Platform=x64', '/v:minimal')
Invoke-Checked $msbuild (@($solution, '/t:Restore', '/p:RestorePackagesConfig=true') + $config)
$patch = Join-Path $PSScriptRoot 'capture.patch'
Invoke-Checked git @('-C', $repo, 'apply', '--unidiff-zero', $patch)
try {
    Invoke-Checked $msbuild (@($solution, '/m:4') + $config)
} finally {
    Invoke-Checked git @('-C', $repo, 'apply', '-R', '--unidiff-zero', $patch)
}
