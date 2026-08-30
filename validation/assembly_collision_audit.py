#!/usr/bin/env python3
"""전체 nominal assembly의 B-Rep 체적 간섭을 열거하고 정책 외 간섭을 차단한다."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad/freecad/compact"))
from geometry import assembly_objects  # noqa: E402


TOLERANCE_MM3 = 0.05

ALLOWED_INTERFACES = {
    frozenset(("CutterSprocket30T", "ChainTightSide")): "보수적 chain LOD와 sprocket 맞물림 체적",
    frozenset(("CutterSprocket30T", "ChainSlackSide")): "보수적 chain LOD와 sprocket 맞물림 체적",
    frozenset(("SealedFeedHopper", "FeedTransferChute")): "밀폐 hopper 용접/socket 삽입부",
    frozenset(("FeedTransferChute", "FeederHousing")): "feeder 용접/socket 삽입부",
    frozenset(("Spool", "SpoolCore")): "구매 spool envelope 안의 reference core",
    frozenset(("Spool", "SpoolSpindle")): "구매 spool envelope 안의 실제 spindle",
    frozenset(("SpoolCore", "SpoolSpindle")): "reference core bore를 solid LOD로 표시한 의도된 중첩",
    frozenset(("Spool", "PPR-C09_SpoolAdapterFront")): "구매 spool 기준 envelope와 조절식 cone 삽입 깊이의 보수적 중첩",
    frozenset(("Spool", "PPR-C09_SpoolAdapterRear")): "구매 spool 기준 envelope와 조절식 cone 삽입 깊이의 보수적 중첩",
    frozenset(("SpoolCore", "PPR-C09_SpoolAdapterFront")): "실측 전 generic core solid LOD에 표시한 cone 접촉/삽입부",
    frozenset(("SpoolCore", "PPR-C09_SpoolAdapterRear")): "실측 전 generic core solid LOD에 표시한 cone 접촉/삽입부",
    frozenset(("HeaterCableDuctBridgeX", "HeaterCableDuctBridgeY")): "18x18 고정 금속 duct의 의도된 L자 결합부",
}


def boxes_overlap(a, b):
    aa = a.BoundBox
    bb = b.BoundBox
    return not (
        aa.XMax <= bb.XMin or bb.XMax <= aa.XMin
        or aa.YMax <= bb.YMin or bb.YMax <= aa.YMin
        or aa.ZMax <= bb.ZMin or bb.ZMax <= aa.ZMin
    )


def main():
    objects = assembly_objects(False)
    hits = []
    unexpected = []
    for index, left in enumerate(objects):
        for right in objects[index + 1:]:
            if not boxes_overlap(left["shape"], right["shape"]):
                continue
            volume = left["shape"].common(right["shape"]).Volume
            if volume > TOLERANCE_MM3:
                pair = frozenset((left["name"], right["name"]))
                reason = ALLOWED_INTERFACES.get(pair)
                row = {
                    "left": left["name"],
                    "right": right["name"],
                    "overlap_mm3": round(volume, 3),
                    "left_class": left["classification"],
                    "right_class": right["classification"],
                    "allowed": reason is not None,
                    "reason": reason or "정책에 없는 체적 간섭",
                }
                hits.append(row)
                if reason is None:
                    unexpected.append(row)
    output = ROOT / "validation/results/assembly_pairwise_collisions.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "revision": "implementation-crosssolver-v0.6",
        "pair_count": len(objects) * (len(objects) - 1) // 2,
        "tolerance_mm3": TOLERANCE_MM3,
        "overlaps": hits,
        "unexpected_count": len(unexpected),
        "status": "PASS" if not unexpected else "FAIL",
    }, ensure_ascii=False, indent=2) + "\n")
    if unexpected:
        for hit in unexpected:
            print(f"UNEXPECTED {hit['left']} / {hit['right']}: {hit['overlap_mm3']} mm3")
        raise AssertionError(f"정책 외 assembly 체적 간섭 {len(unexpected)}건")
    print(f"ASSEMBLY_PAIRWISE_COLLISION_POLICY_OK pairs={len(objects) * (len(objects) - 1) // 2} allowed={len(hits)} unexpected=0")


if __name__ == "__main__":
    main()
