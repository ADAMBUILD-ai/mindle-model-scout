from __future__ import annotations

import argparse
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .report import build_report
from .scout import scout


WEB_UI_PORT = 8765
WEB_UI_HOST = "127.0.0.1"
SUPPORTED_UI_RESOURCES = ("model", "dataset", "space", "all")


def normalize_limit(raw_limit: str | None, default: int = 10) -> int:
    if raw_limit is None or raw_limit == "":
        return default
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("limit must be an integer between 1 and 100") from exc

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    return limit


def normalize_resource(raw_resource: str | None, default: str = "model") -> str:
    resource = (raw_resource or default).strip().lower()
    if resource not in SUPPORTED_UI_RESOURCES:
        raise ValueError(f"resource must be one of {', '.join(SUPPORTED_UI_RESOURCES)}")
    return resource


def build_search_payload(query: str, limit: int, resource_type: str) -> dict[str, Any]:
    limit = normalize_limit(str(limit), default=10)
    resource_type = normalize_resource(resource_type, default="model")
    trimmed = query.strip()
    if not trimmed:
        raise ValueError("query is required")

    raw = scout(trimmed, limit, resource_type)
    report = build_report(raw, top_n=min(limit, 20))
    candidates = raw.get("candidates") or []
    return {
        "query": raw.get("query"),
        "resource_type": resource_type,
        "searched_candidate_count": raw.get("searched_candidate_count", 0),
        "candidate_count": raw.get("candidate_count", 0),
        "search_query": raw.get("search_query"),
        "query_plan": raw.get("query_plan"),
        "shortlist": candidates[: min(len(candidates), limit)],
        "recommended": report.get("recommended"),
        "comparison": report.get("comparison"),
        "warnings": report.get("warnings"),
    }


def json_response(payload: dict[str, Any], status: int = 200) -> tuple[int, dict[str, str], str]:
    return status, {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}, json.dumps(payload, ensure_ascii=False)


