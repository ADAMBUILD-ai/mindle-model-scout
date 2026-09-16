from __future__ import annotations

from src.model_scout import request_profiles


def test_request_profile_routes_priority_issues(monkeypatch, tmp_path):
    monkeypatch.setattr(request_profiles, "_profile_52", lambda workspace: {"issue": 52})
    monkeypatch.setattr(request_profiles, "_profile_54", lambda workspace: {"issue": 54})
    monkeypatch.setattr(request_profiles, "_profile_56", lambda workspace: {"issue": 56})

    for issue in (52, 54, 56):
        result = request_profiles.run_request_profile(
            {"request": {"source_issue": issue}},
            tmp_path,
        )
        assert result == {"issue": issue}


def test_request_profile_ignores_other_issues(tmp_path):
    assert request_profiles.run_request_profile(
        {"request": {"source_issue": 47}},
        tmp_path,
    ) is None
