$log = 'F:\dsh\32\Asgard_Polygon-main\sdk_fix.log'
"=== fix sdk root ===" | Out-File $log -Encoding utf8
& reg.exe add "HKLM\SOFTWARE\Microsoft\Windows Kits\Installed Roots" /v KitsRoot10 /t REG_SZ /d "E:\Windows Kits\10\" /f 2>&1 | Out-File $log -Append -Encoding utf8
(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows Kits\Installed Roots').KitsRoot10 | Out-File $log -Append -Encoding utf8
"=== done ===" | Out-File $log -Append -Encoding utf8
