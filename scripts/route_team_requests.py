from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model_scout.team_router import GitHubChildIssueWriter, RouteLedger, TeamRegistry, TeamRouter


CENTRAL_REPOSITORY = "ADAMBUILD-ai/mindle-model-scout"
ROUTES = (
    {
        "team_id": "mindle-media-ai",
        "central_issue": 50,
        "purpose": "Validate MINDLE MEDIA AI image, video, and Korean STT candidates using actual project originals.",
        "required_input": "3+ JPG/PNG photos, 1+ 10-second MP4/MOV moving-subject video, and 1+ 10-second Korean WAV/MP3/M4A with manifest.txt.",
        "completion_gate": "Provide an accessible original ZIP/artifact and MODEL_SCOUT_ACK; do not substitute generated samples.",
    },
    {
        "team_id": "kimseobang",
        "central_issue": 51,
        "purpose": "Validate Korean STT/TTS and lip-sync candidates using authorized actual source media.",
        "required_input": "1+ 15-30 second Korean WAV/MP3/M4A, 1+ front or semi-front MP4/MOV talking-head video, transcript TXT/DOCX, and manifest.txt.",
        "completion_gate": "Provide an accessible original ZIP/artifact and MODEL_SCOUT_ACK; do not include personal health data.",
    },
    {
        "team_id": "arcos",
        "central_issue": 55,
        "purpose": "Validate geospatial segmentation and map OCR with georeferenced ARCOS source datasets.",
        "required_input": "3+ GeoTIFF/TIFF samples with CRS/EPSG evidence, 2+ OCR maps, metadata, dataset_manifest.csv, expected_checks.json, and manifest.txt.",
        "completion_gate": "Provide an accessible original ZIP/artifact and MODEL_SCOUT_ACK; screenshots without CRS are not valid inputs.",
    },
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    registry = TeamRegistry.load(root / "config" / "team-registry.json")
    writer = GitHubChildIssueWriter()
    state_dir = Path(args.state_dir).resolve()
    router = TeamRouter(registry, writer, ledger=RouteLedger(state_dir / "team-router-routes.json"))
    if not args.audit_only:
        for route in ROUTES:
            issue = int(route["central_issue"])
            router.route(
                **route,
                central_repository=CENTRAL_REPOSITORY,
                callback_url=f"https://github.com/{CENTRAL_REPOSITORY}/issues/{issue}",
            )
    acknowledged = router.collect_acks(writer)
    timed_out = router.audit_ack_timeouts()
    evidence = {
        "acknowledged": [record.as_dict() for record in acknowledged],
        "timed_out": [record.as_dict() for record in timed_out],
        "routes": [record.as_dict() for record in router.records()],
    }
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "team-router-evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
