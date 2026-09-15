# MODEL SCOUT 401 Recovery Evidence - 2026-09-15

## Root cause

- Render Production contains `MODEL_SCOUT_API_KEY` as a masked secret.
- The deployed browser UI sent no `X-API-KEY`, so `GET /api/search` reached the MODEL SCOUT FastAPI authentication dependency and returned HTTP 401.
- Render application logs recorded the 401 at `/api/search`; the request did not reach Hugging Face.

## Recovery contract

- The same-origin web UI uses `/api/search` without receiving, storing, or placing a service key in a URL.
- Programmatic `/v1/*` endpoints retain `MODEL_SCOUT_API_KEY` and `X-API-KEY` protection.
- The UI does not request an API key or a Hugging Face password.
- Search results expose candidate, license, source URL, download count, and `download_status`.
- `SOURCE_ONLY` means the source is available but no weight was downloaded or verified.

## Verification

- Targeted API, UI, report, and CLI tests: 13 passed.
- Full local suite: 84 non-network tests passed; the 3 live Hugging Face tests were blocked by the local sandbox network policy and then passed in the approved network run.
- Live same-origin route check with a temporary process-only test value: `GET /api/search?query=sam2&resource=model&limit=10` returned 200 with 10 candidates. The first candidate was `facebook/sam2.1-hiera-large`, license `apache-2.0`, with its Hugging Face source URL and `SOURCE_ONLY` download status.

## Deployment boundary

This branch is not merged or deployed. Production deployment remains an explicit approval gate.
