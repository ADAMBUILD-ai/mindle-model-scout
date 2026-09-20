from __future__ import annotations

from scripts.run_ssot_priority_e2e import local_candidate_search


def test_local_candidate_search_keeps_issue_specific_candidates():
    cases = {
        "MODEL SCOUT 즉시 실행 요청 — AURA": "google/siglip-base-patch16-224",
        "MODEL SCOUT 즉시 실행 요청 — ADAM\n": "trimesh + Pillow",
        "MODEL SCOUT 즉시 실행 요청 — AVORA": "PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx",
        "MODEL SCOUT 즉시 실행 요청 — ADRAW": "trimesh.section",
    }
    for query, expected in cases.items():
        result = local_candidate_search(query, 10, "all")
        assert result["candidate_count"] > 0
        assert expected in result["candidates"][0]["id"]


def test_local_candidate_search_never_claims_found_without_candidates():
    result = local_candidate_search("unknown request", 10, "all")
    assert result["candidate_count"] == 0
    assert result["candidates"] == []


def test_local_candidate_search_uses_heading_not_cross_team_body_mentions():
    result = local_candidate_search(
        "## MODEL SCOUT 즉시 실행 요청 — ADRAW\nAVORA와의 입력/출력 연계 포맷 제안 포함",
        10,
        "all",
    )

    assert result["candidate_count"] == 1
    assert result["candidates"][0]["id"] == "trimesh.section + ezdxf + SVG"

