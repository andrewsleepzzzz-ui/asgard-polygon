param(
    [ValidateSet('Status', 'Install', 'Remove')]
    [string]$Action = 'Status'
)

$ErrorActionPreference = 'Stop'
$serviceName = 'PolygonMemory'
$kernel = Join-Path $PSScriptRoot 'Asgard_Polygon\Asgard_Polygon\Kernel'
$driver = Join-Path $kernel 'PolygonMemory.test.sys'
$certificate = Join-Path $kernel 'PolygonMemory.test.cer'
$serviceKey = "HKLM:\SYSTEM\CurrentControlSet\Services\$serviceName"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Run this action in an elevated PowerShell window (Run as administrator).'
    }
}

function Show-Status {
    if (Test-Path -LiteralPath $driver) {
        $signature = Get-AuthenticodeSignature -LiteralPath $driver
        $signer = if ($signature.SignerCertificate) { $signature.SignerCertificate.Subject } else { 'none' }
        Write-Host "Driver: $driver"
        Write-Host "Signature: $signer ($($signature.Status))"
    } else {
        Write-Host "Driver missing: $driver"
    }

    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "Service: $serviceName ($($service.Status))"
        if (Test-Path -LiteralPath $serviceKey) {
            Write-Host "ImagePath: $((Get-ItemProperty -LiteralPath $serviceKey).ImagePath)"
        }
    } else {
        Write-Host "Service: $serviceName (not installed)"
    }

    $bcd = & bcdedit.exe /enum 2>&1
    if ($LASTEXITCODE -eq 0) {
        $line = $bcd | Where-Object { $_ -match '^\s*testsigning\s+' } | Select-Object -First 1
        Write-Host "Boot setting: $(if ($line) { $line.Trim() } else { 'TESTSIGNING not enabled' })"
    } else {
        Write-Host 'Boot setting: requires an elevated window to inspect'
    }
}

switch ($Action) {
    'Status' {
        Show-Status
    }
    'Install' {
        Assert-Administrator
        if (-not (Test-Path -LiteralPath $driver)) { throw "Build and test-sign first: $driver" }
        if (-not (Test-Path -LiteralPath $certificate)) { throw "Missing public test certificate: $certificate" }
        $signature = Get-AuthenticodeSignature -LiteralPath $driver
        $expected = [Security.Cryptography.X509Certificates.X509Certificate2]::new($certificate)
        if (-not $signature.SignerCertificate -or
            $signature.SignerCertificate.Thumbprint -ne $expected.Thumbprint) {
            throw 'The test driver signature does not match PolygonMemory.test.cer. Run sign-test.ps1 again.'
        }

        if (Test-Path -LiteralPath $serviceKey) {
            $installedPath = (Get-ItemProperty -LiteralPath $serviceKey).ImagePath
            $installedPath = $installedPath -replace '^\\\?\?\\', ''
            $installedPath = $installedPath.Trim('"')
            if (-not [string]::Equals($installedPath, $driver,
                [StringComparison]::OrdinalIgnoreCase)) {
                throw "A $serviceName service already points to another file: $installedPath"
            }
        } else {
            & sc.exe create $serviceName type= kernel start= demand binPath= $driver
            if ($LASTEXITCODE -ne 0) { throw "Could not create service (sc.exe exit $LASTEXITCODE)." }
        }

        $service = Get-Service -Name $serviceName -ErrorAction Stop
        if ($service.Status -ne 'Running') {
            & sc.exe start $serviceName
            if ($LASTEXITCODE -ne 0) {
                throw "Driver did not load (sc.exe exit $LASTEXITCODE). Check the Windows error above and run .\load-test-driver.ps1 -Action Status."
            }
        }
        Show-Status
    }
    'Remove' {
        Assert-Administrator
        if (-not (Test-Path -LiteralPath $serviceKey)) {
            Write-Host "Service: $serviceName (not installed)"
            break
        }
        $service = Get-Service -Name $serviceName -ErrorAction Stop
        if ($service.Status -eq 'Running') {
            & sc.exe stop $serviceName
            if ($LASTEXITCODE -ne 0) { throw "Could not stop driver (sc.exe exit $LASTEXITCODE)." }
        }
        & sc.exe delete $serviceName
        if ($LASTEXITCODE -ne 0) { throw "Could not remove service (sc.exe exit $LASTEXITCODE)." }
        Write-Host "Removed service: $serviceName"
    }
}
