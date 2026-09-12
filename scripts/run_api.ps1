param(
    [string]$Host = $env:MODEL_SCOUT_HOST,
    [string]$Port = $env:MODEL_SCOUT_PORT
)

if (-not $Host) { $Host = "0.0.0.0" }
if (-not $Port) { $Port = "8080" }

python -m uvicorn src.model_scout_api.main:app --host $Host --port $Port
