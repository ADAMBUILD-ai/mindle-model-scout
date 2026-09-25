from __future__ import annotations
import hashlib,json,os,shutil,time,zipfile
from pathlib import Path
from urllib.request import urlopen
from huggingface_hub import HfApi,snapshot_download
from build_aura_handoff_packages import write_common_runtime_scripts

KEY=os.environ["AURA_HANDOFF_ONLY"]
CFG={
"ocr":("PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx","5c6f574b8e2230adf4287b33e736d71b9fabd28e","korean_ocr",["P02","P03","P07","P10","P11","P12"],["inference.onnx","inference.yml","README.md","LICENSE*"]),
"sam21":("facebook/sam2.1-hiera-tiny",None,"segmentation_protected_mask",["P04","P07","P10","P11"],["model.safetensors","*.json","README.md","LICENSE*"]),
"minilm":("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",None,"semantic_source_caption_consistency",["P02","P03","P04","P09","P10","P11","P12"],["model.safetensors","*.json","*.model","vocab.txt","README.md","LICENSE*","1_Pooling/*"]),
"siglip":("google/siglip-base-patch16-224","7fd15f0689c79d79e38b1c2e2e2370a7bf2761ed","visual_reference_fidelity",["P04","P07","P10","P11"],["model.safetensors","*.json","*.model","*.txt","README.md","LICENSE*"]),
}
mid,pin,role,pages,allow=CFG[KEY]
api=HfApi(); info=api.model_info(mid,revision=pin or "main"); rev=info.sha
if pin and rev!=pin: raise SystemExit("pinned revision mismatch")
lic=next((t.split(":",1)[1] for t in (info.tags or []) if t.startswith("license:")),None)
if lic!="apache-2.0": raise SystemExit(f"license gate failed: {lic}")
out=Path("aura-handoff-slim"); shutil.rmtree(out,ignore_errors=True); (out/"model").mkdir(parents=True)
snapshot_download(repo_id=mid,revision=rev,local_dir=out/"model",allow_patterns=allow)
if not (out/"model"/"README.md").is_file(): raise SystemExit("model card missing from pinned snapshot")
expected={
 "ocr":("inference.onnx",None,"92f0b7785e64fc9090106a241cf4c1eb97472824558272751b88a2a4476d3a08"),
 "siglip":("model.safetensors",812672320,"2c63cb7d1f2e95ba501893cbb8faeb4ea9a3af295498d35097126228659c2af8"),
}
weights=list((out/"model").rglob("*.safetensors"))+list((out/"model").rglob("*.onnx"))
if not weights: raise SystemExit("actual model binary missing")
(out/"LICENSE_PERSISTENCE.json").write_text(json.dumps({
 "model_id":mid,"revision":rev,"license":lic,"status":"CONFIRMED_FOR_PINNED_REVISION",
 "basis":"Apache-2.0 metadata captured at exact revision; acquired exact bytes and hashes are frozen for AURA handoff."
},indent=2),encoding="utf-8")
(out/"README_AURA_HANDOFF.md").write_text(
 f"# AURA MODEL HANDOFF\nModel: {mid}\nRevision: {rev}\nRole: {role}\nPages: {pages}\n"
 "Use only on a COPY of frozen Baseline v61.1. Record input SHA, command/settings, output SHA, A/B comparison, preservation metrics, and final model decision.\n",
 encoding="utf-8")
def sh(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
if KEY in expected:
 name,size,digest=expected[KEY]
 matches=list((out/"model").rglob(name))
 if len(matches)!=1: raise SystemExit(f"expected one {name}, got {len(matches)}")
 if size is not None and matches[0].stat().st_size!=size: raise SystemExit(f"binary size mismatch: {name}")
 if sh(matches[0])!=digest: raise SystemExit(f"binary SHA-256 mismatch: {name}")
with urlopen("https://www.apache.org/licenses/LICENSE-2.0.txt",timeout=30) as response:
 (out/"LICENSE_APACHE_2_0_CANONICAL.txt").write_bytes(response.read())
write_common_runtime_scripts(out)
(out/"runtime"/"requirements.txt").write_text(
 "torch==2.5.1\ntransformers==4.51.3\npillow==11.2.1\nnumpy==2.2.4\nonnxruntime==1.21.0\n",
 encoding="utf-8")
command={"ocr":"run_korean_ocr.py","sam21":"run_sam21_mask.py","minilm":"run_minilm_similarity.py","siglip":"run_siglip_similarity.py"}[KEY]
(out/"README_AURA_HANDOFF.md").write_text(
 (out/"README_AURA_HANDOFF.md").read_text(encoding="utf-8")
 + f"\nRuntime: python runtime/{command} model/ <product-specific inputs>\n"
 + "Runtime results are pending; do not treat this package as AURA TESTED_PASS.\n",
 encoding="utf-8")
files=[]
for p in sorted(out.rglob("*")):
 if p.is_file(): files.append({"path":p.relative_to(out).as_posix(),"bytes":p.stat().st_size,"sha256":sh(p)})
manifest={"model_id":mid,"revision":rev,"license":lic,"role":role,"pages":pages,"files":files,"total_bytes":sum(x["bytes"] for x in files)}
(out/"MODEL_HANDOFF_MANIFEST.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
files=[]
for p in sorted(out.rglob("*")):
 if p.is_file(): files.append({"path":p.relative_to(out).as_posix(),"bytes":p.stat().st_size,"sha256":sh(p)})
(out/"SHA256SUMS.txt").write_text("\n".join(f"{x['sha256']}  {x['path']}" for x in files)+"\n",encoding="utf-8")
z=Path(f"AURA_{KEY.upper()}_HANDOFF_{rev[:12]}.zip")
with zipfile.ZipFile(z,"w",compression=zipfile.ZIP_STORED,allowZip64=True) as a:
 for p in sorted(out.rglob("*")):
  if p.is_file(): a.write(p,p.relative_to(out).as_posix())
idx={"key":KEY,"model_id":mid,"revision":rev,"license":lic,"role":role,"pages":pages,"package":z.name,"package_bytes":z.stat().st_size,"package_sha256":sh(z),"status":"BINARY_PACKAGE_READY","created_at":time.time()}
Path("AURA_MODEL_HANDOFF_INDEX.json").write_text(json.dumps(idx,indent=2),encoding="utf-8")
print(json.dumps(idx))
