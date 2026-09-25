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


def test_intake_coverage_fails_when_team_repository_is_missing(tmp_path):
    registry = tmp_path / "teams.json"
    registry.write_text('{"teams":[{"repository_full_name":"owner/team-a"}]}', encoding="utf-8")
    result = validate_intake_coverage(["owner/other"], registry)
    assert result["status"] == "FAIL_MISSING_REPOSITORIES"
    assert result["missing_repositories"] == ["owner/team-a"]
