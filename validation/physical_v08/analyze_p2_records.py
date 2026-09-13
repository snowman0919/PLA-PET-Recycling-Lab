#!/usr/bin/env python3
"""Fail-closed P2 cold-frame/fit evidence checker with bound fabrication prerequisites."""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
P1_ANALYZER = HERE / "analyze_p1_records.py"
MOUNT_ANALYZER = HERE / "analyze_ggm_mount_compatibility.py"
NESTING_ANALYZER = HERE / "profile_nesting.py"
FRAME_CUTLIST = ROOT / "exports/fabrication/frame_cut_list.csv"
SOURCE_BINDINGS = (
    "docs/drawings/drawing_register.csv",
    "docs/final/assembly_steps.csv",
    "exports/fabrication/frame_cut_list.csv",
    "exports/final/frame_v08/frame_release.json",
)

NUMERIC = {
    "frame_base_x": ("range", (469.2, 470.8), "mm"),
    "frame_base_y": ("range", (699.2, 700.8), "mm"),
    "rail_squareness_700": ("max", 0.50, "mm"),
    "shredder_min_static_clearance": ("min", 1.90, "mm"),
    "shredder_hand_rotation_contacts": ("max", 0.0, "count"),
    "extruder_cold_axial_travel": ("min", 1.50, "mm"),
    "extruder_rear_retainer_endplay": ("range", (0.12, 0.28), "mm"),
    "frame_diagonal_a": ("positive", None, "mm"),
    "frame_diagonal_b": ("positive", None, "mm"),
}
BOOL_FALSE = {"frame_rocking", "guard_moving_envelope_intrusion", "guard_hot_envelope_intrusion"}
REQUIRED = set(NUMERIC) | BOOL_FALSE
APPROVAL_SCOPE = "P2_BOUND_CUT_PRINT_ASSEMBLY_ONLY"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load " + str(path))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def repo_file(value, label: str, root: Path = ROOT) -> Path:
    if value is None or not str(value).strip():
        raise ValueError(label + " missing")
    path = Path(value); path = path if path.is_absolute() else root / path
    path = path.resolve(); resolved_root = root.resolve()
    if not path.is_relative_to(resolved_root) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value, field: str) -> float:
    if value is None or not str(value).strip():
        raise ValueError(field + ": blank numeric field")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(field + ": non-finite value")
    return out


def require_time(value: str, field: str) -> None:
    parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(field + " must include timezone")


def verify_evidence(row: dict[str, str], root: Path, numeric: bool) -> None:
    metric = row.get("metric", "?")
    fields = ["operator", "reviewer", "measured_at", "evidence_path", "sha256"]
    if numeric:
        fields += ["instrument_id", "instrument_calibration_ref"]
    missing = [field for field in fields if not row.get(field, "").strip()]
    if missing:
        raise ValueError(f"{metric}: incomplete provenance: {','.join(missing)}")
    if row["operator"].strip() == row["reviewer"].strip():
        raise ValueError(f"{metric}: independent reviewer must differ from operator")
    require_time(row["measured_at"], metric + " measured_at")
    path = repo_file(row["evidence_path"], metric + " evidence", root)
    digest = row["sha256"].strip().lower()
    if len(digest) != 64 or sha(path) != digest:
        raise ValueError(f"{metric}: stale evidence hash")


def interval_pass(value: float, u95: float, mode: str, limit) -> bool:
    if u95 < 0:
        return False
    if mode == "max": return value + u95 <= float(limit)
    if mode == "min": return value - u95 >= float(limit)
    if mode == "range":
        lo, hi = limit; return value - u95 >= lo and value + u95 <= hi
    if mode == "positive": return value - u95 > 0
    raise ValueError("unknown criterion mode")


