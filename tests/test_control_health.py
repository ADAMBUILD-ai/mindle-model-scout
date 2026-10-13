from src.model_scout.github_request_discovery import normalize_github_issue_request
from src.model_scout.autonomous_runner import summarize_operational_health
from src.model_scout.persistent_queue import PersistentRequestQueue
from src.model_scout.request_queue import normalize_request


def test_control_directive_never_becomes_model_search():
    repo = 'ADAMBUILD-ai/mindle-model-scout'
    issue = {'repository_full_name': repo, 'number': 139, 'state': 'open',
             'title': '[CONTROL][P0][AURA #136] Final generative analysis delivery execution owner',
             'body': 'MODEL SCOUT generative model embedding OCR forbidden'}
    assert normalize_github_issue_request(issue, configured_repos=[repo]) is None
    issue['number'] = 136
    issue['title'] = '[P0][AURA] Model Scout Request'
    assert normalize_github_issue_request(issue, configured_repos=[repo]) is not None


def test_legacy_control_queue_quarantined_once_without_search(tmp_path):
    queue = PersistentRequestQueue(tmp_path / 'queue.sqlite3')
    envelope, _ = queue.enqueue(normalize_request(project='AURA', request_text='control',
        source_repo='ADAMBUILD-ai/mindle-model-scout', source_issue=139))
    assert queue.quarantine_misrouted([('ADAMBUILD-ai/mindle-model-scout', 139)]) == [envelope.fingerprint]
    assert queue.get(envelope.fingerprint).state.value == 'MISROUTED'
    assert queue.quarantine_misrouted([('ADAMBUILD-ai/mindle-model-scout', 139)]) == []


def test_successful_idle_does_not_hide_block_or_acquisition():
    report = summarize_operational_health([
        {'state': 'BLOCKED_INPUT', 'source_issue': 136, 'last_error': 'classifier-only'},
        {'state': 'ACQUIRED_VERIFIED', 'source_issue': 35},
        {'state': 'SUPERSEDED', 'source_issue': 1}], {'status': 'PASS'})
    assert report['status'] == 'ACTION_REQUIRED'
    assert report['unresolved_request_count'] == 2
    assert report['requests'][0]['exact_error'] == 'classifier-only'
    assert not report['process_success_is_product_pass']
