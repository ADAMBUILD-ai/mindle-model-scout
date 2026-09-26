from __future__ import annotations

import httpx

from src.model_scout.github_issue_source import GitHubIssueSource


def test_fetches_all_open_issue_pages_without_pull_requests():
    seen = []

    def handle(request):
        seen.append(str(request.url))
        if "page=2" in str(request.url):
            return httpx.Response(200, json=[{"number": 102, "title": "MODEL SCOUT", "body": "request", "state": "open"}])
        return httpx.Response(200, headers={"Link": '<https://api.github.test/repos/owner/repo/issues?state=open&per_page=100&page=2>; rel="next"'},
                              json=[{"number": 101, "title": "MODEL SCOUT", "body": "request", "state": "open"},
                                    {"number": 100, "pull_request": {"url": "ignored"}}])

    source = GitHubIssueSource(client=httpx.Client(transport=httpx.MockTransport(handle)),
                               api_base="https://api.github.test")
    issues = source.list_open_issues(["owner/repo"])
    assert [item["number"] for item in issues] == [101, 102]
    assert len(seen) == 2
    assert source.repository_diagnostics[0]["page_count"] == 2
    assert source.repository_diagnostics[0]["open_issue_count"] == 2


def test_second_page_failure_does_not_claim_partial_repository_as_complete():
    def handle(request):
        if "page=2" in str(request.url):
            return httpx.Response(404)
        return httpx.Response(200, headers={"Link": '<https://api.github.test/repos/owner/repo/issues?state=open&per_page=100&page=2>; rel="next"'},
                              json=[{"number": 101, "title": "MODEL SCOUT", "body": "request", "state": "open"}])

    source = GitHubIssueSource(client=httpx.Client(transport=httpx.MockTransport(handle)),
                               api_base="https://api.github.test")
    assert source.list_open_issues(["owner/repo"]) == []
    assert source.repository_failures[0]["status_code"] == 404
