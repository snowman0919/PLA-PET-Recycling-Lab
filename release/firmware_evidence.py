"""현재 원본·출시 소스와 HEX의 manifest 일치 검사 (재빌드 증명은 별도)."""
import hashlib
import json
from pathlib import Path


def firmware_evidence_current(root: Path) -> bool:
    try:
        fw = root / "exports/final/firmware"
        manifest = json.loads((fw / "build_manifest.json").read_text(encoding="utf-8"))
        sources = manifest.get("source_files", {})
        if manifest.get("status") != "PASS" or manifest.get("source_kind") != "GGM_BTS7960_VARIANT" or not sources:
            return False
        variant = root / manifest.get("variant_source_dir", "")
        released = fw / "source/arduino_mega"
        for base in (variant, released):
            if not base.is_dir(): return False
            files = {p.relative_to(base).as_posix(): p for p in base.rglob("*")
                     if p.is_file() and not {"__pycache__", "build"} & set(p.relative_to(base).parts)}
            extra_inputs = {name for name in set(files) - set(sources)
                            if Path(name).suffix.lower() in {".ino", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".s", ".a"}}
            if not set(sources) <= set(files) or extra_inputs:
                return False
            if any(hashlib.sha256(files[name].read_bytes()).hexdigest() != digest
                   for name, digest in sources.items()):
                return False
        variant_manifest_path = root / manifest.get("variant_manifest", "")
        variant_manifest = json.loads(variant_manifest_path.read_text(encoding="utf-8"))
        if hashlib.sha256(variant_manifest_path.read_bytes()).hexdigest() != manifest.get("variant_manifest_sha256"):
            return False
        if variant_manifest.get("profile") != "GGM-DRIVE-v0.8-r1" or variant_manifest.get("hardware_enabled") is not False:
            return False
        for name,digest in variant_manifest.get("source_sha256",{}).items():
            p = root/name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                return False
        binary = fw / "binaries/filament_recycler_atmega2560.hex"
        return binary.is_file() and hashlib.sha256(binary.read_bytes()).hexdigest() == manifest.get("binary_sha256")
    except (OSError, ValueError, TypeError, AttributeError, json.JSONDecodeError):
        return False
