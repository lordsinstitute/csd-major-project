$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    $candidateVersion = $null
    foreach ($version in @('3.13', '3.12')) {
        & py "-$version" -c 'import sys; print(sys.version)' 2>$null
        if ($LASTEXITCODE -eq 0) { $candidateVersion = $version; break }
    }
    if (-not $candidateVersion) {
        throw 'Install 64-bit Python 3.12 or 3.13 from python.org, then run setup again.'
    }
    & py "-$candidateVersion" -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -e '.[models]'
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check internet access and retry.' }
Write-Host 'Application installed. Start DocuMeet and use Offline models to prepare model weights.'
