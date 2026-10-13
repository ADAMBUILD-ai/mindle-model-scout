"""Acquire exactly one previously qualified pinned model. No search or inference."""
import concurrent.futures
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MODEL = 'Qwen/Qwen3-4B'
REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'
WEIGHTS = {
    'model-00001-of-00003.safetensors': (3957900840, '328a91d3122359d5547f9d79521205bc0a46e1f79a792dfe650e99fc2d651223'),
    'model-00002-of-00003.safetensors': (3987450520, '6cd087b316306a68c562436b5492edbcf6e16c6dba3a1308279caa5a58e21ca5'),
    'model-00003-of-00003.safetensors': (99630640, 'e4bf436957184f4eeb86a80e9db394503f1f56446b2e6b7edeac5b81470f4ca1'),
}
FILES = ['LICENSE', 'README.md', 'config.json', 'generation_config.json', 'merges.txt', 'model.safetensors.index.json', 'tokenizer.json', 'tokenizer_config.json', 'vocab.json', *WEIGHTS]
LICENSE_SHA = '832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def validate_metadata(metadata):
    if metadata.get('sha') != REVISION or metadata.get('pipeline_tag') != 'text-generation' or metadata.get('cardData', {}).get('license') != 'apache-2.0':
        raise ValueError('official immutable identity/task/license mismatch')
    mapping = {f['rfilename']: f for f in metadata['siblings']}
    if not all(name in mapping for name in FILES):
        raise ValueError('official loader manifest incomplete')
    for name, (size, digest) in WEIGHTS.items():
        lfs = mapping[name].get('lfs', {})
        if lfs.get('size') != size or lfs.get('sha256') != digest:
            raise ValueError('official pinned LFS differs from qualified historical candidate: ' + name)


def git_blob_sha(path):
    digest = hashlib.sha1()
    digest.update(f'blob {path.stat().st_size}\0'.encode())
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def matches_official(path, name, official):
    if not path.is_file():
        return False
    if name in WEIGHTS:
        return (path.stat().st_size, sha(path)) == WEIGHTS[name]
    lfs = official.get('lfs')
    if lfs:
        return (path.stat().st_size, sha(path)) == (lfs['size'], lfs['sha256'])
    return git_blob_sha(path) == official.get('blobId')


def fetch(root, name, official):
    target = root / name
    stage = target.with_suffix(target.suffix + '.acquiring')
    if not matches_official(target, name, official) and matches_official(stage, name, official):
        stage.replace(target)
        print(json.dumps({'file': name, 'status': 'REUSED_VERIFIED_STAGING'}), flush=True)
    existing_matches = matches_official(target, name, official)
    if existing_matches:
        print(json.dumps({'file': name, 'status': 'REUSED_EXISTING'}), flush=True)
    else:
        print(json.dumps({'file': name, 'status': 'FETCH_PINNED'}), flush=True)
        request = urllib.request.Request(f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}', headers={'User-Agent': 'mindle-aura136-pinned-acquisition/1.0'})
        with urllib.request.urlopen(request, timeout=120) as response, stage.open('wb') as stream:
            while chunk := response.read(4 * 1024 * 1024):
                stream.write(chunk)
        if not matches_official(stage, name, official):
            raise ValueError('official pinned file size/hash mismatch: ' + name)
        if stage.stat().st_size == 0:
            raise ValueError('empty pinned file: ' + name)
        stage.replace(target)
    return {'path': name, 'bytes': target.stat().st_size, 'sha256': sha(target), 'officialBlobId': official.get('blobId')}


