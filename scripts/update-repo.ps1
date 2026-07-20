$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
python (Join-Path $PSScriptRoot "build_repo.py") --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Repo da duoc cap nhat." -ForegroundColor Green
