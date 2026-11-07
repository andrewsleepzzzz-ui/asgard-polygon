param(
    [string]$KitsRoot = 'E:\Windows Kits\10'
)

$ErrorActionPreference = 'Stop'
$kernel = Join-Path $PSScriptRoot 'Asgard_Polygon\Asgard_Polygon\Kernel'
$source = Join-Path $kernel 'PolygonMemory.sys'
$signed = Join-Path $kernel 'PolygonMemory.test.sys'
$publicCert = Join-Path $kernel 'PolygonMemory.test.cer'
$signTool = Join-Path $KitsRoot 'bin\10.0.26100.0\x64\signtool.exe'

if (-not (Test-Path -LiteralPath $source)) { throw "Build the driver first: $source" }
if (-not (Test-Path -LiteralPath $signTool)) { throw "Missing SignTool: $signTool" }

$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject 'CN=POLYGON Development Test Only' -CertStoreLocation 'Cert:\CurrentUser\My' -KeyAlgorithm RSA -KeyLength 3072 -HashAlgorithm SHA256 -KeyExportPolicy NonExportable -NotAfter (Get-Date).AddMonths(3)

try {
    Copy-Item -LiteralPath $source -Destination $signed -Force
    Export-Certificate -Cert $cert -FilePath $publicCert -Force | Out-Null
    & $signTool sign /fd SHA256 /s My /sha1 $cert.Thumbprint $signed
    if ($LASTEXITCODE -ne 0) { throw "SignTool failed: $LASTEXITCODE" }
    $signature = Get-AuthenticodeSignature -LiteralPath $signed
    if ($signature.SignerCertificate.Thumbprint -ne $cert.Thumbprint) {
        throw 'The signed driver does not contain the test certificate.'
    }
    Write-Host "Test-signed driver: $signed"
    Write-Host "Public test certificate: $publicCert"
    Write-Host "Signer: $($signature.SignerCertificate.Subject)"
    Write-Host "Trust status on this system: $($signature.Status)"
}
finally {
    Remove-Item -LiteralPath "Cert:\CurrentUser\My\$($cert.Thumbprint)" -ErrorAction SilentlyContinue
}
