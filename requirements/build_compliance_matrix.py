#!/usr/bin/env python3
"""Render the auditable requirement disposition matrix from its CSV source."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "requirements" / "compliance_matrix.csv"
OUTPUT = ROOT / "requirements" / "compliance_matrix.md"


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    counts = Counter(row["Disposition"] for row in rows)
    lines = [
        "# 요구사항 준수·증거 매트릭스",
        "",
        "기준일: 2026-08-28. 이 표는 설계 증거와 물리 합격을 분리한다. `AUTOMATED_PASS`는 현재 저장소에서 완결된 검사/문서 gate, `DESIGN_EVIDENCE`는 구현·해석 증거가 있으나 물리 T/D가 열린 상태, `PHYSICAL_OPEN`은 성능 측정이 핵심인 상태, `BLOCKED_EXTERNAL`은 donor·선정부품·견적 없이는 닫을 수 없는 상태다.",
        "",
        "## 집계",
        "",
        "| 상태 | 수 |",
        "|---|---:|",
    ]
    lines.extend(f"| {status} | {count} |" for status, count in sorted(counts.items()))
    lines.extend([
        "",
        f"총 {len(rows)}개 요구사항이다. 물리 시험이나 외부 증거가 필요한 행은 자동 검사 통과로 닫지 않는다.",
        "",
        "## 추적표",
        "",
        "| ID | 판정 | 로컬 증거 | 자동 증거 | 남은 검증 | 책임 |",
        "|---|---|---|---|---|---|",
    ])
    for row in rows:
        evidence = "<br>".join(f"`{path}`" for path in row["Local evidence"].split(";"))
        automated = "<br>".join(f"`{path}`" for path in row["Automated evidence"].split(";"))
        lines.append(
            f"| {row['Requirement ID']} | {row['Disposition']} | {evidence} | "
            f"{automated} | {row['Open verification']} | {row['Owner']} |"
        )
    lines.extend([
        "",
        "## 해석 제한",
        "",
        "- 이 매트릭스는 요구사항 누락을 드러내기 위한 감사표이며 CE/UL/KC 또는 기계안전 인증서가 아니다.",
        "- `DESIGN_EVIDENCE`와 `PHYSICAL_OPEN`은 release 승인과 동의어가 아니다.",
        "- 사용자 승인 없는 구매·CNC 주문·고전류 통전은 수행하지 않는다.",
    ])
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"compliance requirements={len(rows)} " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
