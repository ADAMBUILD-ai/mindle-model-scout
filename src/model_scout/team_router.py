from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import httpx


class TeamRouteError(RuntimeError):
    """Raised when a team route cannot be created or inspected safely."""


class ChildIssueWriter(Protocol):
    def find_open_issue(self, repository_full_name: str, marker: str) -> "ChildIssue | None": ...

    def create_issue(
        self, repository_full_name: str, *, title: str, body: str
    ) -> "ChildIssue": ...


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
        required = (
            "team_id",
            "display_name",
            "repository_full_name",
            "issue_or_task_channel",
            "execution_workflow",
            "artifact_return_channel",
            "ack_timeout_minutes",
            "retry_policy",
            "owner_or_executor",
        )
        missing = [field for field in required if not str(payload.get(field, "")).strip()]
        if missing:
            raise ValueError(f"team registry entry missing: {', '.join(missing)}")
        timeout = int(payload["ack_timeout_minutes"])
        if timeout <= 0:
            raise ValueError("ack_timeout_minutes must be positive")
        repository = str(payload["repository_full_name"]).strip()
        if len(repository.split("/")) != 2:
            raise ValueError("repository_full_name must use owner/name form")
        return cls(
            team_id=str(payload["team_id"]).strip(),
            display_name=str(payload["display_name"]).strip(),
            repository_full_name=repository,
            issue_or_task_channel=str(payload["issue_or_task_channel"]).strip(),
            execution_workflow=str(payload["execution_workflow"]).strip(),
            artifact_return_channel=str(payload["artifact_return_channel"]).strip(),
            ack_timeout_minutes=timeout,
            retry_policy=str(payload["retry_policy"]).strip(),
            owner_or_executor=str(payload["owner_or_executor"]).strip(),
        )


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


class TeamRouter:
    """Idempotently create child issues and audit missing team acknowledgements."""

    def __init__(self, registry: TeamRegistry, writer: ChildIssueWriter) -> None:
        self._registry = registry
        self._writer = writer
        self._routes: dict[tuple[str, int], RouteRecord] = {}

    @staticmethod
    def route_marker(central_repository: str, central_issue: int) -> str:
        return f"<!-- model-scout-route:{central_repository}#{central_issue} -->"

    def route(
        self,
        *,
        team_id: str,
        central_repository: str,
        central_issue: int,
        purpose: str,
        required_input: str,
        completion_gate: str,
        callback_url: str,
        now: datetime | None = None,
    ) -> RouteRecord:
        endpoint = self._registry.get(team_id)
        if endpoint.issue_or_task_channel != "issues":
            raise TeamRouteError(
                f"ROUTE_FAILED: unsupported channel={endpoint.issue_or_task_channel}"
            )
        if central_issue <= 0:
            raise ValueError("central_issue must be positive")
        if not all(value.strip() for value in (purpose, required_input, completion_gate, callback_url)):
            raise ValueError("route details must not be empty")

        route_key = (central_repository, central_issue)
        existing = self._routes.get(route_key)
        if existing is not None:
            return existing

        marker = self.route_marker(central_repository, central_issue)
        child = self._writer.find_open_issue(endpoint.repository_full_name, marker)
        if child is None:
            body = self._render_child_issue_body(
                marker=marker,
                endpoint=endpoint,
                central_repository=central_repository,
                central_issue=central_issue,
                purpose=purpose,
                required_input=required_input,
                completion_gate=completion_gate,
                callback_url=callback_url,
            )
            child = self._writer.create_issue(
                endpoint.repository_full_name,
                title=f"[MODEL SCOUT ROUTE] Central Issue #{central_issue} input request",
                body=body,
            )

        sent_at = (now or datetime.now(UTC)).astimezone(UTC)
        record = RouteRecord(
            team_id=team_id,
            central_repository=central_repository,
            central_issue=central_issue,
            child_repository=endpoint.repository_full_name,
            child_issue=child.number,
            child_url=child.url,
            state="REQUEST_SENT",
            sent_at=sent_at,
            ack_deadline=sent_at + timedelta(minutes=endpoint.ack_timeout_minutes),
        )
        self._routes[route_key] = record
        return record

    def record_ack(
        self,
        *,
        central_repository: str,
        central_issue: int,
        evidence_url: str,
    ) -> RouteRecord:
        route_key = (central_repository, central_issue)
        record = self._routes.get(route_key)
        if record is None:
            raise KeyError(route_key)
        if not evidence_url.startswith("https://"):
            raise ValueError("ACK evidence must be an https URL")
        acknowledged = replace(
            record,
            state="ACK_RECEIVED",
            ack_evidence_url=evidence_url,
            failure_classification=None,
        )
        self._routes[route_key] = acknowledged
        return acknowledged

    def audit_ack_timeouts(self, *, now: datetime | None = None) -> list[RouteRecord]:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        timed_out: list[RouteRecord] = []
        for route_key, record in self._routes.items():
            if record.state != "REQUEST_SENT" or current < record.ack_deadline:
                continue
            updated = replace(
                record,
                state="ROUTE_FAILED",
                failure_classification="EXECUTOR_UNREACHABLE",
            )
            self._routes[route_key] = updated
            timed_out.append(updated)
        return timed_out

    @staticmethod
    def _render_child_issue_body(
        *,
        marker: str,
        endpoint: TeamEndpoint,
        central_repository: str,
        central_issue: int,
        purpose: str,
        required_input: str,
        completion_gate: str,
        callback_url: str,
    ) -> str:
        central_url = f"https://github.com/{central_repository}/issues/{central_issue}"
        return "\n".join(
            (
                marker,
                "## MODEL SCOUT team input request",
                "",
                f"- Central Issue: {central_url}",
                f"- Purpose: {purpose}",
                f"- Required actual input: {required_input}",
                f"- Completion gate: {completion_gate}",
                f"- Central callback: {callback_url}",
                "",
                "Please post `MODEL_SCOUT_ACK` with the intended executor and an accessible artifact channel before starting.",
                f"Artifact return channel: {endpoint.artifact_return_channel}",
            )
        )


