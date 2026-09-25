from __future__ import annotations
import hashlib,json,os,shutil,time,zipfile
from pathlib import Path
from urllib.request import urlopen
from huggingface_hub import HfApi,snapshot_download
from build_aura_handoff_packages import write_common_runtime_scripts

KEY=os.environ["AURA_HANDOFF_ONLY"]
CFG={
"ocr":("PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx","5c6f574b8e2230adf4287b33e736d71b9fabd28e","korean_ocr",["P02","P03","P07","P10","P11","P12"],["inference.onnx","inference.yml","README.md","LICENSE*"],"apache-2.0"),
"sam21":("facebook/sam2.1-hiera-tiny","de431c4043854a71d8101e17995dfe596bf101a5","segmentation_protected_mask",["P04","P07","P10","P11"],["model.safetensors","*.json","*.yaml","*.yml","README.md","LICENSE*"],"apache-2.0"),
"minilm":("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",None,"semantic_source_caption_consistency",["P02","P03","P04","P09","P10","P11","P12"],["model.safetensors","*.json","*.model","vocab.txt","README.md","LICENSE*","1_Pooling/*"],"apache-2.0"),
"siglip":("google/siglip-base-patch16-224","7fd15f0689c79d79e38b1c2e2e2370a7bf2761ed","visual_reference_fidelity",["P04","P07","P10","P11"],["model.safetensors","*.json","*.model","*.txt","README.md","LICENSE*"],"apache-2.0"),
"florence":("microsoft/Florence-2-base-ft","f6c1a25888ffc1d945ee8a1a77ac833c7303d46e","visual_source_understanding",["P03","P04","P07","P10","P11"],["*.safetensors","*.json","*.py","*.txt","*.model","README.md","LICENSE*"],"mit"),
}
mid,pin,role,pages,allow,expected_license=CFG[KEY]
api=HfApi(); info=api.model_info(mid,revision=pin or "main"); rev=info.sha
if pin and rev!=pin: raise SystemExit("pinned revision mismatch")
lic=next((t.split(":",1)[1] for t in (info.tags or []) if t.startswith("license:")),None)
if lic!=expected_license: raise SystemExit(f"license gate failed: expected {expected_license}, got {lic}")
out=Path("aura-handoff-slim"); shutil.rmtree(out,ignore_errors=True); (out/"model").mkdir(parents=True)
snapshot_download(repo_id=mid,revision=rev,local_dir=out/"model",allow_patterns=allow)
if not (out/"model"/"README.md").is_file(): raise SystemExit("pinned model card missing")
if not list((out/"model").rglob("*.safetensors")) and not list((out/"model").rglob("*.onnx")):
 raise SystemExit("model binary missing")
(out/"LICENSE_PERSISTENCE.json").write_text(json.dumps({
 "model_id":mid,
 "revision":rev,
 "license":lic,
 "status":"LOCKED_PRIOR_AURA_COMPLIANCE_BASELINE" if KEY=="florence" else "CONFIRMED_FOR_PINNED_REVISION",
 "basis":"Florence uses the existing AURA MIT compliance baseline; do not reopen its license gate in this packaging step." if KEY=="florence" else "Apache-2.0 metadata captured at exact revision; acquired exact bytes and hashes are frozen for AURA handoff."
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
known={
 "ocr":("inference.onnx",None,"92f0b7785e64fc9090106a241cf4c1eb97472824558272751b88a2a4476d3a08"),
 "siglip":("model.safetensors",812672320,"2c63cb7d1f2e95ba501893cbb8faeb4ea9a3af295498d35097126228659c2af8"),
}
if KEY in known:
 name,size,digest=known[KEY]
 found=list((out/"model").rglob(name))
 if len(found)!=1: raise SystemExit(f"expected exactly one {name}")
 if size is not None and found[0].stat().st_size!=size: raise SystemExit(f"binary size mismatch: {name}")
 if sh(found[0])!=digest: raise SystemExit(f"binary SHA-256 mismatch: {name}")
if lic=="apache-2.0":
 with urlopen("https://www.apache.org/licenses/LICENSE-2.0.txt",timeout=30) as response:
  (out/"LICENSE_APACHE_2_0_CANONICAL.txt").write_bytes(response.read())
elif not list((out/"model").rglob("LICENSE*")):
 raise SystemExit("license snapshot missing")
if KEY!="florence":
 write_common_runtime_scripts(out)
 (out/"runtime"/"requirements.txt").write_text(
  "torch==2.5.1\ntransformers==4.51.3\npillow==11.2.1\nnumpy==2.2.4\nonnxruntime==1.21.0\n",encoding="utf-8")
 script={"ocr":"run_korean_ocr.py","sam21":"run_sam21_mask.py","minilm":"run_minilm_similarity.py","siglip":"run_siglip_similarity.py"}[KEY]
 (out/"README_AURA_HANDOFF.md").write_text(
  (out/"README_AURA_HANDOFF.md").read_text(encoding="utf-8")
  +f"\nRuntime: python runtime/{script} model/ <product-specific inputs>\n"
  +"Product-specific CPU TESTED_PASS is pending.\n",encoding="utf-8")
else:
 (out/"README_AURA_HANDOFF.md").write_text(
  (out/"README_AURA_HANDOFF.md").read_text(encoding="utf-8")
  +"\nRuntime adapter unavailable: do not execute model repository Python code.\n",encoding="utf-8")
files=[]
for p in sorted(out.rglob("*")):
 if p.is_file() and ".cache" not in p.parts: files.append({"path":p.relative_to(out).as_posix(),"bytes":p.stat().st_size,"sha256":sh(p)})
manifest={"model_id":mid,"revision":rev,"license":lic,"role":role,"pages":pages,"files":files,"total_bytes":sum(x["bytes"] for x in files)}
(out/"MODEL_HANDOFF_MANIFEST.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
files=[]
for p in sorted(out.rglob("*")):
 if p.is_file() and ".cache" not in p.parts: files.append({"path":p.relative_to(out).as_posix(),"bytes":p.stat().st_size,"sha256":sh(p)})
(out/"SHA256SUMS.txt").write_text("\n".join(f"{x['sha256']}  {x['path']}" for x in files)+"\n",encoding="utf-8")
z=Path(f"AURA_{KEY.upper()}_HANDOFF_{rev[:12]}.zip")
with zipfile.ZipFile(z,"w",compression=zipfile.ZIP_STORED,allowZip64=True) as a:
 for p in sorted(out.rglob("*")):
  if p.is_file() and ".cache" not in p.parts: a.write(p,p.relative_to(out).as_posix())
idx={"key":KEY,"model_id":mid,"revision":rev,"license":lic,"role":role,"pages":pages,"package":z.name,"package_bytes":z.stat().st_size,"package_sha256":sh(z),"status":"BINARY_PACKAGE_READY","created_at":time.time()}
Path("AURA_MODEL_HANDOFF_INDEX.json").write_text(json.dumps(idx,indent=2),encoding="utf-8")
print(json.dumps(idx))
