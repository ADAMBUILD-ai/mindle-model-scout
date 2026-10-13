import json
from scripts.audit_aura136_runner_assets import PINS, inspect


def test_missing_asset_is_explicit_and_no_model_calls(tmp_path):
    result = inspect(tmp_path, [tmp_path / 'hub'])
    assert all(m['status'] == 'NOT_FOUND_IN_BOUNDED_RUNNER_SCOPE' for m in result['models'])
    assert result['modelCalls'] == 0
    assert not result['productPass']


def test_only_exact_identity_and_existing_file_bytes_observed(tmp_path):
    model, rev = next(iter(PINS.items()))
    root = tmp_path / 'hub' / ('models--' + model.replace('/', '--')) / 'snapshots' / rev
    root.mkdir(parents=True)
    (root / 'config.json').write_text('{}')
    result = inspect(tmp_path, [tmp_path / 'hub'])
    match = next(row for row in result['models'] if row['modelId'] == model)
    assert match['snapshots'][0]['files'][0]['bytes'] == 2
    assert match['status'] == 'EXISTING_BYTES_OBSERVED'
    assert not result['productPass']
