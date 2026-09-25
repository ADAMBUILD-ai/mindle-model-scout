from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

OUT = Path("aura-handoff-output")
WORK = Path("aura-handoff-work")
OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)

CANDIDATES = [
    {
        "key": "siglip",
        "model_id": "google/siglip-base-patch16-224",
        "revision": "7fd15f0689c79d79e38b1c2e2e2370a7bf2761ed",
        "role": "visual/reference fidelity QA",
        "license": "apache-2.0",
        "pages": ["P04", "P07", "P10", "P11"],
        "run_script": "run_siglip_similarity.py",
        "required_files": {"model.safetensors": (812672320, "2c63cb7d1f2e95ba501893cbb8faeb4ea9a3af295498d35097126228659c2af8")},
    },
    {
        "key": "ocr",
        "model_id": "PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx",
        "revision": "5c6f574b8e2230adf4287b33e736d71b9fabd28e",
        "role": "Korean OCR / visible label-number verification",
        "license": "apache-2.0",
        "pages": ["P02", "P03", "P07", "P10", "P11", "P12"],
        "run_script": "run_korean_ocr.py",
        "required_files": {"inference.onnx": (None, "92f0b7785e64fc9090106a241cf4c1eb97472824558272751b88a2a4476d3a08")},
    },
    {
        "key": "sam21",
        "model_id": "facebook/sam2.1-hiera-tiny",
        "revision": None,
        "role": "segmentation / protected-mask / region isolation",
        "license": "apache-2.0",
        "pages": ["P04", "P07", "P10", "P11"],
        "run_script": "run_sam21_mask.py",
    },
    {
        "key": "minilm",
        "model_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "revision": None,
        "role": "multilingual semantic/source-caption consistency",
        "license": "apache-2.0",
        "pages": ["P02", "P03", "P04", "P09", "P10", "P11", "P12"],
        "run_script": "run_minilm_similarity.py",
    },
]

ALLOW = [
    "*.safetensors",
    "*.onnx",
    "*.yml",
    "*.yaml",
    "*.json",
    "*.model",
    "*.txt",
    "README.md",
    "LICENSE",
    "LICENSE.*",
    "modules.json",
    "sentence_bert_config.json",
    "1_Pooling/*",
    "2_Dense/*",
]

APACHE_URL = "https://www.apache.org/licenses/LICENSE-2.0.txt"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def inventory(root: Path) -> list[dict]:
    rows = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rows.append({
                "path": p.relative_to(root).as_posix(),
                "size": p.stat().st_size,
                "sha256": sha256_file(p),
            })
    return rows


def selected_candidates() -> list[dict]:
    key = os.environ.get("AURA_HANDOFF_ONLY", "").strip().lower()
    if key and key not in {candidate["key"] for candidate in CANDIDATES}:
        raise ValueError(f"unknown AURA_HANDOFF_ONLY key: {key}")
    return [candidate for candidate in CANDIDATES if not key or candidate["key"] == key]


def verify_snapshot(model_dir: Path, candidate: dict) -> None:
    if not (model_dir / "README.md").is_file():
        raise RuntimeError("exact-revision model card missing")
    weights = list(model_dir.rglob("*.safetensors")) + list(model_dir.rglob("*.onnx"))
    if not weights:
        raise RuntimeError("actual model binary missing")
    for name, (expected_size, expected_sha) in candidate.get("required_files", {}).items():
        matches = list(model_dir.rglob(name))
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one {name}, got {len(matches)}")
        actual = matches[0]
        if expected_size is not None and actual.stat().st_size != expected_size:
            raise RuntimeError(f"size mismatch: {name}")
        if sha256_file(actual) != expected_sha:
            raise RuntimeError(f"SHA-256 mismatch: {name}")


