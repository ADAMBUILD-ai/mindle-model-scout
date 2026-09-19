from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import httpx


class TeamRouteError(RuntimeError):
    pass


class ChildIssueWriter(Protocol):
    def find_open_issue(self, repository_full_name: str, marker: str) -> "ChildIssue | None": ...
    def create_issue(self, repository_full_name: str, *, title: str, body: str) -> "ChildIssue": ...


@dataclass(frozen=True)
class TeamEndpoint:
    team_id: str
    display_name: str
    repository_full_name: str
    issue_or_task_channel: str
    execution_workflow: str
    artifact_return_channel: str
    ack_timeout_minutes: int
    retry_policy: str
    owner_or_executor: str

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "TeamEndpoint":
        names = tuple(cls.__dataclass_fields__)
        missing = [name for name in names if not str(payload.get(name, "")).strip()]
        if missing:
            raise ValueError(f"team registry entry missing: {', '.join(missing)}")
        if int(payload["ack_timeout_minutes"]) <= 0:
            raise ValueError("ack_timeout_minutes must be positive")
        repository = str(payload["repository_full_name"]).strip()
        if len(repository.split("/")) != 2:
            raise ValueError("repository_full_name must use owner/name form")
        values = {name: str(payload[name]).strip() for name in names}
        values["ack_timeout_minutes"] = int(payload["ack_timeout_minutes"])
        return cls(**values)


class TeamRegistry:
    def __init__(self, endpoints: list[TeamEndpoint]) -> None:
        self._endpoints = {endpoint.team_id: endpoint for endpoint in endpoints}
        if len(self._endpoints) != len(endpoints):
            raise ValueError("team registry team_id values must be unique")

    @classmethod
    def load(cls, path: str | Path) -> "TeamRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        entries = payload.get("teams") if isinstance(payload, dict) else None
        if not isinstance(entries, list) or not entries:
            raise ValueError("team registry must contain a non-empty teams list")
        return cls([TeamEndpoint.from_mapping(entry) for entry in entries if isinstance(entry, dict)])

    def get(self, team_id: str) -> TeamEndpoint:
        try:
            return self._endpoints[team_id]
        except KeyError as exc:
            raise TeamRouteError(f"ROUTE_FAILED: unregistered team_id={team_id}") from exc


@dataclass(frozen=True)
class ChildIssue:
    number: int
    url: str


@dataclass(frozen=True)
class RouteRecord:
    team_id: str
    central_repository: str
    central_issue: int
    child_repository: str
    child_issue: int
    child_url: str
    state: str
    sent_at: datetime
    ack_deadline: datetime
    ack_evidence_url: str | None = None
    failure_classification: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["sent_at"] = self.sent_at.isoformat()
        data["ack_deadline"] = self.ack_deadline.isoformat()
        return data

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "RouteRecord":
        data = dict(data)
        data["sent_at"] = datetime.fromisoformat(str(data["sent_at"])).astimezone(UTC)
        data["ack_deadline"] = datetime.fromisoformat(str(data["ack_deadline"])).astimezone(UTC)
        return cls(**data)


class RouteLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[tuple[str, int], RouteRecord]:
        if not self.path.is_file():
            return {}
        records = [RouteRecord.from_mapping(item) for item in json.loads(self.path.read_text(encoding="utf-8"))]
        return {(record.central_repository, record.central_issue): record for record in records}

    def save(self, records: dict[tuple[str, int], RouteRecord]) -> None:
        self.path.write_text(json.dumps([record.as_dict() for record in records.values()], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class TeamRouter:
    def __init__(self, registry: TeamRegistry, writer: ChildIssueWriter, *, ledger: RouteLedger | None = None) -> None:
        self._registry = registry
        self._writer = writer
        self._ledger = ledger
        self._routes = ledger.load() if ledger else {}

    def _persist(self) -> None:
        if self._ledger:
            self._ledger.save(self._routes)

    def records(self) -> list[RouteRecord]:
        return [self._routes[key] for key in sorted(self._routes)]

    @staticmethod
    def route_marker(central_repository: str, central_issue: int) -> str:
        return f"<!-- model-scout-route:{central_repository}#{central_issue} -->"

    def route(self, *, team_id: str, central_repository: str, central_issue: int, purpose: str, required_input: str, completion_gate: str, callback_url: str, now: datetime | None = None) -> RouteRecord:
        endpoint = self._registry.get(team_id)
        if endpoint.issue_or_task_channel != "issues":
            raise TeamRouteError(f"ROUTE_FAILED: unsupported channel={endpoint.issue_or_task_channel}")
        if central_issue <= 0:
            raise ValueError("central_issue must be positive")
        if not all(value.strip() for value in (purpose, required_input, completion_gate, callback_url)):
            raise ValueError("route details must not be empty")
        key = (central_repository, central_issue)
        if key in self._routes:
            return self._routes[key]
        marker = self.route_marker(*key)
        child = self._writer.find_open_issue(endpoint.repository_full_name, marker)
        if child is None:
            central_url = f"https://github.com/{central_repository}/issues/{central_issue}"
            body = "\n".join((marker, "## MODEL SCOUT team input request", "", f"- Central Issue: {central_url}", f"- Purpose: {purpose}", f"- Required actual input: {required_input}", f"- Completion gate: {completion_gate}", f"- Central callback: {callback_url}", "", "Please post MODEL_SCOUT_ACK with the intended executor and an accessible artifact channel before starting.", f"Artifact return channel: {endpoint.artifact_return_channel}"))
            child = self._writer.create_issue(endpoint.repository_full_name, title=f"[MODEL SCOUT ROUTE] Central Issue #{central_issue} input request", body=body)
        sent_at = (now or datetime.now(UTC)).astimezone(UTC)
        record = RouteRecord(team_id, central_repository, central_issue, endpoint.repository_full_name, child.number, child.url, "REQUEST_SENT", sent_at, sent_at + timedelta(minutes=endpoint.ack_timeout_minutes))
        self._routes[key] = record
        self._persist()
        return record

    def record_ack(self, *, central_repository: str, central_issue: int, evidence_url: str) -> RouteRecord:
        key = (central_repository, central_issue)
        if key not in self._routes:
            raise KeyError(key)
        if not evidence_url.startswith("https://"):
            raise ValueError("ACK evidence must be an https URL")
        record = replace(self._routes[key], state="ACK_RECEIVED", ack_evidence_url=evidence_url, failure_classification=None)
        self._routes[key] = record
        self._persist()
        return record

    def collect_acks(self, reader: "GitHubChildIssueWriter") -> list[RouteRecord]:
        result = []
        for record in self.records():
            if record.state == "REQUEST_SENT":
                evidence_url = reader.find_ack_evidence(record.child_repository, record.child_issue)
                if evidence_url:
                    result.append(self.record_ack(central_repository=record.central_repository, central_issue=record.central_issue, evidence_url=evidence_url))
        return result

    def audit_ack_timeouts(self, *, now: datetime | None = None) -> list[RouteRecord]:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        result = []
        for key, record in self._routes.items():
            if record.state == "REQUEST_SENT" and current >= record.ack_deadline:
                updated = replace(record, state="ROUTE_FAILED", failure_classification="EXECUTOR_UNREACHABLE")
                self._routes[key] = updated
                result.append(updated)
        if result:
            self._persist()
        return result


class GitHubChildIssueWriter:
    def __init__(self, *, token: str | None = None, api_base: str = "https://api.github.com", timeout: float = 15.0, client: httpx.Client | None = None) -> None:
        self._token = str(token or os.getenv("GITHUB_TOKEN") or "").strip()
        if not self._token:
            raise ValueError("GITHUB_TOKEN is required for team routing")
        self._api_base = api_base.rstrip("/")
        self._timeout = timeout
        self._client = client

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {self._token}", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "mindle-model-scout-team-router"}
        try:
            if self._client:
                return self._client.request(method, url, headers=headers, timeout=self._timeout, **kwargs)
            with httpx.Client(timeout=self._timeout) as client:
                return client.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise TeamRouteError(f"GitHub route transport failed: {type(exc).__name__}") from None

    def find_open_issue(self, repository_full_name: str, marker: str) -> ChildIssue | None:
        response = self._request("GET", f"{self._api_base}/repos/{repository_full_name}/issues", params={"state": "open", "per_page": 100})
        if response.status_code != 200:
            raise TeamRouteError(f"ROUTE_FAILED: GitHub issue lookup returned HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, list):
            raise TeamRouteError("ROUTE_FAILED: GitHub issue lookup returned invalid JSON")
        for item in payload:
            if isinstance(item, dict) and not item.get("pull_request") and marker in str(item.get("body") or ""):
                return ChildIssue(number=int(item["number"]), url=str(item["html_url"]))
        return None

    def create_issue(self, repository_full_name: str, *, title: str, body: str) -> ChildIssue:
        response = self._request("POST", f"{self._api_base}/repos/{repository_full_name}/issues", json={"title": title, "body": body})
        if not 200 <= response.status_code < 300:
            raise TeamRouteError(f"ROUTE_FAILED: GitHub child issue create returned HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict) or "number" not in payload or "html_url" not in payload:
            raise TeamRouteError("ROUTE_FAILED: GitHub child issue create returned invalid JSON")
        return ChildIssue(number=int(payload["number"]), url=str(payload["html_url"]))

    def find_ack_evidence(self, repository_full_name: str, issue_number: int) -> str | None:
        response = self._request("GET", f"{self._api_base}/repos/{repository_full_name}/issues/{issue_number}/comments", params={"per_page": 100})
        if response.status_code != 200:
            raise TeamRouteError(f"ACK audit returned HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, list):
            raise TeamRouteError("ACK audit returned invalid JSON")
        for comment in payload:
            if isinstance(comment, dict) and "MODEL_SCOUT_ACK" in str(comment.get("body") or ""):
                url = str(comment.get("html_url") or "")
                if url.startswith("https://"):
                    return url
        return None
