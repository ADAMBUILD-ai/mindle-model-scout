from __future__ import annotations

import argparse, json
from pathlib import Path
from src.model_scout.acquisition import AcquisitionRunner, AcquisitionSpec, ModelRegistry

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("specs"); p.add_argument("--state-dir",required=True); p.add_argument("--concurrency",type=int,default=3); p.add_argument("--output",default="acquisition-evidence.json"); a=p.parse_args()
    payload=json.loads(Path(a.specs).read_text(encoding="utf-8")); specs=[AcquisitionSpec.from_mapping(x) for x in payload]
    state=Path(a.state_dir); registry=ModelRegistry(state/"model-registry.json"); runner=AcquisitionRunner(cache_root=state/"cache",registry=registry)
    results=runner.acquire_many(specs,concurrency=a.concurrency)
    out={"concurrency":a.concurrency,"results":results,"registry":registry.snapshot()}; Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out,sort_keys=True)); return 0 if all(x["status"] in {"ACQUIRED_VERIFIED","DUPLICATE_SUPPRESSED"} for x in results) else 1
if __name__=="__main__": raise SystemExit(main())
