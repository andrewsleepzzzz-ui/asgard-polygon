param()
$ErrorActionPreference = 'Continue'
$kernel = 'F:\dsh\32\Asgard_Polygon-main\Asgard_Polygon\Asgard_Polygon\Kernel'
$cert = Join-Path $kernel 'PolygonMemory.test.cer'
$sys  = Join-Path $kernel 'PolygonMemory.test.sys'
$log = 'C:\poly_elevate.log'

"=== elevate_setup start ===" | Out-File $log -Encoding utf8
"admin=" + ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) | Out-File $log -Append -Encoding utf8

& bcdedit.exe /set testsigning on 2>&1 | Out-File $log -Append -Encoding utf8
& certutil.exe -addstore -f Root $cert 2>&1 | Out-File $log -Append -Encoding utf8
& certutil.exe -addstore -f TrustedPublisher $cert 2>&1 | Out-File $log -Append -Encoding utf8

if (-not (Get-Service -Name PolygonMemory -ErrorAction SilentlyContinue)) {
    & sc.exe create PolygonMemory type= kernel start= demand binPath= $sys 2>&1 | Out-File $log -Append -Encoding utf8
} else {
    "service exists" | Out-File $log -Append -Encoding utf8
}
& bcdedit.exe /enum 2>&1 | Select-String 'testsigning' | Out-File $log -Append -Encoding utf8
"=== elevate_setup done (reboot required for testsigning) ===" | Out-File $log -Append -Encoding utf8
