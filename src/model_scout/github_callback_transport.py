from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any

import httpx


_REPO_PART = re.compile(r"^[A-Za-z0-9_.-]+$")


class GitHubCallbackTransportError(RuntimeError):
    """Raised when GitHub callback delivery fails without exposing credentials."""


def _normalize_repo(repo: str) -> tuple[str, str]:
    value = str(repo or "").strip()
    parts = value.split("/")
    if len(parts) != 2 or not all(_REPO_PART.fullmatch(part) for part in parts):
        raise ValueError("repository must be in owner/name form")
    return parts[0], parts[1]


class GitHubIssueCommentWriter:
    """Concrete callback writer for GitHub Issue comments.

    The object is callable and therefore satisfies callback_delivery.CallbackWriter.
    Authentication stays at the transport boundary: callers may inject a token directly
    or rely on GITHUB_TOKEN. The API base may be injected or read from GITHUB_API_URL.
    Error messages intentionally omit response bodies and request headers so credentials
    cannot be echoed into queue Evidence.
    """

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
            raise ValueError("GitHub callback token is required")

        resolved_base = str(api_base or os.getenv("GITHUB_API_URL") or "https://api.github.com").strip()
        if not resolved_base.startswith(("https://", "http://")):
            raise ValueError("GitHub API base must be an http(s) URL")

        self._token = resolved_token
        self._api_base = resolved_base.rstrip("/")
        self._timeout = float(timeout)
        self._client = client

    def _post(self, url: str, *, body: str) -> httpx.Response:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "mindle-model-scout",
        }
        if self._client is not None:
            return self._client.post(url, headers=headers, json={"body": body}, timeout=self._timeout)
        with httpx.Client(timeout=self._timeout) as client:
            return client.post(url, headers=headers, json={"body": body})

    def __call__(self, repo: str, issue: int, body: str) -> Mapping[str, Any]:
        owner, name = _normalize_repo(repo)
        try:
            issue_number = int(issue)
        except (TypeError, ValueError) as exc:
            raise ValueError("issue number must be an integer") from exc
        if issue_number <= 0:
            raise ValueError("issue number must be positive")
        callback_body = str(body or "")
        if not callback_body.strip():
            raise ValueError("callback body is required")

        url = f"{self._api_base}/repos/{owner}/{name}/issues/{issue_number}/comments"
        try:
            response = self._post(url, body=callback_body)
        except httpx.HTTPError as exc:
            raise GitHubCallbackTransportError(
                f"GitHub callback transport failed: {type(exc).__name__}"
            ) from None

        if not 200 <= response.status_code < 300:
            raise GitHubCallbackTransportError(
                f"GitHub callback rejected with HTTP {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError:
            raise GitHubCallbackTransportError("GitHub callback returned invalid JSON") from None
        if not isinstance(payload, dict) or payload.get("id") is None:
            raise GitHubCallbackTransportError("GitHub callback response is missing comment id")

        result: dict[str, Any] = {"id": payload["id"]}
        if payload.get("html_url"):
            result["html_url"] = payload["html_url"]
        return result
