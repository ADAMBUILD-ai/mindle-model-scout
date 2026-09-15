import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import onnx

OUT = Path("sam21-mission-evidence.json")
COMMERCIAL_LICENSES = {"apache-2.0", "mit", "bsd-3-clause", "bsd-2-clause"}


def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def main():
    evidence = {"status": "BLOCKED"}
    try:
        models = get_json("https://huggingface.co/api/models?search=sam2%20onnx&limit=20&full=true")
        for model in models:
            repository = model.get("modelId") or model.get("id")
            license_name = next((tag[8:] for tag in model.get("tags", []) if tag.startswith("license:")), None)
            if license_name not in COMMERCIAL_LICENSES:
                continue
            metadata = get_json("https://huggingface.co/api/models/" + urllib.parse.quote(repository, safe="/"))
            revision = metadata.get("sha")
            files = [file for file in metadata.get("siblings", []) if file.get("rfilename", "").endswith((".onnx", ".safetensors"))]
            if not files:
                continue
            selected = min(files, key=lambda file: file.get("size", 10**18))
            filename = selected["rfilename"]
            destination = Path("weight" + Path(filename).suffix)
            digest = hashlib.sha256()
            size = 0
            url = f"https://huggingface.co/{repository}/resolve/{revision}/{urllib.parse.quote(filename)}"
            with urllib.request.urlopen(url, timeout=120) as response, destination.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    digest.update(chunk)
                    output.write(chunk)
                    size += len(chunk)
            loaded = onnx.load_model(str(destination), load_external_data=False)
            onnx.checker.check_model(loaded)
            evidence = {
                "status": "DOWNLOADED_AND_ONNX_VALIDATED",
                "repo_id": repository,
                "revision": revision,
                "license": license_name,
                "source_url": f"https://huggingface.co/{repository}",
                "weight_filename": filename,
                "file_format": destination.suffix,
                "file_size": size,
                "sha256": digest.hexdigest(),
                "safe_loader": "ONNX_GRAPH_VALIDATED_NO_REMOTE_CODE_EXECUTED",
            }
            break
    except Exception as error:
        evidence["error_type"] = type(error).__name__
    OUT.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence))
    sys.exit(evidence["status"] != "DOWNLOADED_AND_ONNX_VALIDATED")


if __name__ == "__main__":
    main()
