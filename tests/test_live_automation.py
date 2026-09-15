from __future__ import annotations

import hashlib
from pathlib import Path

from src.model_scout.github_issue_source import GitHubIssueSource
from src.model_scout.live_automation import run_live_cycle


class FakeIssueSource(GitHubIssueSource):
    def __init__(self, issues):
        self._issues = list(issues)

    def list_open_issues(self, repos, *, per_page=100):
        return list(self._issues)


class RecordingWriter:
    def __init__(self):
        self.calls = []

    def __call__(self, repo, issue, body):
        self.calls.append((repo, issue, body))
        return {"id": len(self.calls), "html_url": f"https://example.test/{repo}/issues/{issue}#comment-{len(self.calls)}"}


def _issue(repo: str, number: int, project: str):
    return {
        "repository_full_name": repo,
        "number": number,
        "title": f"[P0][{project}] MODEL SCOUT request",
        "body": "MODEL SCOUT 요청\nfind model dataset space all for local safe use",
        "state": "open",
    }


def test_live_cycle_discovers_dedupes_delivers_and_survives_restart(tmp_path, monkeypatch):
    issues = [
        _issue("ADAMBUILD-ai/agri-ai-business-platform", 33, "AGRI"),
        _issue("ADAMBUILD-ai/adam-build", 38, "ADAM"),
    ]
    source = FakeIssueSource(issues)
    writer = RecordingWriter()
    calls = []

    def fake_scout(query, limit, resource):
        calls.append((query, limit, resource))
        return {
            "query": query,
            "search_query": query,
            "query_plan": [query],
            "resource_type": resource,
            "searched_candidate_count": 1,
            "candidate_count": 1,
            "candidates": [{"id": "example/model", "license": "mit", "score": 1}],
        }

    monkeypatch.setattr("src.model_scout.live_automation.run_scout_core", fake_scout)

    first = run_live_cycle(
        configured_repos=("ADAMBUILD-ai/agri-ai-business-platform", "ADAMBUILD-ai/adam-build"),
        state_dir=tmp_path,
        issue_source=source,
        callback_writer=writer,
    )

    assert len(calls) == 2
    assert len(writer.calls) == 2
    assert sum(1 for item in first if item.get("state") == "DELIVERED") == 2

    second = run_live_cycle(
        configured_repos=("ADAMBUILD-ai/agri-ai-business-platform", "ADAMBUILD-ai/adam-build"),
        state_dir=tmp_path,
        issue_source=source,
        callback_writer=writer,
    )

    assert len(calls) == 2
    assert len(writer.calls) == 2
    assert second == []


def test_live_cycle_duplicate_source_request_executes_once(tmp_path, monkeypatch):
    issue = _issue("ADAMBUILD-ai/adam-build", 38, "ADAM")
    source = FakeIssueSource([issue, dict(issue)])
    writer = RecordingWriter()
    calls = []

    def fake_scout(query, limit, resource):
        calls.append(query)
        return {
            "query": query,
            "search_query": query,
            "query_plan": [query],
            "resource_type": resource,
            "searched_candidate_count": 0,
            "candidate_count": 0,
            "candidates": [],
        }

    monkeypatch.setattr("src.model_scout.live_automation.run_scout_core", fake_scout)
    run_live_cycle(
        configured_repos=("ADAMBUILD-ai/adam-build",),
        state_dir=tmp_path,
        issue_source=source,
        callback_writer=writer,
    )
    assert len(calls) == 1
    assert len(writer.calls) == 1


def test_live_cycle_callback_failure_is_retry_safe(tmp_path, monkeypatch):
    issue = _issue("ADAMBUILD-ai/agri-ai-business-platform", 33, "AGRI")
    source = FakeIssueSource([issue])
    calls = []

    def fake_scout(query, limit, resource):
        calls.append(query)
        return {
            "query": query,
            "search_query": query,
            "query_plan": [query],
            "resource_type": resource,
            "searched_candidate_count": 1,
            "candidate_count": 1,
            "candidates": [{"id": "example/model", "license": "mit", "score": 1}],
        }

    class FailingWriter:
        def __call__(self, repo, issue, body):
            raise RuntimeError("temporary callback failure")

    monkeypatch.setattr("src.model_scout.live_automation.run_scout_core", fake_scout)
    first = run_live_cycle(
        configured_repos=("ADAMBUILD-ai/agri-ai-business-platform",),
        state_dir=tmp_path,
        issue_source=source,
        callback_writer=FailingWriter(),
    )
    assert len(calls) == 1
    assert any(item.get("delivered") is False for item in first)

    writer = RecordingWriter()
    second = run_live_cycle(
        configured_repos=("ADAMBUILD-ai/agri-ai-business-platform",),
        state_dir=tmp_path,
        issue_source=source,
        callback_writer=writer,
    )
    assert len(calls) == 1
    assert len(writer.calls) == 1
    assert any(item.get("state") == "DELIVERED" for item in second)
