"""Fail the workflow after evidence upload when request intake was not verified."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(path: str = "autonomous-cycle-evidence.json") -> int:
    try:
        cycle = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        access = cycle["discovery_access"]
        failures = access.get("failed_repositories", [])
        if access.get("status") == "PASS" and not failures:
            print("DISCOVERY_ACCESS_PASS (does not certify request delivery or model quality)")
            return 0
        codes = {item.get("status_code") for item in failures}
        cause = "PERMISSION_BLOCK" if 401 in codes or 403 in codes else "GITHUB_WRITE_PATH_FAILURE"
        print(f"::error::{cause}: repository discovery failed; inspect preserved discovery_access evidence. Request delivery is unverified.")
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        print("::error::VERIFY_REQUIRED: missing or invalid discovery evidence")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "autonomous-cycle-evidence.json"))
