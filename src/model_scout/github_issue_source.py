from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from typing import Any

import httpx

_REPO_PART = re.compile(r"^[A-Za-z0-9_.-]+$")


class GitHubIssueSourceError(RuntimeError):
    pass


def _normalize_repo(repo: str) -> tuple[str, str]:
    value = str(repo or "").strip()
    parts = value.split("/")
    if len(parts) != 2 or not all(_REPO_PART.fullmatch(part) for part in parts):
        raise ValueError("repository must be in owner/name form")
    return parts[0], parts[1]


class GitHubIssueSource:
    """Read open GitHub Issues from configured repositories for MODEL SCOUT discovery."""

    def __init__(
        self,
        *,
        token: str | None = None,
        api_base: str | None = None,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        resolved_token = str(token or os.getenv("GITHUB_TOKEN") or "").strip()
        if not resolved_token:
            raise ValueError("GitHub issue source token is required")
        resolved_base = str(api_base or os.getenv("GITHUB_API_URL") or "https://api.github.com").strip()
        if not resolved_base.startswith(("https://", "http://")):
            raise ValueError("GitHub API base must be an http(s) URL")
        self._token = resolved_token
        self._api_base = resolved_base.rstrip("/")
        self._timeout = float(timeout)
        self._client = client

    def _get(self, url: str) -> httpx.Response:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "mindle-model-scout",
        }
        if self._client is not None:
            return self._client.get(url, headers=headers, timeout=self._timeout)
        with httpx.Client(timeout=self._timeout) as client:
            return client.get(url, headers=headers)

    def list_open_issues(self, repos: Iterable[str], *, per_page: int = 100) -> list[dict[str, Any]]:
        if per_page < 1 or per_page > 100:
            raise ValueError("per_page must be between 1 and 100")
        results: list[dict[str, Any]] = []
        for repo in repos:
            owner, name = _normalize_repo(repo)
            url = f"{self._api_base}/repos/{owner}/{name}/issues?state=open&per_page={per_page}"
            try:
                response = self._get(url)
            except httpx.HTTPError as exc:
                raise GitHubIssueSourceError(f"GitHub issue source failed: {type(exc).__name__}") from None
            if not 200 <= response.status_code < 300:
                raise GitHubIssueSourceError(f"GitHub issue source rejected with HTTP {response.status_code}")
            try:
                payload = response.json()
            except ValueError:
                raise GitHubIssueSourceError("GitHub issue source returned invalid JSON") from None
            if not isinstance(payload, list):
                raise GitHubIssueSourceError("GitHub issue source payload must be a list")
            for item in payload:
                if not isinstance(item, Mapping) or item.get("pull_request"):
                    continue
                number = item.get("number")
                title = str(item.get("title") or "")
                body = str(item.get("body") or "")
                state = str(item.get("state") or "open")
                results.append({
                    "repository_full_name": f"{owner}/{name}",
                    "number": number,
                    "title": title,
                    "body": body,
                    "state": state,
                })
        return results
