import hashlib,json,sys,urllib.parse,urllib.request
from pathlib import Path
OUT=Path("sam21-mission-evidence.json"); OK={"apache-2.0","mit","bsd-3-clause","bsd-2-clause"}
def get(url):
    with urllib.request.urlopen(url,timeout=60) as r:return json.load(r)
def main():
    e={"status":"BLOCKED"}
    try:
        for m in get("https://huggingface.co/api/models?search=sam2%20onnx&limit=20&full=true"):
            repo=m.get("modelId") or m.get("id"); lic=next((x[8:] for x in m.get("tags",[]) if x.startswith("license:")),None)
            if lic not in OK: continue
            meta=get("https://huggingface.co/api/models/"+urllib.parse.quote(repo,safe="/")); sha=meta.get("sha"); files=[x for x in meta.get("siblings",[]) if x.get("rfilename","").endswith((".onnx",".safetensors"))]
            if not files: continue
            f=min(files,key=lambda x:x.get("size",10**18)); name=f["rfilename"]; dest=Path("weight"+Path(name).suffix); h=hashlib.sha256(); size=0
            with urllib.request.urlopen(f"https://huggingface.co/{repo}/resolve/{sha}/{urllib.parse.quote(name)}",timeout=120) as r, dest.open("wb") as w:
                while chunk:=r.read(1048576):h.update(chunk);w.write(chunk);size+=len(chunk)
            e={"status":"DOWNLOADED","repo_id":repo,"revision":sha,"license":lic,"source_url":f"https://huggingface.co/{repo}","weight_filename":name,"file_format":dest.suffix,"file_size":size,"sha256":h.hexdigest(),"safe_loader":"ONNX_OR_SAFETENSORS_NO_REMOTE_CODE_EXECUTED"};break
    except Exception as x:e["error_type"]=type(x).__name__
    OUT.write_text(json.dumps(e,indent=2)+"\n");print(json.dumps(e));sys.exit(e["status"]!="DOWNLOADED")
if __name__=="__main__":main()