def evaluate_measurements(rows: list[dict[str, str]], root: Path = ROOT) -> dict:
    by_metric={}
    for row in rows:
        metric=row.get("metric", "").strip()
        if not metric or metric in by_metric:
            raise ValueError("blank or duplicate P2 metric")
        by_metric[metric]=row
    missing=sorted(REQUIRED-set(by_metric)); extra=sorted(set(by_metric)-REQUIRED)
    if missing: raise ValueError("missing required metrics: " + ", ".join(missing))
    if extra: raise ValueError("unexpected metrics: " + ", ".join(extra))
    source_hashes={name:sha(root/name) for name in SOURCE_BINDINGS if (root/name).is_file()}
    if len(source_hashes) != len(SOURCE_BINDINGS):
        raise ValueError("missing P2 controlling source")
    out={"status":"PASS", "checks":{}, "source_bindings_sha256":source_hashes}
    values={}; uncertainties={}
    for metric,(mode,limit,unit) in NUMERIC.items():
        row=by_metric[metric]; verify_evidence(row,root,True)
        if row.get("unit", "").strip()!=unit: raise ValueError(f"{metric}: unit must be {unit}")
        value=number(row.get("value"),metric); u95=number(row.get("u95"),metric+" U95")
        if value<0 or u95<0: raise ValueError(f"{metric}: negative physical value or U95")
        if metric=="shredder_hand_rotation_contacts" and not value.is_integer():
            raise ValueError(metric+": contact count must be integer")
        ok=interval_pass(value,u95,mode,limit); values[metric]=value; uncertainties[metric]=u95
        out["checks"][metric]={"value":value,"u95":u95,"unit":unit,"criterion":mode,"limit":limit,"pass":ok}
        if not ok: out["status"]="FAIL"
    diff=abs(values["frame_diagonal_a"]-values["frame_diagonal_b"])
    bound=diff+uncertainties["frame_diagonal_a"]+uncertainties["frame_diagonal_b"]
    ok=bound<=1.0; out["checks"]["frame_diagonal_difference"]={"difference_mm":diff,"u95_conservative_bound_mm":bound,"limit_mm":1.0,"pass":ok}
    if not ok: out["status"]="FAIL"
    for metric in sorted(BOOL_FALSE):
        row=by_metric[metric]; verify_evidence(row,root,False)
        if row.get("unit", "").strip()!="boolean": raise ValueError(metric+": unit must be boolean")
        token=row.get("value", "").strip().lower()
        if token not in {"false","0","no","true","1","yes"}: raise ValueError(metric+": invalid boolean")
        ok=token in {"false","0","no"}; out["checks"][metric]={"value":token,"pass":ok}
        if not ok: out["status"]="FAIL"
    return out


def verify_approval(path: Path, inventory: Path, packet: Path, stock: Path, kerf_mm: float, root: Path) -> dict:
    path=repo_file(path,"P2 fabrication approval",root)
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("stage")!="P2" or data.get("status")!="APPROVED" or data.get("scope")!=APPROVAL_SCOPE:
        raise ValueError("P2 fabrication approval state/scope invalid")
    if data.get("procurement_authorized") is not False or data.get("energization_authorized") is not False:
        raise ValueError("P2 approval must not authorize procurement or energization")
    if not isinstance(data.get("approved_by"),str) or not data["approved_by"].strip():
        raise ValueError("P2 fabrication approval missing approved_by")
    require_time(data.get("approved_at", ""),"P2 approved_at")
    bindings={"p1_inventory_sha256":inventory,"ggm_packet_sha256":packet,"profile_stock_sha256":stock,"frame_cut_list_sha256":root/"exports/fabrication/frame_cut_list.csv", "frame_release_sha256":root/"exports/final/frame_v08/frame_release.json"}
    for field,target in bindings.items():
        if data.get(field)!=sha(target): raise ValueError(field+" mismatch")
    approved_kerf=number(data.get("kerf_budget_mm"),"P2 approved kerf")
    if approved_kerf<0 or not math.isclose(approved_kerf,kerf_mm,abs_tol=1e-12):
        raise ValueError("P2 kerf budget differs from approval")
    return {"approval_sha256":sha(path),"approved_by":data["approved_by"],"approved_at":data["approved_at"],"scope":APPROVAL_SCOPE}


