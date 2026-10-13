"""Read existing pinned AURA assets on the real runner; never acquire or infer."""
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

PINS = {
    'Qwen/Qwen3-0.6B': 'c1899de289a04d12100db370d81485cdf75e47ca',
    'Qwen/Qwen3-1.7B': '70d244cc86ccca08cf5af4e1e306ecf908b1ad5e',
    'Qwen/Qwen2.5-1.5B-Instruct': '989aa7980e4cf806f80c7fef2b1adb7bc71aa306',
}


def inspect(state_root, hub_roots):
    historical = json.loads((Path(__file__).resolve().parents[1] / 'config/aura136-historical-asset-manifests.json').read_text(encoding='utf-8'))
    expected = {m['modelId']: m for m in historical}
    registry_path = Path(state_root) / 'model-registry.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8-sig')) if registry_path.is_file() else {'models': []}
    rows = []
    for model_id, revision in PINS.items():
        roots = [Path(root) / ('models--' + model_id.replace('/', '--')) / 'snapshots' / revision for root in hub_roots]
        matches = [r for r in registry.get('models', []) if r.get('model_id') == model_id and r.get('revision') == revision]
        roots += [Path(r['cache_location']) for r in matches if r.get('cache_location')]
        roots = list(dict.fromkeys(str(p) for p in roots))
        found = []
        for value in roots:
            root = Path(value)
            if not root.is_dir():
                continue
            files = []
            for p in sorted(root.rglob('*')):
                if not p.is_file():
                    continue
                digest = hashlib.sha256()
                with p.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(chunk)
                files.append({'path': str(p.relative_to(root)), 'bytes': p.stat().st_size, 'sha256': digest.hexdigest()})
            # Observation is not official hash matching or architectural acceptance.
            actual = {f['path'].replace('\\', '/'): f for f in files}
            wanted = {f['path']: f for f in expected[model_id]['files']}
            missing = sorted(set(wanted) - set(actual))
            mismatched = sorted(name for name in set(wanted) & set(actual) if actual[name]['bytes'] != wanted[name]['bytes'] or actual[name]['sha256'] != wanted[name]['sha256'])
            unexpected = sorted(set(actual) - set(wanted))
            found.append({'root': value, 'files': files, 'missing': missing, 'mismatched': mismatched, 'unexpected': unexpected,
                          'status': 'FILES_MATCH_HISTORICAL_MANIFEST_NOT_PRODUCT_PASS' if not missing and not mismatched and not unexpected else 'BLOCKED_INCOMPLETE_OR_MISMATCH'})
        rows.append({'modelId': model_id, 'revision': revision, 'status': 'EXISTING_BYTES_OBSERVED' if found else 'NOT_FOUND_IN_BOUNDED_RUNNER_SCOPE', 'searchedRoots': roots, 'snapshots': found, 'registryMatches': len(matches)})
    return {'observedAt': datetime.now(timezone.utc).isoformat(), 'models': rows,
            'modelCalls': 0, 'downloads': 0, 'productPass': False,
            'scope': 'exact pinned Hub snapshots and matching canonical registry cache locations; not all host disks/NAS',
            'runtime': {'os': platform.platform(), 'pythonVersion': sys.version, 'pythonExe': sys.executable,
                        'packages': {name: package_version(name) for name in ('torch', 'transformers')}}}


def package_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return 'NOT_INSTALLED'


def sanitize(value):
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, str):
        for home in filter(None, (os.environ.get('USERPROFILE'), os.environ.get('HOME'))):
            value = value.replace(home, '%OWNER_HOME%')
        return value
    return value


def main():
    state = os.environ['MODEL_SCOUT_STATE_DIR']
    hub = Path(os.environ.get('HF_HOME', str(Path.home() / '.cache' / 'huggingface'))) / 'hub'
    roots = [hub, Path(state) / 'hf-cache' / 'hub', Path(state) / 'cache']
    report = sanitize(inspect(state, roots))
    Path('aura136-runner-asset-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'ASSET_AUDIT_COMPLETED_NOT_PRODUCT_PASS', 'models': [{k: r[k] for k in ('modelId', 'revision', 'status')} for r in report['models']], 'modelCalls': 0}))


if __name__ == '__main__':
    main()