def ui_index_html() -> str:
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>MODEL SCOUT</title>
  <style>
    :root { font-family: "Pretendard", "Noto Sans KR", Arial, sans-serif; color: #122; background: #f6f8fb; }
    body { margin: 0; padding: 2rem; }
    .container { max-width: 960px; margin: 0 auto; background: #fff; border-radius: 14px; box-shadow: 0 18px 40px rgba(15, 35, 84, 0.08); padding: 1.2rem; }
    h1 { margin-top: 0; }
    .row { display: grid; grid-template-columns: 1.3fr 1fr 1fr auto; gap: 0.6rem; align-items: end; }
    input, select, button { padding: 0.6rem; border-radius: 8px; border: 1px solid #ccd4e4; font-size: 1rem; }
    button { background: #2f63f6; color: white; border-color: #2f63f6; cursor: pointer; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .error { color: #b1002e; background: #fff0f4; border: 1px solid #ffb5ca; padding: 0.6rem; border-radius: 8px; }
    .panel { margin-top: 1rem; background: #fafcff; border: 1px solid #dbe4ff; border-radius: 10px; padding: 0.8rem; }
    table { border-collapse: collapse; width: 100%; margin-top: 0.7rem; }
    th, td { text-align: left; border-bottom: 1px solid #dce4fa; padding: 0.5rem; }
    th { background: #edf2ff; }
    .hidden { display: none; }
    #status { font-size: 0.96rem; margin-top: 0.5rem; }
  </style>
</head>
<body>
  <div class=\"container\">
    <h1>MODEL SCOUT</h1>
    <form id=\"search-form\">
      <div class=\"row\">
        <label>query<input id=\"query\" type=\"text\" placeholder=\"e.g. commercial tts\" required /></label>
        <label>api key<input id=\"api-key\" type=\"password\" placeholder=\"if required\" autocomplete=\"off\" /></label>
        <label>resource
          <select id=\"resource\">
            <option value=\"model\" selected>model</option>
            <option value=\"dataset\">dataset</option>
            <option value=\"space\">space</option>
            <option value=\"all\">all</option>
          </select>
        </label>
        <label>limit<input id=\"limit\" type=\"number\" min=\"1\" max=\"100\" value=\"10\" /></label>
        <button id=\"run-btn\" type=\"submit\">Search</button>
      </div>
    </form>
    <div id=\"error\" class=\"error hidden\"></div>
    <div id=\"status\"></div>

    <div class=\"panel\">
      <h2>Top recommendation</h2>
      <div id=\"top-reco\">-</div>
    </div>

    <div class=\"panel\">
      <h2>Comparison</h2>
      <table id=\"comparison\">
        <thead>
          <tr><th>candidate</th><th>type</th><th>license</th><th>score</th><th>status</th><th>downloads</th><th>source</th></tr>
        </thead>
        <tbody></tbody>
      </table>
      <div id=\"comparison-empty\">No candidates yet.</div>
    </div>

    <div class=\"panel\">
      <h2>License / status</h2>
      <ul id=\"warnings\"></ul>
    </div>
  </div>

  <script>
    const form = document.getElementById("search-form");
    const queryInput = document.getElementById("query");
    const resourceInput = document.getElementById("resource");
    const apiKeyInput = document.getElementById("api-key");
    const limitInput = document.getElementById("limit");
    const runButton = document.getElementById("run-btn");
    const errorEl = document.getElementById("error");
    const statusEl = document.getElementById("status");
    const topReco = document.getElementById("top-reco");
    const warningEl = document.getElementById("warnings");
    const tbody = document.querySelector("#comparison tbody");
    const comparisonEmpty = document.getElementById("comparison-empty");

    function showError(message) {
      errorEl.textContent = message;
      errorEl.classList.remove("hidden");
    }

    function clearError() {
      errorEl.textContent = "";
      errorEl.classList.add("hidden");
    }

    function escapeHtml(text) {
      const div = document.createElement("div");
      div.textContent = text ?? "";
      return div.innerHTML;
    }

    function renderRecommendation(payload) {
      const rec = payload.recommended;
      if (!rec) {
        topReco.textContent = "No eligible recommendation. Check warnings.";
        return;
      }
      const license = (rec.license || "UNKNOWN");
      const status = rec.status || "UNKNOWN";
      topReco.innerHTML = `<strong>${escapeHtml(rec.model_id || "")}</strong> (Score: ${rec.score || 0}, Status: ${escapeHtml(status)}, License: ${escapeHtml(license)})<br/>`;
      if (rec.source_url) {
        topReco.innerHTML += `<a href=\"${escapeHtml(rec.source_url)}\" target=\"_blank\">Hugging Face source</a>`;
      }
    }

    function renderWarnings(payload) {
      warningEl.innerHTML = "";
      if (!payload.warnings || payload.warnings.length === 0) {
        warningEl.innerHTML = "<li>None</li>";
        return;
      }
      for (const warning of payload.warnings) {
        const li = document.createElement("li");
        li.textContent = warning;
        warningEl.appendChild(li);
      }
    }

    function renderComparison(payload) {
      tbody.innerHTML = "";
      const rows = payload.comparison || [];
      comparisonEmpty.classList.toggle("hidden", rows.length > 0);
      for (const row of rows) {
        const tr = document.createElement("tr");
        const href = row.model_id ? `https://huggingface.co/${row.resource_type === "dataset" ? "datasets/" : row.resource_type === "space" ? "spaces/" : ""}${row.model_id}` : "";
        tr.innerHTML = `<td>${escapeHtml(row.model_id || "")}</td><td>${escapeHtml(row.resource_type || "")}</td><td>${escapeHtml(row.license || "UNKNOWN")}</td><td>${row.score || 0}</td><td>${escapeHtml(row.status || "")}</td><td>${row.downloads || 0}</td><td>${href ? `<a href=\"${href}\" target=\"_blank\">open</a>` : "-"}</td>`;
        tbody.appendChild(tr);
      }
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearError();
      statusEl.textContent = "Searching...";
      runButton.disabled = true;
      tbody.innerHTML = "";
      comparisonEmpty.classList.remove("hidden");

      const params = new URLSearchParams({
        query: queryInput.value,
        resource: resourceInput.value,
        limit: limitInput.value || "10",
      });
      if (apiKeyInput.value) {
        params.set("api_key", apiKeyInput.value.trim());
      }

      try {
        const response = await fetch(`/api/search?${params.toString()}`);
        const bodyText = await response.text();
        let data;
        try {
          data = JSON.parse(bodyText);
      } catch (parseError) {
          throw new Error("Response was not valid JSON");
        }
        if (!response.ok) {
          throw new Error((data && data.error) || `Request failed with status ${response.status}`);
        }
        renderRecommendation(data);
        renderComparison(data);
        renderWarnings(data);
        statusEl.textContent = `Completed: searched ${data.searched_candidate_count} / visible ${data.comparison?.length || 0}`;
      } catch (error) {
        showError(String(error.message || error));
        renderRecommendation({});
        renderComparison({});
        renderWarnings({warnings: [""]});
        statusEl.textContent = "";
      } finally {
        runButton.disabled = false;
      }
    });
  </script>
</body>
</html>"""


class ScoutRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict[str, Any], status_code: int = 200) -> None:
        status, headers, body = json_response(payload, status_code)
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "":
            page = ui_index_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
            return

        if parsed.path != "/api/search":
            self.send_response(404)
            self.end_headers()
            return

        query = urllib.parse.parse_qs(parsed.query)
        query_text = (query.get("query") or [""])[0]
        resource = (query.get("resource") or ["model"])[0]
        limit = (query.get("limit") or ["10"])[0]
        try:
            normalized_limit = normalize_limit(limit, default=10)
            normalized_resource = normalize_resource(resource, default="model")
            payload = build_search_payload(query_text, normalized_limit, normalized_resource)
            self._send_json(payload, 200)
            return
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        except Exception as exc:  # noqa: BLE001
            self._send_json({"error": f"{exc}"}, 500)


def run_server(host: str = WEB_UI_HOST, port: int = WEB_UI_PORT, *, open_browser: bool = False) -> None:
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    server = ThreadingHTTPServer((host, port), ScoutRequestHandler)
    try:
        if open_browser:
            import webbrowser

            webbrowser.open_new(f"http://{host}:{port}/")
        print(f"Serving MODEL SCOUT UI on http://{host}:{port}/")
        server.serve_forever()
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Start MODEL SCOUT local web UI")
    parser.add_argument("--host", default=WEB_UI_HOST, help="HTTP bind address")
    parser.add_argument("--port", type=int, default=WEB_UI_PORT, help="HTTP bind port")
    parser.add_argument("--open", action="store_true", help="open browser automatically")
    args = parser.parse_args()
    run_server(args.host, args.port, open_browser=args.open)


if __name__ == "__main__":
    main()
