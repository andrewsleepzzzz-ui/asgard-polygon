$ErrorActionPreference = 'Continue'
$log = 'F:\dsh\32\Asgard_Polygon-main\kdmapper.log'
"=== run as admin=$([bool]([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) ===" | Out-File $log -Encoding utf8
& reg.exe add "HKLM\SYSTEM\CurrentControlSet\Control\CI\Config" /v VulnerableDriverBlocklistEnable /t REG_DWORD /d 0 /f 2>&1 | Out-File $log -Append -Encoding utf8
"=== kdmapper ===" | Out-File $log -Append -Encoding utf8
& "F:\dsh\kdmapper-master\x64\Release\kdmapper.exe" "F:\dsh\32\Asgard_Polygon-main\Asgard_Polygon\Asgard_Polygon\Kernel\PolygonMemory.sys" 2>&1 | Out-File $log -Append -Encoding utf8
"=== done exit=$LASTEXITCODE ===" | Out-File $log -Append -Encoding utf8
