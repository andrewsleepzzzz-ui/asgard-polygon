$ErrorActionPreference = 'Continue'
$log = 'F:\dsh\32\Asgard_Polygon-main\kdmapper.log'
"=== stop EAC + kdmapper (admin=$([bool]([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))) ===" | Out-File $log -Encoding utf8
"--- sc stop EasyAntiCheat_EOS ---" | Out-File $log -Append -Encoding utf8
& sc.exe stop EasyAntiCheat_EOS 2>&1 | Out-File $log -Append -Encoding utf8
"--- taskkill EAC ---" | Out-File $log -Append -Encoding utf8
& taskkill.exe /f /im EasyAntiCheat_EOS.exe 2>&1 | Out-File $log -Append -Encoding utf8
Start-Sleep -Seconds 2
"--- EAC procs after ---" | Out-File $log -Append -Encoding utf8
(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match 'EasyAnti' } | Select-Object -ExpandProperty ProcessName) | Out-File $log -Append -Encoding utf8
"--- kdmapper ---" | Out-File $log -Append -Encoding utf8
& "F:\dsh\kdmapper-master\x64\Release\kdmapper.exe" "F:\dsh\32\Asgard_Polygon-main\Asgard_Polygon\Asgard_Polygon\Kernel\PolygonMemory.sys" 2>&1 | Out-File $log -Append -Encoding utf8
"--- done exit=$LASTEXITCODE ---" | Out-File $log -Append -Encoding utf8