def main():
    receipt = {'status': 'VERIFY_REQUIRED', 'modelId': MODEL, 'revision': REVISION, 'modelCalls': 0, 'broadSearchCalls': 0, 'paidServices': False, 'productPass': False, 'desktopInferenceReleased': False, 'startedAt': datetime.now(timezone.utc).isoformat()}
    try:
        durable = Path(os.environ['MODEL_SCOUT_STATE_DIR'])
        root = durable / 'aura136-pinned-models' / 'Qwen--Qwen3-4B' / REVISION
        root.mkdir(parents=True, exist_ok=True)
        receipt['modelRoot'] = str(root)
        free = shutil.disk_usage(root).free
        required = sum(size for name, (size, digest) in WEIGHTS.items() if not (root / name).is_file() or ((root / name).stat().st_size, sha(root / name)) != (size, digest)) + 2 * 1024 ** 3
        receipt['diskFreeBytesBefore'] = free
        if free < required:
            raise RuntimeError(f'BLOCKED_SAFE_DISK_BUDGET: required={required}, available={free}')
        with urllib.request.urlopen(f'https://huggingface.co/api/models/{MODEL}/revision/{REVISION}?blobs=true', timeout=30) as response:
            metadata = json.load(response)
        validate_metadata(metadata)
        official_files = {f['rfilename']: f for f in metadata['siblings']}
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            records = list(pool.map(lambda name: fetch(root, name, official_files[name]), FILES))
        license_record = next(r for r in records if r['path'] == 'LICENSE')
        if license_record['sha256'] != LICENSE_SHA:
            raise ValueError('pinned Apache license snapshot hash mismatch')
        config = json.loads((root / 'config.json').read_text(encoding='utf-8'))
        if not any('CausalLM' in name for name in config.get('architectures', [])) or config.get('max_position_embeddings', 0) < 32768:
            raise ValueError('causal architecture or configured context is unsuitable')
        receipt.update({'status': 'ACQUIRED_PINNED_FULL_FILES_VERIFIED_NOT_PRODUCT_PASS', 'files': records, 'license': 'apache-2.0', 'licenseSnapshotSha256': license_record['sha256'], 'configuredContextTokens': config['max_position_embeddings'], 'usableContextMeasured': False, 'totalBytes': sum(r['bytes'] for r in records), 'runtime': {'os': platform.platform(), 'pythonExe': sys.executable, 'pythonVersion': sys.version, 'packages': {name: importlib.metadata.version(name) for name in ('torch', 'transformers')}}, 'nextAction': 'Desktop owner resource review and actual architecture/source-bound benchmark; do not mark TESTED_PASS or DELIVERED'})
        unexpected = sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and str(p.relative_to(root)) not in FILES)
        if unexpected:
            raise ValueError('unlisted files in immutable loader root: ' + repr(unexpected))
        manifest_path = root.parent / ('AURA136_MODEL_MANIFEST_' + REVISION + '.json')
        receipt['manifestPath'] = str(manifest_path)
        manifest_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from src.model_scout.acquisition import ModelRegistry
        registry = ModelRegistry(durable / 'model-registry.json')
        record = {'model_id': MODEL, 'revision': REVISION, 'source_url': f'https://huggingface.co/{MODEL}/tree/{REVISION}', 'license': 'apache-2.0',
                  'files': [{'path': f['path'], 'size': f['bytes'], 'sha256': f['sha256']} for f in records],
                  'cache_location': str(root), 'acquisition_runner': 'aura136-pinned-official-v1',
                  'acquisition_status': 'ACQUIRED_VERIFIED', 'validation_status': 'PENDING', 'acquired_at': time.time(),
                  'originating_requests': ['ADAMBUILD-ai/mindle-model-scout#136'], 'consuming_teams': ['AURA'], 'trust_remote_code_required': False}
        persisted, created = registry.upsert(record)
        receipt['registryCreated'] = created
        receipt['registryPath'] = str(registry.path)
        receipt['registryCurrentRootMatches'] = persisted.get('cache_location') == str(root)
    except Exception as exc:
        receipt.update({'status': 'BLOCKED_PINNED_ACQUISITION', 'errorType': type(exc).__name__, 'exactError': str(exc)})
    receipt['finishedAt'] = datetime.now(timezone.utc).isoformat()
    Path('aura136-pinned-acquisition-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: receipt.get(key) for key in ('status', 'modelId', 'revision', 'totalBytes', 'exactError', 'modelCalls')}), flush=True)
    return 0 if receipt['status'] == 'ACQUIRED_PINNED_FULL_FILES_VERIFIED_NOT_PRODUCT_PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
