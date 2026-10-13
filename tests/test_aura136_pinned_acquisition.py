import pytest
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
