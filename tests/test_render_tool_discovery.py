import importlib

from src.model_scout import resources

scout_module = importlib.import_module("src.model_scout.scout")


def test_renderer_discovery_uses_only_audited_pypi_package_names(monkeypatch):
    import io
    import json

    seen = []
    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *args): self.close()

    def urlopen(request, timeout):
        seen.append(request.full_url)
        name = request.full_url.split("/")[-2]
        payload = {"info": {"version": "1.2.3", "classifiers": ["License :: OSI Approved :: MIT License"]},
                   "urls": [{"filename": f"{name}-1.2.3-py3-none-any.whl", "packagetype": "bdist_wheel",
                             "digests": {"sha256": "a" * 64}, "size": 123, "yanked": False}]}
        return Response(json.dumps(payload).encode())

    monkeypatch.setattr(resources.urllib.request, "urlopen", urlopen)
    result = scout_module.scout("AVORA GLB PBR Mapping Render; past OCR unrelated", resource_type="tool")
    assert [item["model_id"] for item in result["candidates"]] == [
        "pypi/pyrender", "pypi/trimesh", "pypi/open3d"
    ]
    assert all(item["resource_type"] == "tool" and item["revision"] == "1.2.3" for item in result["candidates"])
    assert all(item["status"] == "LICENSE_REVIEW_REQUIRED" and item["reported_license_classifier"] == "mit"
               for item in result["candidates"])
    assert seen == [f"https://pypi.org/pypi/{name}/json" for name in resources.RENDER_TOOL_PACKAGES]
