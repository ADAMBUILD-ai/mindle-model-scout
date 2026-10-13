import pytest
import io
import hashlib
from scripts.acquire_aura136_pinned_qwen4b import fetch, git_blob_sha
from scripts.acquire_aura136_pinned_qwen4b import FILES, WEIGHTS, REVISION, validate_metadata


def official():
    return {'sha': REVISION, 'pipeline_tag': 'text-generation', 'cardData': {'license': 'apache-2.0'}, 'siblings': [{'rfilename': name, 'lfs': {'size': WEIGHTS[name][0], 'sha256': WEIGHTS[name][1]} if name in WEIGHTS else {}} for name in FILES]}


def test_only_exact_historical_candidate_allowed():
    validate_metadata(official())
    changed = official()
    changed['sha'] = 'main'
    with pytest.raises(ValueError, match='immutable'):
        validate_metadata(changed)


def test_no_changed_weight_license_or_missing_loader_allowed():
    changed = official()
    changed['siblings'][-1]['lfs']['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='LFS'):
        validate_metadata(changed)
    changed = official()
    changed['cardData']['license'] = 'unknown'
    with pytest.raises(ValueError, match='license'):
        validate_metadata(changed)
    changed = official()
    changed['siblings'].pop(0)
    with pytest.raises(ValueError, match='incomplete'):
        validate_metadata(changed)


def test_nonweight_reuse_requires_official_git_blob(tmp_path, monkeypatch):
    path = tmp_path / 'config.json'
    path.write_bytes(b'{}')
    official = {'blobId': git_blob_sha(path)}
    def forbid(*args, **kwargs):
        raise AssertionError('verified existing file should not download')
    monkeypatch.setattr('urllib.request.urlopen', forbid)
    assert fetch(tmp_path, 'config.json', official)['bytes'] == 2
    path.write_bytes(b'tampered')
    monkeypatch.setattr('urllib.request.urlopen', lambda *args, **kwargs: io.BytesIO(b'{}'))
    assert fetch(tmp_path, 'config.json', official)['sha256']
    assert path.read_bytes() == b'{}'


def test_lfs_tokenizer_is_verified_by_body_digest_and_stage_reused(tmp_path, monkeypatch):
    body = b'{"tokenizer":"pinned-existing-lfs-body"}'
    staged = tmp_path / 'tokenizer.json.acquiring'
    staged.write_bytes(body)
    metadata = {'blobId': 'pointer-is-not-body-sha', 'lfs': {'size': len(body), 'sha256': hashlib.sha256(body).hexdigest()}}
    def forbid(*args, **kwargs):
        raise AssertionError('matching staged LFS body must be reused')
    monkeypatch.setattr('urllib.request.urlopen', forbid)
    record = fetch(tmp_path, 'tokenizer.json', metadata)
    assert record['sha256'] == metadata['lfs']['sha256']
    assert not staged.exists()
    assert (tmp_path / 'tokenizer.json').read_bytes() == body
