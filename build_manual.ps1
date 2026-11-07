param()
$root = 'F:\dsh\32\Asgard_Polygon-main\Asgard_Polygon\Asgard_Polygon'
$msvc = 'E:\c_+\VC\Tools\MSVC\14.44.35207'
$sdk  = 'E:\Windows Kits\10'
$ver  = '10.0.26100.0'
$cl = "$msvc\bin\Hostx64\x64\cl.exe"
$outdir = 'F:\dsh\32\Asgard_Polygon-main\Asgard_Polygon\x64\Release'
New-Item -ItemType Directory -Force -Path $outdir | Out-Null
$srcs = Get-ChildItem "$root\src" -Recurse -Filter *.cpp | ForEach-Object { $_.FullName }
Write-Host ("sources: " + $srcs.Count)

$cmd = '"' + $cl + '" /nologo /EHsc /O2 /std:c++20 /MD /utf-8 /D_AMD64_ /DUNICODE /D_UNICODE'
$cmd += ' /I"' + $root + '\src"'
$cmd += ' /I"' + $msvc + '\include"'
$cmd += ' /I"' + $sdk + '\Include\' + $ver + '\ucrt"'
$cmd += ' /I"' + $sdk + '\Include\' + $ver + '\um"'
$cmd += ' /I"' + $sdk + '\Include\' + $ver + '\shared"'
foreach ($s in $srcs) { $cmd += ' "' + $s + '"' }
$cmd += ' /link /OUT:"' + $outdir + '\Asgard_Polygon.exe" /SUBSYSTEM:CONSOLE'
$cmd += ' /LIBPATH:"' + $msvc + '\lib\x64"'
$cmd += ' /LIBPATH:"' + $sdk + '\Lib\' + $ver + '\ucrt\x64"'
$cmd += ' /LIBPATH:"' + $sdk + '\Lib\' + $ver + '\um\x64"'
$cmd += ' d3d9.lib dwmapi.lib user32.lib gdi32.lib shell32.lib psapi.lib winmm.lib version.lib ole32.lib oleaut32.lib advapi32.lib'

cmd.exe /c $cmd 2>&1 | Select-Object -Last 40
Write-Host ("exit=" + $LASTEXITCODE)
