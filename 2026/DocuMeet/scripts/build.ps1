$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
& '.\.venv\Scripts\python.exe' -m pip install pyinstaller
if ($LASTEXITCODE -ne 0) { throw 'Could not install PyInstaller.' }
& '.\.venv\Scripts\python.exe' -m PyInstaller --noconfirm packaging\DocuMeet.spec
if ($LASTEXITCODE -ne 0) { throw 'Application build failed.' }
$compiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
$privateCompiler = Join-Path $projectRoot '.tools\InnoSetup\ISCC.exe'
$innoPath = if ($compiler) { $compiler.Source } elseif (Test-Path -LiteralPath $privateCompiler) { $privateCompiler } else { Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe' }
if (Test-Path -LiteralPath $innoPath) {
    & $innoPath packaging\DocuMeet.iss
    if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }
} else {
    Write-Host 'Portable app is ready in dist\DocuMeet. Install Inno Setup 6 to also create an installer.'
}
