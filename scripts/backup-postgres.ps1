param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\backups"),
    [string]$Database = "nova",
    [string]$Username = "nova"
)

$resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($resolvedOutput) | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $resolvedOutput "nova-$timestamp.sql"

docker compose exec -T postgres pg_dump -U $Username -d $Database --clean --if-exists | Set-Content -Encoding UTF8 -LiteralPath $backupPath
if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL backup failed."
}

Write-Output "Backup created: $backupPath"
