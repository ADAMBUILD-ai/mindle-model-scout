from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import httpx

from src.model_scout.team_router import (
    ChildIssue,
    GitHubChildIssueWriter,
    TeamRegistry,
    TeamRouteError,
    TeamRouter,
)


class FakeWriter:
    def __init__(self) -> None:
        self.issues: dict[tuple[str, str], ChildIssue] = {}
        self.created: list[tuple[str, str, str]] = []

    def find_open_issue(self, repository_full_name: str, marker: str) -> ChildIssue | None:
        return self.issues.get((repository_full_name, marker))

    def create_issue(self, repository_full_name: str, *, title: str, body: str) -> ChildIssue:
        child = ChildIssue(number=len(self.created) + 1, url=f"https://github.test/{repository_full_name}/issues/{len(self.created) + 1}")
        marker = next(line for line in body.splitlines() if line.startswith("<!-- model-scout-route:"))
        self.issues[(repository_full_name, marker)] = child
        self.created.append((repository_full_name, title, body))
        return child


def _registry(tmp_path):
    path = tmp_path / "team-registry.json"
    path.write_text(
        json.dumps(
            {
                "teams": [
                    {
                        "team_id": "media",
                        "display_name": "Media",
                        "repository_full_name": "ADAMBUILD-ai/mindle-media-ai",
                        "issue_or_task_channel": "issues",
                        "execution_workflow": "triage",
                        "artifact_return_channel": "central callback",
                        "ack_timeout_minutes": 15,
                        "retry_policy": "audit",
                        "owner_or_executor": "maintainer",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return TeamRegistry.load(path)


def _route(router: TeamRouter, *, now: datetime):
    return router.route(
        team_id="media",
        central_repository="ADAMBUILD-ai/mindle-model-scout",
        central_issue=50,
        purpose="Validate actual media",
        required_input="Authorized originals",
        completion_gate="Actual output evidence",
        callback_url="https://github.com/ADAMBUILD-ai/mindle-model-scout/issues/50",
        now=now,
    )


def test_registry_loads_and_router_creates_an_idempotent_child_issue(tmp_path):
    writer = FakeWriter()
    router = TeamRouter(_registry(tmp_path), writer)
    now = datetime(2026, 9, 17, 1, tzinfo=UTC)

    first = _route(router, now=now)
    second = _route(router, now=now + timedelta(minutes=1))

    assert first.state == "REQUEST_SENT"
    assert first.child_repository == "ADAMBUILD-ai/mindle-media-ai"
    assert second == first
    assert len(writer.created) == 1
    body = writer.created[0][2]
    assert "model-scout-route:ADAMBUILD-ai/mindle-model-scout#50" in body
    assert "Central Issue: https://github.com/ADAMBUILD-ai/mindle-model-scout/issues/50" in body
    assert "Required actual input: Authorized originals" in body


def test_ack_and_timeout_are_distinguished(tmp_path):
    writer = FakeWriter()
    router = TeamRouter(_registry(tmp_path), writer)
    now = datetime(2026, 9, 17, 1, tzinfo=UTC)
    routed = _route(router, now=now)

    assert router.audit_ack_timeouts(now=routed.ack_deadline - timedelta(seconds=1)) == []
    timed_out = router.audit_ack_timeouts(now=routed.ack_deadline)
    assert timed_out[0].state == "ROUTE_FAILED"
    assert timed_out[0].failure_classification == "EXECUTOR_UNREACHABLE"

    retry_router = TeamRouter(_registry(tmp_path), writer)
    _route(retry_router, now=now)
    acked = retry_router.record_ack(
        central_repository="ADAMBUILD-ai/mindle-model-scout",
        central_issue=50,
        evidence_url="https://github.com/ADAMBUILD-ai/mindle-media-ai/issues/1#issuecomment-1",
    )
    assert acked.state == "ACK_RECEIVED"
    assert retry_router.audit_ack_timeouts(now=now + timedelta(hours=1)) == []


def test_unregistered_team_is_route_failed(tmp_path):
    router = TeamRouter(_registry(tmp_path), FakeWriter())
    try:
        router.route(
            team_id="missing",
            central_repository="ADAMBUILD-ai/mindle-model-scout",
            central_issue=50,
            purpose="p",
            required_input="i",
            completion_gate="g",
            callback_url="https://github.com/example/issues/1",
        )
    except TeamRouteError as exc:
        assert "ROUTE_FAILED" in str(exc)
    else:
        raise AssertionError("unregistered team must fail")


def test_github_writer_deduplicates_by_route_marker_and_creates_child_issue():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request):
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(200, json=[], request=request)
        return httpx.Response(
            201,
            json={"number": 12, "html_url": "https://github.test/ADAMBUILD-ai/mindle-media-ai/issues/12"},
            request=request,
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        writer = GitHubChildIssueWriter(token="test-token", api_base="https://api.github.test", client=client)
        assert writer.find_open_issue("ADAMBUILD-ai/mindle-media-ai", "marker") is None
        created = writer.create_issue("ADAMBUILD-ai/mindle-media-ai", title="route", body="marker")

    assert created.number == 12
    assert len(requests) == 2
    assert requests[0].url == httpx.URL("https://api.github.test/repos/ADAMBUILD-ai/mindle-media-ai/issues?state=open&per_page=100")
    assert requests[1].headers["authorization"] == "Bearer test-token"
