from __future__ import annotations

from scripts.run_priority_e2e import FilteredIssueSource


class _Source:
    def list_open_issues(self, repos):
        return [
            {"repository_full_name": "ADAMBUILD-ai/mindle-model-scout", "number": 52},
            {"repository_full_name": "ADAMBUILD-ai/mindle-model-scout", "number": 54},
            {"repository_full_name": "ADAMBUILD-ai/other", "number": 52},
        ]


def test_filtered_issue_source_keeps_only_requested_central_issues():
    source = FilteredIssueSource(_Source(), {52})

    assert source.list_open_issues(["ignored"]) == [
        {"repository_full_name": "ADAMBUILD-ai/mindle-model-scout", "number": 52}
    ]
