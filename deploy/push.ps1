# Push local code to the server over SSH (no GitHub needed) and run deploy.sh.
# Usage (from the project root, on Windows PowerShell):
#   .\deploy\push.ps1 -Server ubuntu@YOUR_SERVER_IP
# Assumes you can SSH in with your key and that provision.sh has already been run once.
param(
    [Parameter(Mandatory = $true)][string]$Server,
    [string]$AppDir = "/opt/dad"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot   # project root (deploy/ is one level down)
$stamp = Get-Date -Format "yyyyMMddHHmmss"
$tar = "$env:TEMP\dad-$stamp.tar.gz"

Write-Host "==> Packaging code (excluding node_modules, .venv, .git, dist, uploads)"
# Windows 10+ ships bsdtar as 'tar'. --exclude keeps the upload small.
tar --exclude=".git" --exclude="node_modules" --exclude=".venv" `
    --exclude="frontend/dist" --exclude="backend/uploads" --exclude="*.pptx" `
    -czf $tar -C $root .

Write-Host "==> Uploading to $Server"
scp $tar "${Server}:/tmp/dad-code.tar.gz"

Write-Host "==> Extracting and deploying on server"
$remote = @"
set -e
sudo mkdir -p $AppDir
sudo tar -xzf /tmp/dad-code.tar.gz -C $AppDir
sudo chown -R dad:dad $AppDir
rm -f /tmp/dad-code.tar.gz
sudo -u dad bash $AppDir/deploy/deploy.sh
"@
ssh $Server $remote

Remove-Item $tar -Force
Write-Host "==> Done. Visit your site."
