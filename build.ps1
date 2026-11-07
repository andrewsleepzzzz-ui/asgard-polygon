param(
    [string]$VsRoot = 'E:\c_+',
    [string]$KitsRoot = 'E:\Windows Kits\10'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Join-Path $PSScriptRoot 'Asgard_Polygon\Asgard_Polygon'
$solution = Join-Path $PSScriptRoot 'Asgard_Polygon\Asgard_Polygon.sln'
$kernel = Join-Path $projectRoot 'Kernel'
$msvc = Join-Path $VsRoot 'VC\Tools\MSVC\14.44.35207'
$msbuild = Join-Path $VsRoot 'MSBuild\Current\Bin\MSBuild.exe'
$compiler = Join-Path $msvc 'bin\Hostx64\x64\cl.exe'
$linker = Join-Path $msvc 'bin\Hostx64\x64\link.exe'
$wdk = Join-Path $KitsRoot 'Include\10.0.22621.0\km'
$shared = Join-Path $KitsRoot 'Include\10.0.26100.0\shared'
$lib = Join-Path $KitsRoot 'Lib\10.0.22621.0\km\x64'
$object = Join-Path $kernel 'driver.obj'
$driver = Join-Path $kernel 'PolygonMemory.sys'

foreach ($path in @($msbuild, $compiler, $linker, $wdk, $shared, $lib)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing build dependency: $path"
    }
}

& $msbuild $solution /p:Configuration=Release /p:Platform=x64 "/p:WindowsSdkDir=$KitsRoot\" /p:WindowsTargetPlatformVersion=10.0.26100.0 /p:WindowsSDKInstalled=true /p:WindowsSDK_Desktop_Support=true /m:2 /v:minimal /nologo
if ($LASTEXITCODE -ne 0) { throw "User application build failed: $LASTEXITCODE" }

$compileArgs = @(
    '/nologo', '/c', '/TC', '/kernel', '/O2', '/GS-', '/W4',
    '/D_AMD64_', '/DAMD64', '/D_WIN64', '/D_WIN32_WINNT=0x0A00',
    "/I$wdk", "/I$(Join-Path $wdk 'crt')", "/I$shared",
    "/I$(Join-Path $msvc 'include')",
    "/Fo$object", (Join-Path $kernel 'driver.c')
)
& $compiler @compileArgs
if ($LASTEXITCODE -ne 0) { throw "Kernel compilation failed: $LASTEXITCODE" }

$linkArgs = @(
    '/nologo', '/driver', '/subsystem:native', '/entry:DriverEntry',
    '/nodefaultlib', '/machine:x64', "/out:$driver", "/libpath:$lib",
    $object, 'ntoskrnl.lib', 'hal.lib', 'wdmsec.lib', 'bufferoverflowfastfailk.lib'
)
& $linker @linkArgs
if ($LASTEXITCODE -ne 0) { throw "Kernel link failed: $LASTEXITCODE" }

Write-Host "Built: $(Join-Path $PSScriptRoot 'Asgard_Polygon\x64\Release\Asgard_Polygon.exe')"
Write-Host "Built: $driver"
