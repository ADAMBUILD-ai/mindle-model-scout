"""Verify existing assets only. No network, downloads, installation or inference."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def verify(manifest, root):
    root = Path(root).resolve()
    files = []
    for record in manifest['files']:
        relative = Path(record['path'])
        candidate = root / relative
        path = candidate.resolve()
        if relative.is_absolute() or not path.is_relative_to(root):
            raise ValueError('manifest path escapes model root')
        if candidate.is_symlink():
            raise ValueError('manifest file must not be a symlink')
        if not path.is_file():
            files.append({'path': str(relative), 'status': 'MISSING'})
            continue
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        actual = {'path': str(relative), 'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}
        actual['status'] = 'MATCH' if actual['bytes'] == record['bytes'] and actual['sha256'] == record['sha256'] else 'MISMATCH'
        files.append(actual)
    expected = {str(Path(row['path'])) for row in manifest['files']}
    unlisted = sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and str(p.relative_to(root)) not in expected) if root.is_dir() else []
    return {'modelId': manifest['modelId'], 'revision': manifest.get('revision'),
            'status': 'FILES_VERIFIED_NOT_PRODUCT_PASS' if files and all(row['status'] == 'MATCH' for row in files) and not unlisted else 'BLOCKED_ASSET_INCOMPLETE_OR_MISMATCH',
            'files': files, 'unlistedFiles': unlisted, 'modelCalls': 0, 'productPass': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--model-root', required=True)
    parser.add_argument('--python-exe')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = verify(json.loads(Path(args.manifest).read_text(encoding='utf-8')), args.model_root)
    result['runtime'] = {'status': 'NOT_INSPECTED'}
    if args.python_exe:
        probe = "import sys,platform,json,importlib.metadata as m; print(json.dumps({'python':sys.version,'os':platform.platform(),'packages':{p:m.version(p) for p in ['torch','transformers']}}))"
        try:
            run = subprocess.run([str(Path(args.python_exe).resolve()), '-I', '-c', probe], capture_output=True, text=True, timeout=30)
            result['runtime'] = {'exitCode': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr, 'modelCalls': 0}
        except (OSError, subprocess.TimeoutExpired) as exc:
            result['runtime'] = {'status': 'BLOCKED_RUNTIME_UNAVAILABLE', 'error': str(exc)}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if result['status'] == 'FILES_VERIFIED_NOT_PRODUCT_PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
