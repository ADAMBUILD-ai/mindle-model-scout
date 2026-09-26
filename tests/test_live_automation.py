from __future__ import annotations

import hashlib
from pathlib import Path
import pytest

from src.model_scout.github_issue_source import GitHubIssueSource
from src.model_scout.live_automation import run_live_cycle


class FakeIssueSource(GitHubIssueSource):
    def __init__(self, issues):
        self._issues = list(issues)

    def list_open_issues(self, repos, *, per_page=100):
        self.requested_repos = tuple(repos)
        return list(self._issues)

    def get_issue(self, repo, issue):
        return _issue(repo, issue, "CURRENT")


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


def test_live_cycle_ingests_central_requests_without_configuration(tmp_path, monkeypatch):
    source = FakeIssueSource([_issue("ADAMBUILD-ai/mindle-model-scout", 47, "ADAM")])
    writer = RecordingWriter()
    monkeypatch.setattr(
        "src.model_scout.live_automation.run_scout_core",
        lambda query, limit, resource: {"query": query, "candidates": []},
    )

    results = run_live_cycle(
        configured_repos=("ADAMBUILD-ai/adam-build",),
        state_dir=tmp_path,
        issue_source=source,
        callback_writer=writer,
    )

    assert "ADAMBUILD-ai/mindle-model-scout" in source.requested_repos
    assert any(item.get("state") == "DELIVERED" for item in results)


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


def test_live_cycle_processes_current_event_before_older_requests(tmp_path, monkeypatch):
    older = _issue("ADAMBUILD-ai/mindle-model-scout", 60, "OLDER")
    current = _issue("ADAMBUILD-ai/mindle-model-scout", 71, "CURRENT")
    current["body"] += "\nunique current event query"
    source = FakeIssueSource([older, current])
    order = []

    def fake_scout(query, limit, resource):
        order.append(query)
        return {"query": query, "candidates": []}

    monkeypatch.setattr("src.model_scout.live_automation.run_scout_core", fake_scout)
    run_live_cycle(
        configured_repos=("ADAMBUILD-ai/mindle-model-scout",),
        state_dir=tmp_path,
        issue_source=source,
        callback_writer=RecordingWriter(),
        preferred_source=("ADAMBUILD-ai/mindle-model-scout", 71),
    )

    assert order[0] == " ".join(current["body"].split())


def test_live_cycle_fetches_current_event_when_list_snapshot_omits_it(tmp_path, monkeypatch):
    source = FakeIssueSource([_issue("ADAMBUILD-ai/mindle-model-scout", 60, "OLDER")])
    calls = []
    monkeypatch.setattr(
        "src.model_scout.live_automation.run_scout_core",
        lambda query, limit, resource: calls.append(query) or {"query": query, "candidates": []},
    )

    run_live_cycle(
        configured_repos=("ADAMBUILD-ai/mindle-model-scout",),
        state_dir=tmp_path,
        issue_source=source,
        callback_writer=RecordingWriter(),
        preferred_source=("ADAMBUILD-ai/mindle-model-scout", 71),
    )

    expected = _issue("ADAMBUILD-ai/mindle-model-scout", 71, "CURRENT")["body"]
    assert calls[0] == " ".join(expected.split())


def test_live_cycle_bounds_work_and_prioritizes_p0(tmp_path, monkeypatch):
    low = _issue("ADAMBUILD-ai/mindle-model-scout", 80, "LOW")
    low["title"] = "[P3][LOW] MODEL SCOUT request"
    high = _issue("ADAMBUILD-ai/mindle-model-scout", 81, "HIGH")
    calls = []
    monkeypatch.setattr(
        "src.model_scout.live_automation.run_scout_core",
        lambda query, limit, resource: calls.append(query) or {"query": query, "candidates": []},
    )
    run_live_cycle(
        configured_repos=("ADAMBUILD-ai/mindle-model-scout",),
        state_dir=tmp_path,
        issue_source=FakeIssueSource([low, high]),
        callback_writer=RecordingWriter(),
        max_requests=1,
    )
    assert calls == [" ".join(high["body"].split())]


def test_scoped_real_issue_executes_once_after_parent_is_terminal_or_delivered(tmp_path, monkeypatch):
    issue = _issue("ADAMBUILD-ai/mindle-model-scout", 51, "KIMSERV")
    issue["body"] += "\nmemory retrieval requested"
    source = FakeIssueSource([issue])
    calls = []
    monkeypatch.setattr("src.model_scout.live_automation.run_scout_core", lambda query, limit, resource:
                        calls.append(query) or {"query": query, "candidates": []})
    args = dict(configured_repos=("ADAMBUILD-ai/mindle-model-scout",), state_dir=tmp_path,
                issue_source=source, callback_writer=RecordingWriter())
    run_live_cycle(**args)  # prior broad request is already completed
    scope = {"source_repo": "ADAMBUILD-ai/mindle-model-scout", "source_issue": 51,
             "model_id": "intfloat/multilingual-e5-small", "capability": "memory"}
    result = run_live_cycle(**args, scoped_requests=[scope])
    assert sum(item.get("state") == "DELIVERED" for item in result) == 1
    assert "intfloat/multilingual-e5-small" in calls[-1]
    assert "embedding retrieval" in calls[-1]
    assert run_live_cycle(**args, scoped_requests=[scope]) == []


def test_scoped_request_requires_open_matching_real_issue(tmp_path, monkeypatch):
    source = FakeIssueSource([])
    monkeypatch.setattr("src.model_scout.live_automation.run_scout_core", lambda *args: pytest.fail("must not run"))
    result = run_live_cycle(configured_repos=("ADAMBUILD-ai/mindle-model-scout",), state_dir=tmp_path,
                            issue_source=source, callback_writer=RecordingWriter(),
                            scoped_requests=[{"source_repo": "ADAMBUILD-ai/mindle-model-scout", "source_issue": 51,
                                              "model_id": "intfloat/multilingual-e5-small", "capability": "memory"}])
    assert result == []
