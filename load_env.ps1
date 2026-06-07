# Load KEY=VALUE pairs from .env into the current PowerShell session, so command
# line tools (twine, etc.) can read them. Pytest loads .env on its own via
# conftest.py; this is for everything else.
#
# Usage (note the leading dot — it loads into your current session):
#   . .\load_env.ps1
#   python -m twine upload --repository testpypi dist/*

$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host ".env not found next to load_env.ps1 — copy .env.example to .env first." -ForegroundColor Yellow
    return
}

Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or ($line -notmatch "=")) { return }
    $idx = $line.IndexOf("=")
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim().Trim('"').Trim("'")
    Set-Item -Path "env:$key" -Value $val
    Write-Host "loaded $key" -ForegroundColor Green   # name only — never print the value
}
