param()
$log = 'C:\gdrv_start.log'
"=== start gdrv3 ===" | Out-File $log -Encoding utf8
"admin=" + ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) | Out-File $log -Append -Encoding utf8
& sc.exe start gdrv3 2>&1 | Out-File $log -Append -Encoding utf8
& sc.exe query gdrv3 2>&1 | Out-File $log -Append -Encoding utf8
& sc.exe qc gdrv3 2>&1 | Out-File $log -Append -Encoding utf8
"=== done ===" | Out-File $log -Append -Encoding utf8
