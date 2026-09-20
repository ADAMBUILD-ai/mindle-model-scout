from __future__ import annotations
import json, time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Callable, Any

class CloseoutState(str, Enum):
    REQUESTED="REQUESTED"; FOUND="FOUND"; DOWNLOADED="DOWNLOADED"; TESTED_PASS="TESTED_PASS"
    CALLBACK_SENT="CALLBACK_SENT"; DELIVERED="DELIVERED"; BLOCKED_CONFIG="BLOCKED_CONFIG"
    BLOCKED_INPUT="BLOCKED_INPUT"; BLOCKED_APPROVAL="BLOCKED_APPROVAL"; FAILED_RETRYABLE="FAILED_RETRYABLE"

class CloseoutBlocked(RuntimeError): pass

@dataclass(frozen=True)
class DeliveryEvidence:
    central_issue: int
    source_repository: str
    source_issue: int
    route_fingerprint: str
    model_id: str
    revision: str
    license: str
    input_sha256: str
    output_sha256: str
    output_path: str
    output_size: int
    exact_commit: str
    workflow_run_id: int
    artifact_id: int
    callback_target: str = ""
    state_before: str = "TESTED_PASS"
    timestamp: str = ""
    def as_dict(self):
        d=asdict(self); d["output_size"]=int(d["output_size"]); return d

class DeliveryFinalizer:
    def __init__(self, ledger_path: str|Path, sender: Callable[[str,str],str]|None=None):
        self.path=Path(ledger_path); self.path.parent.mkdir(parents=True,exist_ok=True); self.sender=sender
        self.records=self._load()
    def _load(self):
        if not self.path.exists(): return {}
        payload=json.loads(self.path.read_text(encoding="utf-8"))
        return payload.get("records",{}) if isinstance(payload,dict) else {}
    def _save(self):
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps({"records":self.records},ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        tmp.replace(self.path)
    @staticmethod
    def _validate(e: DeliveryEvidence):
        if e.state_before!="TESTED_PASS": raise CloseoutBlocked("ACK_ALONE_IS_NOT_DELIVERED")
        if not e.callback_target: raise CloseoutBlocked("BLOCKED_CONFIG: missing authoritative callback target")
        required=(e.model_id,e.revision,e.license,e.input_sha256,e.output_sha256,e.output_path,e.exact_commit,e.route_fingerprint)
        if any(not str(x).strip() for x in required) or e.output_size<=0 or e.central_issue<=0 or e.source_issue<=0:
            raise CloseoutBlocked("BLOCKED_INPUT: incomplete request-level evidence")
        if len(e.input_sha256)!=64 or len(e.output_sha256)!=64:
            raise CloseoutBlocked("BLOCKED_INPUT: invalid SHA-256 evidence")
    def finalize(self,e: DeliveryEvidence, body: str):
        key=e.route_fingerprint
        old=self.records.get(key)
        if old and old.get("state")==CloseoutState.DELIVERED.value:
            return {"state_before":"DELIVERED","state_after":"DELIVERED","idempotent":True,"duplicate_suppressed":True,"callback_url":old.get("callback_url")}
        self._validate(e)
        now=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        if self.sender is None: raise CloseoutBlocked("BLOCKED_CONFIG: callback sender unavailable")
        try:
            callback_url=self.sender(e.callback_target,body)
        except Exception as exc:
            record={"state":CloseoutState.TESTED_PASS.value,"state_before":"TESTED_PASS","state_after":"TESTED_PASS","route_fingerprint":key,"error":type(exc).__name__,"updated_at":now,"evidence":e.as_dict()}
            self.records[key]=record; self._save(); raise
        record={"state":CloseoutState.DELIVERED.value,"state_before":"TESTED_PASS","state_after":"DELIVERED","route_fingerprint":key,"callback_url":callback_url,"callback_sent_at":now,"delivered_at":now,"evidence":e.as_dict()}
        self.records[key]=record; self._save()
        return {"state_before":"TESTED_PASS","state_after":"DELIVERED","idempotent":False,"duplicate_suppressed":False,"callback_url":callback_url}
