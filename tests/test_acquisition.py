import json, threading, time
from pathlib import Path
import pytest
from src.model_scout.acquisition import AcquisitionRejected, AcquisitionRunner, AcquisitionSpec, ModelRegistry

def spec(name="org/model", **overrides):
    data={"model_id":name,"revision":"abcdef123456","source_url":"https://huggingface.co/"+name,"license":"apache-2.0","files":("model.safetensors",)}; data.update(overrides); return AcquisitionSpec(**data)

def test_fail_closed_policy(tmp_path):
    with pytest.raises(AcquisitionRejected): spec(license="unknown").validate()
    with pytest.raises(AcquisitionRejected): spec(trust_remote_code_required=True).validate()
    with pytest.raises(AcquisitionRejected): spec(revision="main").validate()

def test_registry_atomic_duplicate_suppression(tmp_path):
    r=ModelRegistry(tmp_path/"registry.json"); row={"model_id":"a/b","revision":"1234567","acquisition_status":"ACQUIRED_VERIFIED"}
    assert r.upsert(row)[1] is True; assert r.upsert(row)[1] is False; assert len(r.snapshot()["models"])==1

def test_parallel_acquisition_isolated_and_overlapping(tmp_path, monkeypatch):
    active=0; peak=0; lock=threading.Lock()
    class Response:
        def __init__(self,data): self.data=data
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def read(self,n):
            nonlocal active,peak
            if self.data:
                with lock: active+=1; peak=max(peak,active)
                time.sleep(.04); value=self.data; self.data=b""
                with lock: active-=1
                return value
            return b""
    monkeypatch.setattr("urllib.request.urlopen",lambda *a,**k: Response(b"safe model bytes"))
    r=AcquisitionRunner(cache_root=tmp_path/"cache",registry=ModelRegistry(tmp_path/"registry.json"))
    result=r.acquire_many([spec(f"org/model-{i}") for i in range(3)],concurrency=3)
    assert peak>=2; assert {x["status"] for x in result}=={"ACQUIRED_VERIFIED"}; assert len(r.registry.snapshot()["models"])==3
    again=r.acquire_many([spec("org/model-0")],concurrency=3); assert again[0]["status"]=="DUPLICATE_SUPPRESSED"
