from dataclasses import replace
import pytest
from src.model_scout.request_queue import normalize_request
from src.model_scout.runtime_executors import classify_executor_kind
from src.model_scout.scout import _query_plan, _capability_compatible, scout
from src.model_scout.requirements import parse_requirement

CAPABILITY = 'AURA_GENERATIVE_ARCHITECTURAL_CORPUS_ANALYSIS_MODEL'

@pytest.mark.parametrize('prose', ['pin revision', 'preview revision license', 'drawing-proof requirements; OCR is unrelated', 'embedding is not the requested model'])
def test_explicit_text_identity_outranks_incidental_prose(prose):
    request = replace(normalize_request(project='AURA', request_text=prose),
                      requested_capability=CAPABILITY, requested_model_family='GENERATIVE_TEXT_REASONING')
    assert classify_executor_kind(request) == 'huggingface-model'

@pytest.mark.parametrize('prose', ['pin revision', 'preview license', 'supervision required'])
def test_revision_is_not_vision(prose):
    assert classify_executor_kind(normalize_request(project='TEST', request_text=prose)) == 'huggingface-model'

def test_family_and_explicit_task_override_prose():
    request = replace(normalize_request(project='TEST', request_text='OCR in license prose'),
                      requested_model_family='GENERATIVE_TEXT_REASONING', acceptance_criteria='Task: text-generation; JSON only')
    assert classify_executor_kind(request) == 'huggingface-model'

def test_exact_capability_plan_never_contains_body_or_repo_paths():
    raw = f'{CAPABILITY}\nTask: text generation\nCallback ADAMBUILD-ai/aura-engine\n' + 'pin revision; architectural visual understanding. ' * 200
    plan = _query_plan(parse_requirement(raw))
    assert plan == ['Korean', 'multilingual', 'task:text-generation']
    assert all(len(query) < 64 for query in plan)
    assert _capability_compatible({'pipeline_tag':'text-generation'}, raw)
    assert not _capability_compatible({'pipeline_tag':'image-to-text'}, raw)
    assert not _capability_compatible({'pipeline_tag':'feature-extraction'}, raw)

def test_actual_scout_filters_wrong_modality_without_weakening_contract(monkeypatch):
    import importlib
    module = importlib.import_module('src.model_scout.scout')
    calls = []
    models = [dict(model_id='test/'+task, pipeline_tag=task, downloads=100, likes=1,
                   library_name='transformers', license='apache-2.0', languages=['ko','en'],
                   revision='a'*40) for task in ['text-generation','image-to-text','feature-extraction']]
    def search(query, limit):
        calls.append(query)
        return models
    monkeypatch.setattr(module, 'search_huggingface', search)
    monkeypatch.setattr(module, 'search_huggingface_task', lambda task,limit:search('task:'+task,limit))
    raw = f'{CAPABILITY} commercial Korean English Transformers; license; revision; OCR historical reference'
    result = scout(raw)
    assert calls == ['Korean','multilingual','task:text-generation']
    assert result['candidate_count'] == 1
    assert result['candidates'][0]['pipeline_tag'] == 'text-generation'
    assert result['requirement_profile']['commercial_use']
    assert result['requirement_profile']['license_required']
    assert result['requirement_profile']['explicit_model_ids'] == []
    assert result['query'] == raw


def test_aura_never_runs_generic_sentiment_worker(tmp_path):
    from src.model_scout.runtime_executors import RuntimeExecutorRegistry
    from src.model_scout.runtime_validation import RuntimeInputUnavailable
    class WrongWorker:
        def run(self, *args, **kwargs):
            raise AssertionError("sentiment worker must not run")
    request = replace(normalize_request(project='AURA', request_text='text generation'),
                      requested_capability=CAPABILITY)
    registry = RuntimeExecutorRegistry({'huggingface-model': WrongWorker()}, work_root=tmp_path)
    with pytest.raises(RuntimeInputUnavailable, match='generative-text executor'):
        registry(request, {'candidates': []})
