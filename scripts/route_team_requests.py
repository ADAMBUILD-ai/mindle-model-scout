from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.model_scout.team_router import GitHubChildIssueWriter, TeamRegistry, TeamRouter


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
    root = Path(__file__).resolve().parents[1]
    registry = TeamRegistry.load(root / "config" / "team-registry.json")
    router = TeamRouter(registry, GitHubChildIssueWriter())
    records = []
    for route in ROUTES:
        issue = int(route["central_issue"])
        records.append(
            router.route(
                **route,
                central_repository=CENTRAL_REPOSITORY,
                callback_url=f"https://github.com/{CENTRAL_REPOSITORY}/issues/{issue}",
            )
        )
    print(
        json.dumps(
            [
                {
                    "central_issue": record.central_issue,
                    "child_repository": record.child_repository,
                    "child_issue": record.child_issue,
                    "child_url": record.child_url,
                    "state": record.state,
                    "ack_deadline": record.ack_deadline.isoformat(),
                }
                for record in records
            ],
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
