from types import SimpleNamespace
from src.model_scout.candidate_metadata import hydrate_candidates, rejection_reasons


def info(revision='a'*40,license='apache-2.0',langs=None):
    return SimpleNamespace(sha=revision,card_data={'license':license,'language':langs or ['ko','en']},
                           tags=[],siblings=[SimpleNamespace(rfilename=n) for n in ['model.safetensors','LICENSE','README.md']],
                           pipeline_tag='text-generation',library_name='transformers')


def base():
    return {'model_id':'UNIT_TEST/model','revision':'a'*40,'pipeline_tag':'text-generation',
            'license':None,'languages':[],'library_name':None}


def test_missing_list_license_is_hydrated_before_filter(tmp_path):
    calls=[]
    r=hydrate_candidates([base()],info_fetcher=lambda mid,rev:(calls.append((mid,rev)) or info()),evidence_root=tmp_path)[0]
    assert calls==[('UNIT_TEST/model','a'*40)]
    assert r['license']=='apache-2.0' and r['languages']==['en','ko']
    assert rejection_reasons(r)==[]
    assert r['metadata_evidence']['license_urls']
    assert len(list(tmp_path.glob('*.json')))==1


def test_exact_revision_mismatch_rejected(tmp_path):
    r=hydrate_candidates([base()],info_fetcher=lambda *_:info('b'*40),evidence_root=tmp_path)[0]
    assert 'REVISION_MISMATCH' in rejection_reasons(r)


def test_official_metadata_still_missing_license_rejected(tmp_path):
    r=hydrate_candidates([base()],info_fetcher=lambda *_:info(license=None),evidence_root=tmp_path)[0]
    assert 'OFFICIAL_LICENSE_MISSING' in rejection_reasons(r)


def test_korean_alone_does_not_prove_english(tmp_path):
    r=hydrate_candidates([base()],info_fetcher=lambda *_:info(langs=['ko']),evidence_root=tmp_path)[0]
    assert 'OFFICIAL_ENGLISH_EVIDENCE_MISSING' in rejection_reasons(r)


def test_missing_immutable_revision_rejected_without_network(tmp_path):
    m=base();m['revision']='main'
    r=hydrate_candidates([m],info_fetcher=lambda *_:(_ for _ in ()).throw(AssertionError('network denied')),evidence_root=tmp_path)[0]
    assert 'IMMUTABLE_REVISION_MISSING' in rejection_reasons(r)


def test_wrong_modality_rejected_without_hydration(tmp_path):
    m=base();m['pipeline_tag']='image-to-text'
    r=hydrate_candidates([m],info_fetcher=lambda *_:(_ for _ in ()).throw(AssertionError('network denied')),evidence_root=tmp_path)[0]
    assert 'TASK_NOT_TEXT_GENERATION' in rejection_reasons(r)


def test_network_failure_not_accepted(tmp_path):
    def fail(*_):raise TimeoutError()
    r=hydrate_candidates([base()],info_fetcher=fail,evidence_root=tmp_path)[0]
    assert r['hydration_status']=='METADATA_FETCH_FAILED'
    assert r['hydration_error_type']=='TimeoutError'
    assert rejection_reasons(r)


def test_noncommercial_license_never_accepted(tmp_path):
    r=hydrate_candidates([base()],info_fetcher=lambda *_:info(license='cc-by-nc-4.0'),evidence_root=tmp_path)[0]
    assert 'LICENSE_NOT_IN_APPROVED_COMMERCIAL_ALLOWLIST' in rejection_reasons(r)


def test_official_body_language_claim_hydrated_when_frontmatter_empty(tmp_path):
    obj=info();obj.card_data['language']=[]
    r=hydrate_candidates([base()],info_fetcher=lambda *_:obj,
                         card_fetcher=lambda *_:b'- Support of 119 languages and dialects with strong capabilities.',
                         evidence_root=tmp_path)[0]
    assert r['languages']==['multilingual']
    assert rejection_reasons(r)==[]
    assert r['metadata_evidence']['language_document']['sha256']


def test_negative_multilingual_claim_not_accepted():
    from src.model_scout.candidate_metadata import documented_languages
    languages,lines=documented_languages('Does not support multilingual languages.\nUnsupported languages: Korean, English.')
    assert languages==[]
