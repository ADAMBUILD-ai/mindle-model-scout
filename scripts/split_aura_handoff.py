from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: split_aura_handoff.py <model-key>")
    key = sys.argv[1]
    packages = sorted(Path(".").glob("AURA_*_HANDOFF_*.zip"))
    if len(packages) != 1:
        raise SystemExit(f"expected exactly one package, found {len(packages)}: {packages}")
    pkg = packages[0]
    out = Path("aura-chunks")
    out.mkdir(exist_ok=True)
    chunk_size = 180 * 1024 * 1024
    parts = []
    with pkg.open("rb") as f:
        index = 0
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            name = f"{key}.part-{index:02d}"
            path = out / name
            path.write_bytes(data)
            parts.append({
                "name": name,
                "bytes": len(data),
                "sha256": sha256_bytes(data),
            })
            index += 1
    manifest = {
        "key": key,
        "package": pkg.name,
        "package_bytes": pkg.stat().st_size,
        "package_sha256": sha256_file(pkg),
        "chunk_size": chunk_size,
        "parts": parts,
    }
    (out / f"{key}.reassembly.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    index_src = Path("AURA_MODEL_HANDOFF_INDEX.json")
    if index_src.is_file():
        (out / f"{key}.index.json").write_bytes(index_src.read_bytes())
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