def write_common_runtime_scripts(pkg: Path) -> None:
    scripts = pkg / "runtime"
    scripts.mkdir(exist_ok=True)

    (scripts / "run_siglip_similarity.py").write_text(r'''from pathlib import Path
import sys, torch
from PIL import Image
from transformers import AutoModel, AutoProcessor

MODEL = Path(sys.argv[1])
REF = Image.open(sys.argv[2]).convert("RGB")
CAND = Image.open(sys.argv[3]).convert("RGB")
processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
model = AutoModel.from_pretrained(MODEL, local_files_only=True)
model.eval()
with torch.no_grad():
    batch = processor(images=[REF, CAND], return_tensors="pt")
    feats = torch.nn.functional.normalize(model.get_image_features(**batch), dim=1)
score = float(feats[0] @ feats[1])
print({"reference_similarity": score})
''', encoding="utf-8")

    (scripts / "run_minilm_similarity.py").write_text(r'''from pathlib import Path
import sys, torch
from transformers import AutoModel, AutoTokenizer

MODEL = Path(sys.argv[1])
A = sys.argv[2]
B = sys.argv[3]
tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
model = AutoModel.from_pretrained(MODEL, local_files_only=True)
model.eval()
enc = tok([A, B], padding=True, truncation=True, return_tensors="pt")
with torch.no_grad():
    hidden = model(**enc).last_hidden_state
mask = enc["attention_mask"].unsqueeze(-1)
vec = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1)
vec = torch.nn.functional.normalize(vec, dim=1)
print({"semantic_similarity": float(vec[0] @ vec[1])})
''', encoding="utf-8")

    (scripts / "run_sam21_mask.py").write_text(r'''from pathlib import Path
import sys, torch
from PIL import Image
from transformers import Sam2Model, Sam2Processor

MODEL = Path(sys.argv[1])
IMAGE = Image.open(sys.argv[2]).convert("RGB")
X = float(sys.argv[3]); Y = float(sys.argv[4])
processor = Sam2Processor.from_pretrained(MODEL, local_files_only=True)
model = Sam2Model.from_pretrained(MODEL, local_files_only=True)
model.eval()
inputs = processor(images=IMAGE, input_points=[[[X, Y]]], input_labels=[[1]], return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)
masks = processor.post_process_masks(outputs.pred_masks.cpu(), inputs["original_sizes"])[0]
mask = masks[0, 0].numpy()
out = Image.fromarray((mask * 255).astype("uint8"))
target = Path(sys.argv[5])
out.save(target)
print({"mask": str(target), "size": out.size})
''', encoding="utf-8")

    (scripts / "run_korean_ocr.py").write_text(r'''from pathlib import Path
import sys
import numpy as np
import onnxruntime as ort
from PIL import Image

MODEL = Path(sys.argv[1])
IMAGE = Image.open(sys.argv[2]).convert("RGB")
onnx = next(MODEL.rglob("inference.onnx"))
yml = next(MODEL.rglob("inference.yml"))

def chars(path):
    out=[]; active=False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip()=="character_dict:":
            active=True; continue
        if active and line.startswith("  - "):
            v=line[4:]
            if v.startswith("'") and v.endswith("'"):
                v=v[1:-1].replace("''", "'")
            out.append(v)
        elif active and line and not line.startswith("  "):
            break
    return ["<blank>", *out, " "]

w=max(1,min(320,round(IMAGE.width*48/IMAGE.height)))
img=IMAGE.resize((w,48))
canvas=np.zeros((48,320,3),dtype=np.float32)
canvas[:,:w]=np.asarray(img,dtype=np.float32)[:,:,::-1]
tensor=((canvas/255.0)-0.5)/0.5
tensor=np.transpose(tensor,(2,0,1))[None,...]
sess=ort.InferenceSession(str(onnx),providers=["CPUExecutionProvider"])
pred=sess.run(None,{sess.get_inputs()[0].name:tensor})[0]
labels=chars(yml)
idx=pred.argmax(axis=-1)[0].tolist(); scores=pred.max(axis=-1)[0].tolist()
text=[]; conf=[]; prev=-1
for i,s in zip(idx,scores):
    if i!=prev and i!=0 and i<len(labels):
        text.append(labels[i]); conf.append(float(s))
    prev=i
print({"text":"".join(text).strip(),"confidence":sum(conf)/len(conf) if conf else 0.0})
''', encoding="utf-8")


