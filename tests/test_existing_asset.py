import hashlib
import pytest
from scripts.verify_existing_model_asset import verify


def test_missing_tampered_and_unlisted_files_block(tmp_path):
    model = {'modelId': 'existing/model', 'files': [{'path': 'weights', 'bytes': 3, 'sha256': hashlib.sha256(b'abc').hexdigest()}]}
    assert verify(model, tmp_path)['status'].startswith('BLOCKED')
    (tmp_path / 'weights').write_bytes(b'abc')
    assert verify(model, tmp_path)['status'] == 'FILES_VERIFIED_NOT_PRODUCT_PASS'
    (tmp_path / 'extra').write_bytes(b'x')
    assert verify(model, tmp_path)['status'].startswith('BLOCKED')
    (tmp_path / 'extra').unlink()
    (tmp_path / 'weights').write_bytes(b'xyz')
    assert verify(model, tmp_path)['status'].startswith('BLOCKED')


def test_manifest_cannot_escape_root(tmp_path):
    with pytest.raises(ValueError, match='escapes'):
        verify({'modelId': 'existing/model', 'files': [{'path': '../outside'}]}, tmp_path)
