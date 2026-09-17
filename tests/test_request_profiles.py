from __future__ import annotations

from src.model_scout import request_profiles
from src.model_scout.github_request_discovery import infer_project


def test_infer_project_preserves_korean_team_name():
    assert infer_project("ADAMBUILD-ai/mindle-model-scout", "[P0][김서방] request", "") == "김서방"


def test_request_profile_routes_priority_issues(monkeypatch, tmp_path):
    monkeypatch.setattr(request_profiles, "_profile_47", lambda workspace: {"issue": 47})
    monkeypatch.setattr(request_profiles, "_profile_48", lambda workspace: {"issue": 48})
    monkeypatch.setattr(request_profiles, "_profile_49", lambda workspace: {"issue": 49})
    monkeypatch.setattr(request_profiles, "_profile_53", lambda workspace: {"issue": 53})
    monkeypatch.setattr(request_profiles, "_profile_52", lambda workspace: {"issue": 52})
    monkeypatch.setattr(request_profiles, "_profile_54", lambda workspace: {"issue": 54})
    monkeypatch.setattr(request_profiles, "_profile_56", lambda workspace: {"issue": 56})
    monkeypatch.setattr(request_profiles, "_profile_50", lambda workspace: {"issue": 50})
    monkeypatch.setattr(request_profiles, "_profile_51", lambda workspace: {"issue": 51})
    monkeypatch.setattr(request_profiles, "_profile_55", lambda workspace: {"issue": 55})
    monkeypatch.setattr(request_profiles, "_profile_57", lambda workspace: {"issue": 57})
    monkeypatch.setattr(request_profiles, "_profile_58", lambda workspace: {"issue": 58})

    for issue in (53, 47, 48, 49, 50, 51, 52, 54, 55, 56, 57, 58):
        result = request_profiles.run_request_profile(
            {"request": {"source_issue": issue}},
            tmp_path,
        )
        assert result == {"issue": issue}


def test_request_profile_ignores_other_issues(tmp_path):
    assert request_profiles.run_request_profile(
        {"request": {"source_issue": 46}},
        tmp_path,
    ) is None

