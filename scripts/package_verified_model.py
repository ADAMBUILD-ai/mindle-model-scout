"""Package a previously verified Hub snapshot for independent GitHub download.

This tool never fetches or executes model code. It rechecks the durable registry
against the runner's pinned bytes, then verifies the downloaded ZIP independently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


LICENSES = {"mit", "apache-2.0"}
ALLOWED_SUFFIXES = {".json", ".md", ".txt", ".safetensors", ".model", ".onnx", ".vocab", ".merges"}
ALLOWED_FILENAMES = {".gitattributes"}
WEIGHT_SUFFIXES = {".safetensors", ".onnx"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot_root(path: Path, model_id: str, revision: str) -> Path:
    expected_dir = "models--" + model_id.replace("/", "--")
    parts = path.parts
    matches = [i for i in range(len(parts) - 2) if parts[i].casefold() == expected_dir.casefold()
               and parts[i + 1].casefold() == "snapshots" and parts[i + 2] == revision]
    if len(matches) != 1:
        raise ValueError(f"recorded file is not within pinned Hub snapshot: {path}")
    return Path(*parts[:matches[0] + 3])


def build(registry_path: Path, model_id: str, output_dir: Path) -> dict:
    registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    rows = [row for row in registry["models"] if row.get("model_id") == model_id]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one registry row for {model_id}")
    row = rows[0]
    revision = str(row.get("revision") or "")
    license_id = str(row.get("license") or "").lower()
    if row.get("acquisition_status") != "ACQUIRED_VERIFIED":
        raise ValueError("model acquisition is not verified")
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("model revision is not an immutable Hub commit")
    if license_id not in LICENSES or row.get("trust_remote_code_required") is not False:
        raise ValueError("license or remote-code safety gate failed")
    if row.get("source_url") != f"https://huggingface.co/{model_id}":
        raise ValueError("source must be the official model repository")
    recorded = row.get("files") or []
    if not recorded:
        raise ValueError("registry contains no downloaded file evidence")
    roots = {_snapshot_root(Path(item["path"]), model_id, revision) for item in recorded}
    if len(roots) != 1:
        raise ValueError("model evidence spans multiple snapshots")
    root = roots.pop()
    if not root.is_dir():
        raise FileNotFoundError(root)
    for item in recorded:
        path = Path(item["path"])
        if not path.is_file() or path.stat().st_size != item["size"] or sha256(path) != item["sha256"]:
            raise ValueError(f"registered file does not match durable bytes: {path}")
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files or not any(path.suffix.lower() in WEIGHT_SUFFIXES for path in files):
        raise ValueError("pinned snapshot has no safe model weights")
    if not any(path.name == "README.md" for path in files):
        raise ValueError("exact-revision license/model card is absent")
    details = []
    for path in files:
        relative = path.relative_to(root)
        if path.suffix.lower() not in ALLOWED_SUFFIXES and path.name not in ALLOWED_FILENAMES:
            raise ValueError(f"unreviewed executable or unsafe snapshot file: {relative}")
        if path.is_symlink():
            actual = path.resolve()
            hub_root = root.parent.parent
            if not (actual.is_relative_to(root) or actual.is_relative_to(hub_root / "blobs")):
                raise ValueError(f"snapshot symlink escapes its own model repository: {relative}")
        details.append({"path": f"snapshot/{relative.as_posix()}", "size": path.stat().st_size, "sha256": sha256(path)})
    manifest = {
        "model_id": model_id,
        "revision": revision,
        "source_url": row["source_url"],
        "license": license_id,
        "license_evidence": "snapshot/README.md (exact-revision copy); see license metadata and terms before product release",
        "acquisition_status": "ACQUIRED_VERIFIED",
        "product_validation_status": row.get("validation_status", "PENDING"),
        "trust_remote_code": False,
        "files": details,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / (model_id.replace("/", "--") + "-" + revision[:12] + ".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as output:
        for path in files:
            output.write(path, f"snapshot/{path.relative_to(root).as_posix()}")
        output.writestr("MODEL_HANDOFF_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    receipt = {"model_id": model_id, "revision": revision, "package": archive.name,
               "package_size": archive.stat().st_size, "package_sha256": sha256(archive),
               "file_count": len(details), "status": "PACKAGED_UNVERIFIED_DOWNLOAD"}
    (output_dir / "PACKAGE_BUILD_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def verify(archive: Path, *, expected_sha256: str | None = None) -> dict:
    digest = sha256(archive)
    if expected_sha256 and digest != expected_sha256:
        raise ValueError("downloaded ZIP SHA-256 differs from uploaded original")
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read("MODEL_HANDOFF_MANIFEST.json"))
        entries = manifest["files"]
        if {entry["path"] for entry in entries} != set(z.namelist()) - {"MODEL_HANDOFF_MANIFEST.json"}:
            raise ValueError("ZIP file list differs from manifest")
        for entry in entries:
            name = entry["path"]
            if not name.startswith("snapshot/") or ".." in Path(name).parts:
                raise ValueError("unsafe ZIP entry")
            checksum = hashlib.sha256()
            size = 0
            with z.open(name) as source:
                for block in iter(lambda: source.read(4 * 1024 * 1024), b""):
                    size += len(block)
                    checksum.update(block)
            if size != entry["size"] or checksum.hexdigest() != entry["sha256"]:
                raise ValueError(f"downloaded file bytes do not match manifest: {name}")
    return {"model_id": manifest["model_id"], "revision": manifest["revision"],
            "package": archive.name, "package_size": archive.stat().st_size,
            "package_sha256": digest, "file_count": len(entries), "status": "INDEPENDENT_DOWNLOAD_VERIFIED",
            "product_validation_status": manifest["product_validation_status"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "verify"))
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--model-id")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args()
    if args.mode == "build":
        if not args.registry or not args.model_id or not args.output_dir:
            parser.error("build requires --registry, --model-id and --output-dir")
        result = build(args.registry, args.model_id, args.output_dir)
    else:
        if not args.archive or not args.expected_sha256:
            parser.error("verify requires --archive and --expected-sha256")
        result = verify(args.archive, expected_sha256=args.expected_sha256)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
