param()
$ErrorActionPreference = 'Stop'
$VsRoot = 'E:\c_+'
$KitsRoot = 'E:\Windows Kits\10'
$kernel = 'F:\dsh\32\Asgard_Polygon-main\Asgard_Polygon\Asgard_Polygon\Kernel'
$msvc = Join-Path $VsRoot 'VC\Tools\MSVC\14.44.35207'
$compiler = Join-Path $msvc 'bin\Hostx64\x64\cl.exe'
$linker = Join-Path $msvc 'bin\Hostx64\x64\link.exe'
$wdk = Join-Path $KitsRoot 'Include\10.0.22621.0\km'
$shared = Join-Path $KitsRoot 'Include\10.0.26100.0\shared'
$lib = Join-Path $KitsRoot 'Lib\10.0.22621.0\km\x64'
$object = Join-Path $kernel 'driver.obj'
$driver = Join-Path $kernel 'PolygonMemory.sys'

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
Get-Item $driver | Select-Object Length,LastWriteTime | Format-List
