from src.model_scout.autonomous_runner import run_autonomous_cycle
from src.model_scout.delivery_ledger import DeliveryLedger, DeliveryState
from src.model_scout.requirements import parse_requirement


def test_adam_38_provider_intent_wins_over_context_words():
    profile = parse_requirement(
        "Stage 3 surrounding buildings terrain context. Render provider shopping for final GLB/GLTF and deterministic local rendering."
    )
    assert profile["semantic_intent"] == "3d_render_provider"
    assert profile["query"] == "glb gltf render provider"


def test_adam_39_placement_and_40_context_remain_distinct():
    placement = parse_requirement("building footprint placement drawing transform assist")
    context = parse_requirement("surrounding buildings terrain context modeling")
    assert placement["semantic_intent"] == "3d_placement"
    assert context["semantic_intent"] == "3d_context"


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
