from src.model_scout.autonomous_runner import run_autonomous_cycle, validate_intake_coverage
from src.model_scout.delivery_ledger import DeliveryLedger, DeliveryState

def test_delivery_ledger_requires_owner_and_next_action(tmp_path):
    ledger = DeliveryLedger(tmp_path / "delivery.sqlite3")
    requested = ledger.request("request-1", owner="team-a", next_action="find candidate")
    found = ledger.advance("request-1", DeliveryState.FOUND, owner="scout", next_action="download candidate", evidence={"candidate": "a/model"})
    assert requested.state == DeliveryState.REQUESTED
    assert found.state == DeliveryState.FOUND
    assert found.owner == "scout"


def test_autonomous_cycle_requeues_stale_work_before_processing(tmp_path, monkeypatch):
    import src.model_scout.autonomous_runner as runner

    monkeypatch.setattr(runner, "run_live_cycle", lambda **_kwargs: [])
    result = run_autonomous_cycle(configured_repos=["owner/repo"], state_dir=tmp_path / "durable")
    assert result["watchdog_requeued"] == []
    assert result["discovery_diagnostics"] == {}


def test_autonomous_watchdog_runs_after_live_issue_reconciliation(tmp_path, monkeypatch):
    import src.model_scout.autonomous_runner as runner
    from src.model_scout.persistent_queue import PersistentRequestQueue
    from src.model_scout.request_queue import normalize_request

    root = tmp_path / "durable"
    queue = PersistentRequestQueue(root / "request_queue.sqlite3", clock=lambda: 1.0)
    old, _ = queue.enqueue(normalize_request(
        project="AVORA", request_text="old model request", source_repo="owner/repo", source_issue=115))
    observed = []

    def fake_cycle(**kwargs):
        current = PersistentRequestQueue(root / "request_queue.sqlite3")
        canonical = normalize_request(
            project="AVORA", resource="tool", request_text="new render request",
            source_repo="owner/repo", source_issue=115)
        current.supersede_obsolete([canonical])
        kwargs["before_dispatch"]()
        observed.append(current.get(old.fingerprint).state.value)
        return []

    monkeypatch.setattr(runner, "run_live_cycle", fake_cycle)
    result = run_autonomous_cycle(configured_repos=["owner/repo"], state_dir=root)
    assert observed == ["SUPERSEDED"]
    assert result["watchdog_requeued"] == []
    assert result["eligible_request_count"] == 0


def test_intake_coverage_auto_completes_when_team_repository_is_missing(tmp_path):
    registry = tmp_path / "teams.json"
    registry.write_text('{"teams":[{"repository_full_name":"owner/team-a"}]}', encoding="utf-8")
    result = validate_intake_coverage(["owner/other"], registry)
    assert result["status"] == "PASS_AUTO_COMPLETED_FROM_TEAM_REGISTRY"
    assert result["missing_repositories"] == ["owner/team-a"]
    assert result["auto_completed_repositories"] == ["owner/team-a"]
    assert result["effective_repositories"] == [
        "adambuild-ai/mindle-model-scout",
        "owner/other",
        "owner/team-a",
    ]


def test_autonomous_cycle_uses_registry_repositories_when_variable_is_empty(tmp_path, monkeypatch):
    import src.model_scout.autonomous_runner as runner

    registry = tmp_path / "teams.json"
    registry.write_text('{"teams":[{"repository_full_name":"owner/team-a"}]}', encoding="utf-8")
    captured = {}

    def fake_cycle(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(runner, "run_live_cycle", fake_cycle)
    result = run_autonomous_cycle(
        configured_repos=[],
        state_dir=tmp_path / "durable",
        team_registry_path=registry,
    )
    assert "owner/team-a" in captured["configured_repos"]
    assert result["intake_coverage"]["status"] == "PASS_AUTO_COMPLETED_FROM_TEAM_REGISTRY"


def test_autonomous_idle_reports_repository_access_failure_instead_of_healthy_idle(tmp_path, monkeypatch):
    import src.model_scout.autonomous_runner as runner

    def fake_cycle(**kwargs):
        kwargs["discovery_diagnostics"]["repository_failures"] = [{
            "repository_full_name": "owner/private-team",
            "status_code": 404,
            "reason": "repository_issue_discovery_rejected",
        }]
        return []

    monkeypatch.setattr(runner, "run_live_cycle", fake_cycle)
    result = run_autonomous_cycle(configured_repos=["owner/private-team"], state_dir=tmp_path / "durable")
    assert result["idle_reason"] == "DISCOVERY_PARTIAL_FAILURE"
    assert result["discovery_access"]["status"] == "DEGRADED_REPOSITORY_ACCESS"
    assert result["discovery_access"]["failed_repositories"][0]["status_code"] == 404
