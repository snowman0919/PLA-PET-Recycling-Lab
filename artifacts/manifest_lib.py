"""Decision-relevant artifact hashing shared by build and validation.

The canonical hash deliberately removes only tool-generated container noise:
STEP timestamps/translator counters, FCStd topological history maps, and ZIP
member timestamps.  Manufacturing geometry and slicer member contents remain
inside the hash boundary.
"""

from __future__ import annotations

import hashlib
import re
import zipfile
from collections.abc import Iterable
from pathlib import Path


PATTERNS = (
    "README.md", "CHANGELOG.md", "AGENTS.md",
    ".github/workflows/ci-light.yml", ".github/workflows/ci-full.yml",
    "artifacts/*.py",
    "control/**/*",
    "cad/parameters/*.json", "cad/freecad/**/*.py", "cad/generation/*.py", "cad/generation/*.csv", "cad/generation/*.json",
    "cad/README.md", "cad/manufacturing_object_audit.csv",
    "cad/generation/fcstd/*.FCStd",
    "cad/generation/assembly_metadata.json",
    "exports/step/*.step",
    "exports/cnc/**/*.FCStd", "exports/cnc/**/*.step", "exports/cnc/**/*.dxf", "exports/cnc/**/*.md", "exports/cnc/**/*.pdf", "exports/cnc/*.csv",
    "exports/drive_interface/**/*", "exports/jigs/**/*",
    "exports/print/**/*.FCStd", "exports/print/**/*.step", "exports/print/**/*.stl", "exports/print/**/*.3mf",
    "exports/print/**/*.md", "exports/print/**/*.py", "exports/print/**/*.svg", "exports/print/**/*.csv", "exports/print/*.csv",
    "exports/print/slicer_profiles/*",
    "renders/**/*.png", "docs/*.pdf", "docs/*.typ", "docs/*.md",
    "bom/*.csv", "bom/*.md", "bom/*.py", "calculations/*.md", "calculations/*.csv", "calculations/*.py", "calculations/economics/*.md",
    "decisions/*.md", "electronics/*.md", "electronics/*.csv",
    "firmware/arduino_mega/Makefile", "firmware/arduino_mega/*.md", "firmware/arduino_mega/*.py", "firmware/arduino_mega/*.ino", "firmware/arduino_mega/src/*", "firmware/arduino_mega/tests/*",
    "simulation/*.json", "simulation/openmodelica/**/*.mo", "simulation/openmodelica/**/*.mos",
    "simulation/openmodelica/**/*.json", "simulation/openmodelica/**/*.md", "simulation/openmodelica/results/plots/*.svg",
    "analysis/**/*.py", "analysis/**/*.json", "analysis/**/*.md", "analysis/structural/generated/*.inp",
    "requirements/*.md", "validation/*.py", "validation/*.md", "validation/test_plans/*.md", "validation/visual_review/*.md", "validation/physical_gate_status.json", "validation/results/*.json",
)


def collect_paths(root: Path) -> list[Path]:
    return sorted({
        path
        for pattern in PATTERNS
        for path in root.glob(pattern)
        if path.is_file()
        and "simulation/openmodelica/results/raw" not in path.as_posix()
        and not ("exports/print/slicing_previews" in path.as_posix() and path.suffix == ".gcode")
    })


def _frame_members(members: Iterable[tuple[str, bytes]]) -> bytes:
    framed = bytearray()
    for name, data in members:
        encoded_name = name.encode("utf-8")
        framed.extend(len(encoded_name).to_bytes(4, "big"))
        framed.extend(encoded_name)
        framed.extend(len(data).to_bytes(8, "big"))
        framed.extend(data)
    return bytes(framed)


def _normalized_step(data: bytes) -> bytes:
    text = data.decode("ascii")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'2000-01-01T00:00:00'", text, count=1)
    text = re.sub(
        r"Open CASCADE STEP translator ([0-9.]+) [0-9]+",
        r"Open CASCADE STEP translator \1 0",
        text,
    )
    return text.replace("\r\n", "\n").encode("ascii")


def _normalized_zip(path: Path, *, exclude_shape_map: bool) -> bytes:
    with zipfile.ZipFile(path, "r") as archive:
        members = []
        for name in sorted(archive.namelist()):
            if exclude_shape_map and name.endswith(".Shape.Map.txt"):
                continue
            members.append((name, archive.read(name)))
    return _frame_members(members)


def artifact_record(path: Path, root: Path) -> dict[str, object]:
    suffix = path.suffix.lower()
    if suffix in {".step", ".stp"}:
        canonical = _normalized_step(path.read_bytes())
        mode = "STEP_TEXT_NORMALIZED_V1"
    elif suffix == ".fcstd":
        canonical = _normalized_zip(path, exclude_shape_map=True)
        mode = "FCSTD_DOCUMENT_BREP_V1"
    elif suffix == ".3mf":
        canonical = _normalized_zip(path, exclude_shape_map=False)
        mode = "ZIP_MEMBER_CONTENT_V1"
    else:
        canonical = path.read_bytes()
        mode = "RAW_SHA256_V1"
    return {
        "path": path.relative_to(root).as_posix(),
        "hash_mode": mode,
        "normalized_bytes": len(canonical),
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }
