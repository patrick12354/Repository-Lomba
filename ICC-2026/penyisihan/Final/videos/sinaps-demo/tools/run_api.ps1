# API MVP lokal untuk rekaman demo: SQLite lokal (DATABASE_URL produksi sengaja TIDAK dipakai),
# OPENAI_API_KEY diambil dari Final/.env supaya tutor menjawab sungguhan.
$root = Resolve-Path "$PSScriptRoot\..\..\.."
$envFile = Join-Path $root ".env"
Get-Content $envFile | ForEach-Object {
  if ($_ -match '^\s*OPENAI_API_KEY\s*=\s*"?([^"]+)"?\s*$') { $env:OPENAI_API_KEY = $Matches[1].Trim() }
}
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:POSTGRES_URL -ErrorAction SilentlyContinue
Set-Location (Join-Path $root "mvp")
& "C:\Patrick\coding\.venv\Scripts\python.exe" -m uvicorn api.index:app --port 8000
