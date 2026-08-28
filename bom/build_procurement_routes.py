#!/usr/bin/env python3
"""Generate deterministic supplier routing for every system-BOM BUY row."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "Part ID", "Description", "Primary channel", "Alternate channel",
    "AliExpress policy", "Required qualification", "Evidence state",
)


ROUTES = {
    "SHR-BRG-001": ("Korean bearing specialist", "AliExpress sample; authorized bearing distributor", "SAMPLE_ONLY", "6004-2RS 20x42x12; C/C0; seal; fit; shock coupon"),
    "SHR2-BRG-001": ("Korean bearing specialist", "AliExpress sample; authorized bearing distributor", "SAMPLE_ONLY", "6004-2RS 20x42x12; C/C0; seal; fit; shock coupon"),
    "SHR2-SHM-001": ("MISUMI or precision shim specialist", "DeviceMart catalog", "FORBIDDEN", "ground thickness certificate; flatness; hardness; oil compatibility"),
    "GRN-BRG-001": ("DigiKey or Korean bearing specialist", "AliExpress sample", "SAMPLE_ONLY", "6203-2RS 17x40x12; C/C0; seal; fit; shock coupon"),
    "SRT-SCR-TOP": ("Perforated-sheet specialist", "DeviceMart; AliExpress sample", "SAMPLE_ONLY", "6.0 mm aperture; open area; stainless grade; frame retention"),
    "SRT-SCR-BOT": ("Perforated-sheet specialist", "DeviceMart; AliExpress sample", "SAMPLE_ONLY", "3.0 mm aperture; open area; stainless grade; frame retention"),
    "SRT-ISO-001": ("Vibration-mount specialist", "AliExpress sample", "SAMPLE_ONLY", "measured vertical stiffness near 947 N/m each; loss factor; M5 geometry"),
    "DRY-INS-001": ("Industrial insulation supplier", "DeviceMart industrial catalog", "FORBIDDEN", "continuous temperature; noncombustibility; fiber containment; 40 mm installed thickness"),
    "DRY-PLA-HTR": ("Authorized heater supplier", "DeviceMart industrial catalog", "FORBIDDEN", "24 V 60 W; sheath temperature; airflow interlock; 60 C trip; 72 C one-shot fuse"),
    "DRY-PET-HTR": ("Authorized industrial air-heater supplier", "DeviceMart industrial catalog", "FORBIDDEN", "24 V 240 W; 160 C duty; 170 C trip; 184 C fuse; metal airflow path"),
    "DRY-AIR-001": ("Dryer/blower specialist", "DeviceMart blower and desiccant catalog", "FORBIDDEN", "3 m3/h operating point; 160 C isolation; desiccant regeneration; leak test"),
    "DRY-SEN-001": ("Authorized sensor distributor", "DigiKey; DeviceMart", "FORBIDDEN", "three traceable temperature channels; humidity limit; external dew-point port"),
    "EXT-THR-001": ("Bearing specialist", "MISUMI", "FORBIDDEN", "51102 C0/C; radial bearing set; 5.09 kN proof; temperature derating"),
    "EXT-HTR-001": ("Authorized cartridge-heater supplier", "DeviceMart industrial catalog", "FORBIDDEN", "24 V; 3x80 W + 60 W; watt density; sheath; lead temperature; clamp fit"),
    "EXT-SEN-001": ("Industrial pressure/temperature specialist", "DigiKey; DeviceMart for temperature only", "FORBIDDEN", "four hot-zone sensors; calibrated melt pressure 0-20 MPa; cool-bearing channel"),
    "EXT-REL-001": ("Extrusion rupture-disk specialist", "OEM quotation", "FORBIDDEN", "polymer melt service; burst tolerance below 20 MPa proof; guarded discharge; certificate"),
    "GAU-CAM-001": ("Raspberry Pi approved reseller", "DeviceMart", "SAMPLE_ONLY", "Camera Module 3 standard; fixed exposure support; final U95 <=0.020 mm validation"),
    "GAU-OPT-001": ("Machine-vision optics supplier", "AliExpress optical coupon only", "SAMPLE_ONLY", "front-surface mirror; distortion; MTF; backlight stability; combined U95"),
    "SAF-EST-001": ("DigiKey or authorized safety distributor", "Korean industrial automation supplier", "FORBIDDEN", "2NC positive-opening channels; latching reset; 24 VDC rating; enclosure/IP; safety validation"),
    "SAF-REL-001": ("Authorized safety distributor", "DigiKey; AutomationDirect", "FORBIDDEN", "dual-channel input; monitored reset; EDM; required PL/category; output utilization"),
    "SAF-CON-001": ("Authorized contactor distributor", "Korean industrial automation supplier", "FORBIDDEN", "24 VDC coil; positively guided/mirror auxiliary; DC utilization; branch current; suppression"),
    "SAF-FUS-HLD": ("DigiKey or authorized circuit-protection distributor", "Korean industrial panel supplier", "FORBIDDEN", "Class CC; 600 VDC holder rating; finger-safe; terminal conductor range; stock; exact fuse link coordination"),
    "SAF-FUS-001": ("Authorized circuit-protection distributor", "DigiKey; DeviceMart", "FORBIDDEN", "DC voltage; branch current; interrupt rating; fuse coordination; touch-safe holder"),
    "SAF-THM-001": ("DigiKey or authorized thermal-protection distributor", "DeviceMart industrial catalog", "FORBIDDEN", "one-shot; zone-specific Tf/Th; current and DC interruption; mounting derating; approvals"),
    "SAF-INT-001": ("Authorized machine-safety distributor", "DigiKey", "FORBIDDEN", "positive opening; actuator included; contact arrangement; defeat resistance; system PL validation"),
    "ELE-HTR-DRV": ("Authorized power-semiconductor/SSR distributor", "DigiKey; DeviceMart", "FORBIDDEN", "24 VDC load output; worst-case SOA/Rds(on); isolation; default OFF; heat sink; welded-on test"),
    "ELE-HTR-HS": ("DigiKey or authorized Sensata distributor", "Korean industrial thermal supplier", "FORBIDDEN", "three-SSR mounting; thermal resistance; interface material; orientation; enclosure ambient rise"),
    "ELE-SEN-IF": ("PCB assembly plus authorized components", "DigiKey component order", "FORBIDDEN", "native PCB BOM MPN completion; keyed connectors; lifecycle; calibration; no safety credit"),
    "ELE-PCB-IF": ("JLCPCB/PCBWay prototype quotation", "Local PCB fabricator", "FORBIDDEN", "current fabrication HOLD closure; stackup; finish; electrical test; impedance not claimed"),
    "ELE-BUCK-001": ("DigiKey or authorized power distributor", "DeviceMart industrial catalog", "FORBIDDEN", "9-36 V input; regulated 5 V >=5 A; transient; thermal; fuse; no USB backfeed"),
    "MISC-WIR-001": ("DeviceMart and authorized connector distributor", "DigiKey; local panel shop", "FORBIDDEN", "wire gauge; temperature; keyed mating pairs; ferrules; PE lugs; cable-chain rating"),
    "CTL-ENC-001": ("DigiKey or authorized nVent HOFFMAN distributor", "Korean certified enclosure supplier", "FORBIDDEN", "500x400x210 mm; mounting plate; IP/Type/IK; PE provisions; SCCR; gland and thermal-rise review"),
}


def main() -> None:
    with (ROOT / "bom" / "bom.csv").open(newline="", encoding="utf-8") as handle:
        all_rows = list(csv.DictReader(handle))
    buy_rows = [row for row in all_rows if row["Source type"] == "BUY"]
    buy_ids = {row["Part ID"] for row in buy_rows}
    if buy_ids != set(ROUTES):
        raise SystemExit(f"route coverage mismatch missing={sorted(buy_ids-set(ROUTES))} extra={sorted(set(ROUTES)-buy_ids)}")
    evidence_ids: set[str] = set()
    evidence_rows: list[dict[str, str]] = []
    with (ROOT / "bom" / "cost_evidence.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            evidence_ids.add(row["Part ID"])
            evidence_rows.append(row)
    output = ROOT / "bom" / "procurement_routes.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in buy_rows:
            part_id = row["Part ID"]
            primary, alternate, ali_policy, qualification = ROUTES[part_id]
            writer.writerow({
                "Part ID": part_id,
                "Description": row["Description"],
                "Primary channel": primary,
                "Alternate channel": alternate,
                "AliExpress policy": ali_policy,
                "Required qualification": qualification,
                "Evidence state": "CANDIDATE_EVIDENCE_RECORDED" if part_id in evidence_ids else "SEARCH_REQUIRED",
            })
    def safe(value: str) -> str:
        return value.replace("|", "\\|")

    markdown = [
        "# 구매처·가격 후보",
        "",
        "조회일: 2026-08-28. 상태: **비교 후보 / 주문 미승인**.",
        "",
        f"{len(all_rows)}행 시스템 BOM 중 BUY {len(buy_rows)}행을 모두 `procurement_routes.csv`에 연결했고, 그중 {len(evidence_ids & buy_ids)}개 Part ID에 실제 공개 페이지 또는 Playwright 검색 증거를 기록했다. `PRIMARY_CANDIDATE`와 qualification/sizing 후보는 가격·배치 계산용 기준일 뿐 구매·안전 적합성 승인이 아니다.",
        "",
        "| Part ID | 공급처 | 후보/MPN | 관측가 | 재고 | 선택 상태 | 링크 |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for row in evidence_rows:
        price = f"{row['Observed price']} {row['Currency']}"
        candidate = row["Candidate"] + (f" / `{row['MPN']}`" if row["MPN"] else "")
        markdown.append(
            f"| {safe(row['Part ID'])} | {safe(row['Distributor'])} | {safe(candidate)} | "
            f"{safe(price)} | {safe(row['Stock observed'])} | {safe(row['Selection'])} | "
            f"[제품/검색 결과]({row['Source URL']}) |"
        )
    markdown.extend([
        "",
        "## 해석 규칙",
        "",
        "- DigiKey KRW 단가는 제품 페이지의 1개 가격이다. 60,000 KRW 미만 주문의 20,000 KRW 배송비와 수령 시 관세·세금 가능성은 개별 행 가격에 포함하지 않았다.",
        "- 디바이스마트 값은 VAT 포함 표시가를 사용했다. 66,000 KRW 미만 기본 배송 2,700 KRW 및 해외구매/반품 제한은 checkout 전 다시 확인한다.",
        "- AliExpress 4개 검색 결과(5개 BOM evidence 행)는 Playwright Chromium으로 직접 읽었다. 배송·세금·seller·variant·정품 여부가 확정되지 않아 모두 `SAMPLE_ONLY`이고 planning primary로 선택하지 않았다.",
        "- E-stop, safety relay, guard switch, thermal fuse, heater driver, pressure relief/센서는 AliExpress 구매 금지다. 승인 유통망의 datasheet와 추적 가능한 MPN이 필요하다.",
        "- `PARTIAL_ASSEMBLY`는 BOM 행의 일부만 가격이 잡힌 경우다. 예를 들어 D4NS switch body 가격에는 actuator와 cable이 없다.",
        "- `REJECTED`인 CKRD2420은 24~280 VAC 출력 SSR이므로 24 VDC heater driver로 쓰지 않는다.",
        "",
        "가격·재고는 변동 가능하며 주문 직전에 재조회한다. 사용자 승인 없이 장바구니·주문·견적 발주를 수행하지 않는다.",
    ])
    (ROOT / "bom" / "procurement_candidates.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(f"PROCUREMENT_ROUTES_OK buy_rows={len(buy_rows)} evidence_parts={len(evidence_ids & buy_ids)}")


if __name__ == "__main__":
    main()
