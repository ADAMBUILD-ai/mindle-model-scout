import json

import httpx
import pytest

from scripts.check_discovery_access import main
from src.model_scout.github_issue_source import GitHubIssueSource


def test_bad_cross_repo_token_does_not_disable_local_intake_or_retry_anonymously():
    seen = []

    def handle(request):
        seen.append((request.url.path, request.headers.get("Authorization")))
        if request.headers.get("Authorization") == "Bearer expired":
            return httpx.Response(401)
        if request.url.path.endswith("/136"):
            return httpx.Response(200, json={"number": 136, "title": "MODEL SCOUT", "body": "request"})
        return httpx.Response(200, json=[{"number": 136, "title": "MODEL SCOUT", "body": "request"}])

    source = GitHubIssueSource(token="expired", local_token="workflow", local_repository="Owner/Central",
                               client=httpx.Client(transport=httpx.MockTransport(handle)))
    issues = source.list_open_issues(["owner/central", "owner/aura"])
    assert [(x["repository_full_name"], x["number"]) for x in issues] == [("owner/central", 136)]
    assert seen == [("/repos/owner/central/issues", "Bearer workflow"), ("/repos/owner/aura/issues", "Bearer expired")]
    assert source.repository_failures[0]["status_code"] == 401
    assert source.get_issue("OWNER/CENTRAL", 136)["number"] == 136


@pytest.mark.parametrize("access,expected", [
    ({"status": "PASS", "failed_repositories": []}, 0),
    ({"status": "DEGRADED_REPOSITORY_ACCESS", "failed_repositories": [{"status_code": 401}]}, 1),
    ({"status": "PASS", "failed_repositories": [{"status_code": 403}]}, 1),
    ({"status": "DEGRADED_REPOSITORY_ACCESS", "failed_repositories": [{"status_code": 500}]}, 1),
    ({}, 1),
])
def test_failed_intake_cannot_have_green_exit(tmp_path, access, expected):
    path = tmp_path / "cycle.json"
    path.write_text(json.dumps({"discovery_access": access}), encoding="utf-8")
    assert main(str(path)) == expected


def test_missing_evidence_is_failure(tmp_path):
    assert main(str(tmp_path / "missing.json")) == 1
