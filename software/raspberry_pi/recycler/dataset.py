"""Append-only, content-addressed calibration dataset manifest."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_FIELDS = {
    "sample_id",
    "source_object_id",
    "material_truth",
    "color_truth",
    "thickness_mm",
    "camera_exposure_us",
    "camera_gain",
    "current_rms_a",
    "current_peak_a",
    "speed_drop_fraction",
    "vibration_peak_g",
}


def append_sample(manifest: str | Path, image: str | Path, metadata: dict) -> dict:
    missing = REQUIRED_FIELDS - metadata.keys()
    if missing:
        raise ValueError(f"missing dataset fields: {sorted(missing)}")
    if metadata["material_truth"] not in {"PLA", "PET", "UNKNOWN"}:
        raise ValueError("invalid material truth")
    image_path = Path(image)
    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
    record = dict(metadata)
    record.update(
        {
            "image_path": str(image_path),
            "image_sha256": digest,
            "recorded_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
    )
    manifest_path = Path(manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return record
