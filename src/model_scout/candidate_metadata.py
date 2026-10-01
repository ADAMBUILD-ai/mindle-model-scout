"""Exact-revision evidence hydration before AURA candidate qualification."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import os
import re
import urllib.request
from .acquisition import ALLOWED_LICENSES

AURA_QUERIES = ['Korean', 'multilingual Instruct', 'long-context', 'Instruct', 'Qwen3']


def documented_languages(model_card):
    evidence = []
    languages = set()
    for line in model_card.splitlines():
        lowered = re.sub(r'[*_`]', '', line.casefold())
        if any(word in lowered for word in ('not support', 'unsupported', 'does not', 'no support', 'lacks multilingual', 'without multilingual')):
            continue
        if 'language' not in lowered:
            continue
        claim = re.search(r'multilingual support|multilingual instruction|support (?:of |for |over |more than )*\d+\+? languages', lowered)
        if claim:
            languages.add('multilingual')
            evidence.append(lowered[max(0, claim.start()-30):claim.end()+120])
        if 'including' in lowered or 'supported languages' in lowered:
            if 'korean' in lowered:
                languages.add('ko')
            if 'english' in lowered:
                languages.add('en')
            if 'ko' in languages or 'en' in languages:
                evidence.append(line[:256])
    return sorted(languages), evidence


def _fetch_card(mid, revision):
    url = f'https://huggingface.co/{mid}/resolve/{revision}/README.md'
    with urllib.request.urlopen(url, timeout=12) as response:
        data = response.read(1048577)
    if len(data) > 1048576:
        raise ValueError('MODEL_CARD_OVERSIZE')
    return data


def hydrate_candidates(models, *, info_fetcher=None, evidence_root=None, card_fetcher=None):
    if info_fetcher is None:
        from huggingface_hub import HfApi
        api = HfApi(token=False)
        info_fetcher = lambda mid, rev: api.model_info(mid, revision=rev, files_metadata=True)
    root = Path(evidence_root or os.environ.get('MODEL_SCOUT_METADATA_EVIDENCE_DIR') or
                (Path(os.environ['MODEL_SCOUT_STATE_DIR']) / 'metadata-evidence'
                 if os.environ.get('MODEL_SCOUT_STATE_DIR') else Path('.model-scout-evidence/metadata')))
    root.mkdir(parents=True, exist_ok=True)
    card_fetcher = card_fetcher or _fetch_card

    def hydrate(model):
        result = dict(model)
        mid, revision = str(model.get('model_id') or ''), str(model.get('revision') or '')
        if model.get('pipeline_tag') != 'text-generation':
            result['hydration_status'] = 'WRONG_TASK'
            return result
        if not re.fullmatch('[0-9a-f]{40}', revision):
            result['hydration_status'] = 'IMMUTABLE_REVISION_MISSING'
            return result
        try:
            info = info_fetcher(mid, revision)
            if str(info.sha).casefold() != revision.casefold():
                result['hydration_status'] = 'REVISION_MISMATCH'
                return result
            card = getattr(info, 'card_data', None)
            card = card.to_dict() if hasattr(card, 'to_dict') else card
            card = card if isinstance(card, dict) else {}
            tags = list(getattr(info, 'tags', None) or [])
            license_name = card.get('license')
            if not isinstance(license_name, str):
                license_name = next((t.split(':', 1)[1] for t in tags if t.startswith('license:')), None)
            languages = card.get('language') or card.get('languages') or []
            languages = [languages] if isinstance(languages, str) else languages
            languages = [str(x).casefold() for x in languages] if isinstance(languages, list) else []
            languages.extend(t.split(':', 1)[1].casefold() for t in tags if t.startswith('language:'))
            language_document = None
            documented_set = set(languages)
            bilingual = bool(documented_set & {'multilingual','multi'}) or (bool(documented_set & {'ko','kor','korean'}) and bool(documented_set & {'en','eng','english'}))
            if not bilingual and license_name and license_name.casefold() in ALLOWED_LICENSES:
                card_bytes = card_fetcher(mid, revision)
                card_hash = hashlib.sha256(card_bytes).hexdigest()
                card_path = root / (card_hash + '.md')
                card_path.write_bytes(card_bytes)
                if hashlib.sha256(card_path.read_bytes()).hexdigest() != card_hash:
                    raise ValueError('MODEL_CARD_READBACK_FAILED')
                documented, lines = documented_languages(card_bytes.decode('utf-8'))
                languages.extend(documented)
                language_document = {'sha256': card_hash, 'artifact_ref': str(card_path), 'evidence_lines': lines}
            files = [str(x.rfilename) for x in (getattr(info, 'siblings', None) or [])]
            evidence = {'model_id': mid, 'revision': revision, 'official_info_url':
                        f'https://huggingface.co/api/models/{mid}/revision/{revision}',
                        'model_card_url': f'https://huggingface.co/{mid}/blob/{revision}/README.md',
                        'license_urls': [f'https://huggingface.co/{mid}/blob/{revision}/{name}'
                                         for name in files if 'license' in name.casefold()],
                        'tags': tags, 'card': card, 'language_document': language_document, 'files': files,
                        'pipeline_tag': getattr(info, 'pipeline_tag', None),
                        'library_name': getattr(info, 'library_name', None) or card.get('library_name')}
            data = json.dumps(evidence, sort_keys=True, ensure_ascii=False).encode()
            digest = hashlib.sha256(data).hexdigest()
            path = root / (digest + '.json')
            path.write_bytes(data)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('METADATA_READBACK_FAILED')
            result.update(license=license_name.casefold() if license_name else None,
                          languages=sorted(set(languages)), model_files=files,
                          pipeline_tag=evidence['pipeline_tag'], library_name=evidence['library_name'],
                          hydration_status='EXACT_REVISION_VERIFIED',
                          metadata_evidence={'sha256': digest, 'artifact_ref': str(path),
                                             'model_card_url': evidence['model_card_url'], 'language_document': language_document,
                                             'license_urls': evidence['license_urls']})
        except Exception as error:
            result['hydration_status'] = 'METADATA_FETCH_FAILED'
            result['hydration_error_type'] = type(error).__name__
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(hydrate, models))


def rejection_reasons(model):
    reasons = []
    if model.get('hydration_status') != 'EXACT_REVISION_VERIFIED':
        reasons.append(str(model.get('hydration_status') or 'METADATA_NOT_HYDRATED'))
    if model.get('pipeline_tag') != 'text-generation':
        reasons.append('TASK_NOT_TEXT_GENERATION')
    if not re.fullmatch('[0-9a-f]{40}', str(model.get('revision') or '')):
        reasons.append('IMMUTABLE_REVISION_MISSING')
    if model.get('library_name') != 'transformers':
        reasons.append('LIBRARY_NOT_TRANSFORMERS')
    license_name = str(model.get('license') or '').casefold()
    if not license_name:
        reasons.append('OFFICIAL_LICENSE_MISSING')
    elif license_name not in ALLOWED_LICENSES:
        reasons.append('LICENSE_NOT_IN_APPROVED_COMMERCIAL_ALLOWLIST')
    langs = set(model.get('languages') or [])
    multi = bool(langs & {'multilingual', 'multi'})
    if not multi and not langs & {'ko', 'kor', 'korean', '한국어'}:
        reasons.append('OFFICIAL_KOREAN_EVIDENCE_MISSING')
    if not multi and not langs & {'en', 'eng', 'english', '영어'}:
        reasons.append('OFFICIAL_ENGLISH_EVIDENCE_MISSING')
    if not any(name.endswith('.safetensors') for name in model.get('model_files') or []):
        reasons.append('PINNED_SAFETENSORS_MISSING')
    if not model.get('metadata_evidence', {}).get('license_urls'):
        reasons.append('PINNED_LICENSE_SNAPSHOT_FILE_MISSING')
    return reasons
