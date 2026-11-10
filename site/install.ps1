# TokenRelay Fast Installer for Windows
$ErrorActionPreference = "Stop"
Write-Host "⚡ Installing TokenRelay — Universal AI Cost Savings Agent..." -ForegroundColor Cyan

$InstallDir = "$HOME\.tokenrelay"
if (Test-Path $InstallDir) {
    Write-Host "Existing installation detected. Updating..." -ForegroundColor Yellow
} else {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

$ZipUrl = "https://github.com/qanvass/tokenrelay/archive/refs/heads/master.zip"
$ZipFile = "$env:TEMP\tokenrelay.zip"

Write-Host "Downloading latest TokenRelay release..." -ForegroundColor Gray
Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipFile

Write-Host "Extracting files..." -ForegroundColor Gray
Expand-Archive -Path $ZipFile -DestinationPath "$env:TEMP\tokenrelay_extract" -Force
Copy-Item -Recurse -Force "$env:TEMP\tokenrelay_extract\tokenrelay-master\*" $InstallDir
Remove-Item -Recurse -Force "$env:TEMP\tokenrelay_extract", $ZipFile

Write-Host "Registering Claude Desktop MCP Server..." -ForegroundColor Gray
python "$InstallDir\agent.py" mcp

Write-Host "TokenRelay installed successfully to $InstallDir!" -ForegroundColor Green
Write-Host "To launch dashboard: python `"$InstallDir\agent.py`" dashboard" -ForegroundColor Cyan
