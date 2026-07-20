param(
    [string]$RemoteUrl = "",
    [string]$Message = "Update Sileo repository"
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot "update-repo.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Set-Location $RepoRoot
if (-not (Test-Path ".git")) { git init -b main }
if ($RemoteUrl) {
    if (git remote get-url origin 2>$null) { git remote set-url origin $RemoteUrl }
    else { git remote add origin $RemoteUrl }
}
if (-not (git remote get-url origin 2>$null)) {
    throw "Chua co GitHub remote. Chay: .\scripts\publish.ps1 -RemoteUrl https://github.com/USER/REPO.git"
}
git add --all
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { git commit -m $Message }
git push -u origin main
Write-Host "Da upload len GitHub. GitHub Pages se tu dong deploy." -ForegroundColor Green