class GitHubChildIssueWriter:
    """GitHub REST transport used by the real child-issue routing command."""

    def __init__(
        self,
        *,
        token: str | None = None,
        api_base: str = "https://api.github.com",
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._token = str(token or os.getenv("GITHUB_TOKEN") or "").strip()
        if not self._token:
            raise ValueError("GITHUB_TOKEN is required for team routing")
        self._api_base = api_base.rstrip("/")
        self._timeout = float(timeout)
        self._client = client

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "mindle-model-scout-team-router",
        }
        try:
            if self._client is not None:
                return self._client.request(method, url, headers=headers, timeout=self._timeout, **kwargs)
            with httpx.Client(timeout=self._timeout) as client:
                return client.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise TeamRouteError(f"GitHub route transport failed: {type(exc).__name__}") from None

    def find_open_issue(self, repository_full_name: str, marker: str) -> ChildIssue | None:
        response = self._request(
            "GET",
            f"{self._api_base}/repos/{repository_full_name}/issues",
            params={"state": "open", "per_page": 100},
        )
        if response.status_code != 200:
            raise TeamRouteError(f"ROUTE_FAILED: GitHub issue lookup returned HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, list):
            raise TeamRouteError("ROUTE_FAILED: GitHub issue lookup returned invalid JSON")
        for item in payload:
            if not isinstance(item, dict) or item.get("pull_request"):
                continue
            if marker in str(item.get("body") or ""):
                return ChildIssue(number=int(item["number"]), url=str(item["html_url"]))
        return None

    def create_issue(self, repository_full_name: str, *, title: str, body: str) -> ChildIssue:
        response = self._request(
            "POST",
            f"{self._api_base}/repos/{repository_full_name}/issues",
            json={"title": title, "body": body},
        )
        if not 200 <= response.status_code < 300:
            raise TeamRouteError(f"ROUTE_FAILED: GitHub child issue create returned HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict) or "number" not in payload or "html_url" not in payload:
            raise TeamRouteError("ROUTE_FAILED: GitHub child issue create returned invalid JSON")
        return ChildIssue(number=int(payload["number"]), url=str(payload["html_url"]))