def main() -> int:
    api = HfApi()
    index = {
        "schema_version": 1,
        "purpose": "AURA model handoff prior to product-specific benchmark",
        "generated_at_unix": time.time(),
        "packages": [],
        "failures": [],
    }

    selected = selected_candidates()
    index["expected_keys"] = [candidate["key"] for candidate in selected]
    for c in selected:
        key = c["key"]
        try:
            info = api.model_info(c["model_id"], revision=c["revision"] or "main")
            exact_revision = info.sha
            if c["revision"] and exact_revision != c["revision"]:
                raise RuntimeError("Hub revision did not match the pinned commit")
            tags = list(info.tags or [])
            detected_license = None
            for tag in tags:
                if tag.startswith("license:"):
                    detected_license = tag.split(":",1)[1]
                    break
            if detected_license != c["license"]:
                raise RuntimeError(f"license gate failed: expected {c['license']}, got {detected_license}")

            pkg = WORK / f"AURA_{key.upper()}_HANDOFF"
            if pkg.exists():
                shutil.rmtree(pkg)
            model_dir = pkg / "model"
            model_dir.mkdir(parents=True)

            snapshot_download(
                repo_id=c["model_id"],
                revision=exact_revision,
                local_dir=model_dir,
                allow_patterns=ALLOW,
            )
            verify_snapshot(model_dir, c)

            # canonical Apache 2.0 license snapshot
            import httpx
            lic = httpx.get(APACHE_URL, timeout=30.0)
            lic.raise_for_status()
            (pkg / "LICENSE_APACHE_2_0_CANONICAL.txt").write_bytes(lic.content)

            write_common_runtime_scripts(pkg)

            persistence = {
                "model_id": c["model_id"],
                "revision": exact_revision,
                "license": detected_license,
                "status": "CONFIRMED_FOR_PINNED_REVISION",
                "basis": "Apache License 2.0 grants perpetual and irrevocable copyright/patent permissions subject to license conditions; package preserves exact revision, model-card snapshot, canonical license text, and file hashes.",
                "future_source_policy_change": "does not retroactively alter the captured Apache-2.0 grant for these acquired bytes, subject to compliance and termination clauses",
            }
            (pkg / "LICENSE_PERSISTENCE.json").write_text(json.dumps(persistence, ensure_ascii=False, indent=2), encoding="utf-8")

            readme = f"""# AURA MODEL HANDOFF

Model: {c['model_id']}
Exact revision: {exact_revision}
Role: {c['role']}
Target pages: {', '.join(c['pages'])}
License: {detected_license}

## AURA use rule
This package is a delivered runtime input, not an automatic production approval.
AURA Work must run it only on COPIES of the frozen v61.1 baseline.

Required evidence per run:
1. exact baseline input SHA
2. runtime command/settings
3. output artifact + SHA
4. baseline/control comparison
5. geometry/text/source preservation result
6. KEEP_PRIMARY / SUPPORT_ONLY / REJECT_* decision

Runtime script:
runtime/{c['run_script']}
"""
            (pkg / "README_AURA_HANDOFF.md").write_text(readme, encoding="utf-8")

            files = inventory(pkg)
            manifest = {
                "model_id": c["model_id"],
                "revision": exact_revision,
                "role": c["role"],
                "target_pages": c["pages"],
                "license": detected_license,
                "license_persistence": "CONFIRMED_FOR_PINNED_REVISION",
                "runtime_script": f"runtime/{c['run_script']}",
                "files": files,
                "total_bytes": sum(x["size"] for x in files),
            }
            (pkg / "MODEL_HANDOFF_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            (pkg / "SHA256SUMS.txt").write_text("\n".join(f"{x['sha256']}  {x['path']}" for x in inventory(pkg))+"\n", encoding="utf-8")

            zip_path = OUT / f"AURA_{key.upper()}_HANDOFF_{exact_revision[:12]}.zip"
            if zip_path.exists():
                zip_path.unlink()
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as z:
                for p in sorted(pkg.rglob("*")):
                    if p.is_file():
                        z.write(p, p.relative_to(pkg).as_posix())

            package_sha = sha256_file(zip_path)
            item = {
                "key": key,
                "model_id": c["model_id"],
                "revision": exact_revision,
                "license": detected_license,
                "role": c["role"],
                "target_pages": c["pages"],
                "filename": zip_path.name,
                "package_size": zip_path.stat().st_size,
                "package_sha256": package_sha,
                "model_file_count": len([x for x in files if x["path"].startswith("model/")]),
                "status": "BINARY_PACKAGE_READY",
            }
            index["packages"].append(item)
            print(json.dumps(item, ensure_ascii=False), flush=True)
        except Exception as exc:
            fail = {"key": key, "model_id": c["model_id"], "status": "PACKAGE_FAILED", "error": repr(exc)}
            index["failures"].append(fail)
            print(json.dumps(fail, ensure_ascii=False), file=sys.stderr, flush=True)

    index["complete"] = len(index["packages"]) == len(selected) and not index["failures"]
    (OUT / "AURA_MODEL_HANDOFF_INDEX.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False, indent=2))
    return 0 if index["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
