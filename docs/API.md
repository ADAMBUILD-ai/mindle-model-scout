# MINDLE MODEL SCOUT Common API

The Scout core remains unchanged and is exposed through a thin FastAPI service.

## Endpoints

### GET `/health`

Returns service readiness.

```json
{
  "status": "healthy",
  "service": "mindle-model-scout-api",
  "version": "1.0.0",
  "checked_at": "2026-09-12T00:00:00+00:00"
}
```

### GET `/v1/capabilities`

Returns resource support and limits.

### GET `/v1/scout`

Query parameters:

- `query` (required)
- `resource` (`model`, `dataset`, `space`, `all`; default `model`)
- `limit` (1..100, default `10`)
- `top_n` (1..50, default `5`)

### POST `/v1/scout`

Accepts JSON body with:

```json
{
  "query": "commercial tts",
  "limit": 10,
  "top_n": 5,
  "resource": "all"
}
```

## Auth

Set `MODEL_SCOUT_API_KEY` in the environment to enable API key protection.
When set, clients must send `X-API-KEY: <MODEL_SCOUT_API_KEY>`.

## Run locally

```bash
cp .env.example .env
python -m pip install -r requirements.txt
python -m uvicorn src.model_scout_api.main:app --reload --host 0.0.0.0 --port 8080
```

PowerShell:

```powershell
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python -m uvicorn src.model_scout_api.main:app --reload --host 0.0.0.0 --port 8080
```

## Team integration examples

Python:

```python
import os
import requests

url = "http://127.0.0.1:8080/v1/scout"
headers = {"X-API-KEY": os.getenv("MODEL_SCOUT_API_KEY", "")}
payload = {"query": "tts", "resource": "all", "limit": 10, "top_n": 5}
resp = requests.post(url, json=payload, headers=headers)
resp.raise_for_status()
print(resp.json())
```

JavaScript:

```javascript
const response = await fetch("http://127.0.0.1:8080/v1/scout?query=tts&resource=model&limit=10", {
  headers: { "X-API-KEY": process.env.MODEL_SCOUT_API_KEY || "" },
});
const data = await response.json();
console.log(data.response.recommended);
```

PowerShell:

```powershell
$headers = @{ "X-API-KEY" = $env:MODEL_SCOUT_API_KEY }
Invoke-RestMethod -Uri "http://127.0.0.1:8080/v1/scout?query=tts&resource=model&limit=10&top_n=5" -Headers $headers -Method Get
```

Docker:

```bash
docker build -t mindle-model-scout-api .
docker run -p 8080:8080 --env-file .env -e MODEL_SCOUT_API_KEY=change-me mindle-model-scout-api
```
