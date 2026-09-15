from __future__ import annotations

import json

import httpx

from src.model_scout.callback_delivery import deliver_evidence
from src.model_scout.github_callback_transport import (
    GitHubCallbackTransportError,
    GitHubIssueCommentWriter,
)
from src.model_scout.request_queue import QueueState, RequestQueue, normalize_request


def _mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def _ready_delivery():
    envelope = normalize_request(
        project="AGRI",
        request_text="Find Hugging Face models for Korean agricultural RAG",
        resource="model",
        priority="P0",
        source_repo="ADAMBUILD-ai/agri-ai-business-platform",
        source_issue=33,
    )
    queue = RequestQueue()
    queued, _ = queue.enqueue(envelope)
    queue.set_state(queued.fingerprint, QueueState.RUNNING)
    ready = queue.set_state(queued.fingerprint, QueueState.EVIDENCE_READY)
    evidence = {
        "fingerprint": ready.fingerprint,
        "state": ready.state.value,
        "requested_resource": "model",
        "dispatched_resource": "model",
        "callback": {"repo": ready.callback_repo, "issue": ready.callback_issue},
        "result": {"candidate_count": 2, "query": "agricultural RAG"},
    }
    return queue, ready, evidence


def test_writer_posts_issue_comment_with_expected_auth_and_url():
    seen = {}

    def handler(request):
        seen["request"] = request
        return httpx.Response(
            201,
            json={"id": 1234, "html_url": "https://github.example/comment/1234"},
            request=request,
        )

    with _mock_client(handler) as client:
        writer = GitHubIssueCommentWriter(
            token="secret-token",
            api_base="https://api.github.test",
            client=client,
        )
        result = writer("ADAMBUILD-ai/agri-ai-business-platform", 33, "verified evidence")

    request = seen["request"]
    assert request.url == httpx.URL(
        "https://api.github.test/repos/ADAMBUILD-ai/agri-ai-business-platform/issues/33/comments"
    )
    assert request.headers["authorization"] == "Bearer secret-token"
    assert request.headers["accept"] == "application/vnd.github+json"
    assert request.headers["x-github-api-version"] == "2022-11-28"
    assert json.loads(request.content) == {"body": "verified evidence"}
    assert result["id"] == 1234


def test_non_2xx_errors_are_sanitized_and_do_not_echo_secret():
    secret = "super-secret-token"

    for status in (401, 403, 404, 500):
        def handler(request, status=status):
            return httpx.Response(
                status,
                json={"message": f"rejected token={secret}"},
                request=request,
            )

        with _mock_client(handler) as client:
            writer = GitHubIssueCommentWriter(token=secret, client=client)
            try:
                writer("ADAMBUILD-ai/project", 7, "evidence")
            except GitHubCallbackTransportError as exc:
                message = str(exc)
                assert str(status) in message
                assert secret not in message
            else:
                raise AssertionError(f"HTTP {status} must fail")


def test_network_error_is_sanitized_and_does_not_echo_secret():
    secret = "super-secret-token"

    def handler(request):
        raise httpx.ConnectError(f"socket failed token={secret}", request=request)

    with _mock_client(handler) as client:
        writer = GitHubIssueCommentWriter(token=secret, client=client)
        try:
            writer("ADAMBUILD-ai/project", 7, "evidence")
        except GitHubCallbackTransportError as exc:
            assert "ConnectError" in str(exc)
            assert secret not in str(exc)
        else:
            raise AssertionError("network failure must fail")


def test_delivery_moves_to_delivered_only_after_real_transport_success():
    queue, ready, evidence = _ready_delivery()

    def handler(request):
        return httpx.Response(201, json={"id": 91}, request=request)

    with _mock_client(handler) as client:
        writer = GitHubIssueCommentWriter(token="token", client=client)
        result = deliver_evidence(queue, ready.fingerprint, evidence, writer=writer)

    assert result["delivered"] is True
    assert result["state"] == QueueState.DELIVERED.value
    assert queue.get(ready.fingerprint).state == QueueState.DELIVERED


def test_transport_failure_keeps_evidence_ready_and_retry_can_deliver():
    queue, ready, evidence = _ready_delivery()
    secret = "retry-secret"

    def fail_handler(request):
        return httpx.Response(
            503,
            json={"message": f"temporary failure token={secret}"},
            request=request,
        )

    with _mock_client(fail_handler) as client:
        writer = GitHubIssueCommentWriter(token=secret, client=client)
        failed = deliver_evidence(queue, ready.fingerprint, evidence, writer=writer)

    assert failed["delivered"] is False
    assert failed["state"] == QueueState.EVIDENCE_READY.value
    assert secret not in failed["error"]
    assert queue.get(ready.fingerprint).state == QueueState.EVIDENCE_READY

    def success_handler(request):
        return httpx.Response(201, json={"id": 92}, request=request)

    with _mock_client(success_handler) as client:
        retry_writer = GitHubIssueCommentWriter(token=secret, client=client)
        delivered = deliver_evidence(queue, ready.fingerprint, evidence, writer=retry_writer)

    assert delivered["delivered"] is True
    assert delivered["state"] == QueueState.DELIVERED.value
    assert queue.get(ready.fingerprint).state == QueueState.DELIVERED
