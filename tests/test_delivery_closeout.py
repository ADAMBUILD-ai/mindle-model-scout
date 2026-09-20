import tempfile, unittest
from pathlib import Path
from src.model_scout.delivery_closeout import DeliveryEvidence, DeliveryFinalizer, CloseoutBlocked

def evidence(**kw):
    base=dict(central_issue=48,source_repository="ADAMBUILD-ai/mindle-model-scout",source_issue=48,route_fingerprint="fp-48",model_id="PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx + OpenCV HoughLinesP",revision="ocr:5c6f574b8e2230adf4287b33e736d71b9fabd28e",license="apache-2.0",input_sha256="a"*64,output_sha256="b"*64,output_path="output.json",output_size=147836,exact_commit="74fbcafa49ca8590f77fec48b10e9f8dc71f9d7f",workflow_run_id=35408727110,artifact_id=10602056587,callback_target="https://example.test/issues/8")
    base.update(kw); return DeliveryEvidence(**base)

class DeliveryCloseoutTests(unittest.TestCase):
    def test_ack_alone_is_not_delivered(self):
        with tempfile.TemporaryDirectory() as d:
            f=DeliveryFinalizer(Path(d)/"ledger.json",lambda *_:"https://example.test/c")
            with self.assertRaisesRegex(CloseoutBlocked,"ACK_ALONE"): f.finalize(evidence(state_before="ACK_RECEIVED"),"x")
    def test_missing_callback_target_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            f=DeliveryFinalizer(Path(d)/"ledger.json",lambda *_:"https://example.test/c")
            with self.assertRaisesRegex(CloseoutBlocked,"BLOCKED_CONFIG"): f.finalize(evidence(callback_target=""),"x")
    def test_callback_failure_keeps_tested_pass(self):
        with tempfile.TemporaryDirectory() as d:
            def fail(*_): raise RuntimeError("network")
            f=DeliveryFinalizer(Path(d)/"ledger.json",fail)
            with self.assertRaises(RuntimeError): f.finalize(evidence(),"x")
            self.assertEqual(f.records["fp-48"]["state"],"TESTED_PASS")
    def test_success_and_idempotent_rerun(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def send(target,body): calls.append((target,body)); return "https://example.test/issues/8#comment-1"
            f=DeliveryFinalizer(Path(d)/"ledger.json",send)
            first=f.finalize(evidence(),"sanitized")
            second=f.finalize(evidence(),"sanitized")
            self.assertEqual(first["state_after"],"DELIVERED"); self.assertTrue(second["idempotent"]); self.assertEqual(len(calls),1)
if __name__=="__main__": unittest.main()
