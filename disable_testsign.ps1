$log = 'F:\dsh\32\Asgard_Polygon-main\testsign.log'
"=== disable testsigning ===" | Out-File $log -Encoding utf8
& bcdedit.exe /set testsigning off 2>&1 | Out-File $log -Append -Encoding utf8
& bcdedit.exe /set nointegritychecks off 2>&1 | Out-File $log -Append -Encoding utf8
& bcdedit.exe /enum '{current}' 2>&1 | Select-String 'testsigning|nointegritychecks' | Out-File $log -Append -Encoding utf8
"=== done (reboot required) ===" | Out-File $log -Append -Encoding utf8