def validate_prerequisites(inventory: Path, packet: Path, stock: Path, kerf_mm: float, approval: Path, root: Path = ROOT) -> dict:
    if not math.isfinite(kerf_mm) or kerf_mm < 0: raise ValueError("kerf budget must be finite and non-negative")
    inventory=repo_file(inventory,"P1 inventory",root); packet=repo_file(packet,"GGM receipt packet",root); stock=repo_file(stock,"profile stock record",root)
    from frame_release import validate as validate_frame
    frame=validate_frame(root)
    ggm=json.loads(packet.read_text(encoding="utf-8"))
    p1=load(P1_ANALYZER,"ppr_p2_p1")
    p1_result=p1.evaluate(p1.read_csv(inventory),root,ggm)
    if p1_result.get("status")!="P1_RECORD_CHECK_PASS": raise ValueError("P1 full inventory/receipt prerequisite is not PASS")
    mount=load(MOUNT_ANALYZER,"ppr_p2_mount").evaluate(ggm)
    if mount.get("status")!="AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED": raise ValueError("GGM mount is not as-drawn compatible")
    nesting=load(NESTING_ANALYZER,"ppr_p2_nesting")
    req=nesting.requirements(root); measured=nesting.measured(stock, root); profile_results={}
    raw_stock={r["record_id"].strip():r for r in read_rows(stock) if r.get("status", "").strip().upper() in {"USABLE", "PASS"}}
    for typ in ("2020","2040"):
        if not measured[typ]: raise ValueError(typ+" profile stock missing")
        declared=p1_result["semantic_checks"]["ASSET-"+typ]["stock_records"]
        for bar_id, _ in measured[typ]:
            prior=declared.get(bar_id); current=raw_stock[bar_id]
            if prior is None or prior["profile_type"] != typ or any(float(current[k]) != prior[k] for k in ("usable_length_mm", "u95_length_mm")):
                raise ValueError(typ+" profile stock differs from authenticated P1 bar identity/measurement")
        ok,plan=nesting.solve(req[typ],measured[typ],kerf_mm)
        if not ok: raise ValueError(typ+" profile stock is insufficient or unnested")
        canonical_plan=[]
        for bar in plan:
            canonical_plan.append({**bar, "cuts": [[part_id, length] for part_id, length in bar["cuts"]]})
        profile_results[typ]={"required_piece_count":len(req[typ]),"plan":canonical_plan}
    approval_result=verify_approval(approval,inventory,packet,stock,kerf_mm,root)
    return {
        "p1_status":p1_result["status"], "p1_inventory_sha256":sha(inventory),
        "ggm_packet_sha256":sha(packet), "mount_status":mount["status"],
        "profile_stock_sha256":sha(stock), "kerf_budget_mm":kerf_mm,
        "profile_nesting":profile_results, "fabrication_approval":approval_result,
        "frame_design":frame,
    }


def evaluate(record: Path, inventory: Path, packet: Path, stock: Path, kerf_mm: float, approval: Path, root: Path = ROOT) -> dict:
    out={"status":"NOT_RUN_OR_REJECTED","record_check_only":True,"physical_evidence_evaluated":False,
         "fabrication_authorized":False,"energization_authorized":False,"stage_release_granted":False,"machine_release":"HOLD"}
    try:
        record=repo_file(record,"P2 cold-fit record",root)
        prerequisites=validate_prerequisites(inventory,packet,stock,kerf_mm,approval,root)
        measured=evaluate_measurements(read_rows(record),root)
        if measured["status"]!="PASS": raise ValueError("P2 cold-fit measurements failed acceptance")
        out.update({"status":"P2_RECORD_CHECK_PASS","physical_evidence_evaluated":True,
                    "record_sha256":sha(record),"prerequisites":prerequisites,
                    "checks":measured["checks"],"source_bindings_sha256":measured["source_bindings_sha256"]})
    except (ValueError,KeyError,TypeError,FileNotFoundError,json.JSONDecodeError) as exc:
        out["reason"]=str(exc)
    return out


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("record",type=Path)
    ap.add_argument("--p1-inventory",required=True,type=Path); ap.add_argument("--ggm-packet",required=True,type=Path)
    ap.add_argument("--profile-stock",required=True,type=Path); ap.add_argument("--kerf-mm",required=True,type=float)
    ap.add_argument("--fabrication-approval",required=True,type=Path); ap.add_argument("--output",type=Path)
    args=ap.parse_args(); result=evaluate(args.record,args.p1_inventory,args.ggm_packet,args.profile_stock,args.kerf_mm,args.fabrication_approval)
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"; print(text,end="")
    if args.output: args.output.write_text(text,encoding="utf-8")
    raise SystemExit(0 if result["status"]=="P2_RECORD_CHECK_PASS" else 2)


if __name__=="__main__": main()
