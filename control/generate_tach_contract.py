#!/usr/bin/env python3
"""Generate the AVR tach constants from the machine-readable tach contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "control" / "tach_contract.json"
TARGET = ROOT / "firmware" / "arduino_mega" / "src" / "tach_contract_generated.h"


def f(value: float) -> str:
    rendered = f"{value:.6g}"
    if "." not in rendered and "e" not in rendered.lower():
        rendered += ".0"
    return rendered + "f"


def render(contract: dict) -> str:
    channels = contract["channels"]
    enum_values = ", ".join(channel["channel"].upper() for channel in channels)
    lines = [
        "#pragma once",
        "// Generated from control/tach_contract.json. Do not hand-edit channel values.",
        "",
        "#include <stdint.h>",
        "",
        '#include "tach_estimator.h"',
        "",
        f"enum class TachChannel : uint8_t {{ {enum_values} }};",
        "",
    ]
    for channel in channels:
        name = channel["channel"].upper()
        lines.extend(
            [
                f"constexpr TachEstimatorConfig {name}_TACH_CONFIG{{",
                f"    {channel['ppr']}, {f(channel['expected_min_rpm'])}, "
                f"{f(channel['expected_max_rpm'])}, {f(channel['period_count_crossover_rpm'])}, "
                f"{channel['count_window_us']}UL, {channel['count_min_intervals']}, "
                f"{channel['timeout_us']}UL, {channel['minimum_pulse_spacing_us']}UL,",
                f"    {channel['filter_time_constant_us']}UL, "
                f"{f(channel['maximum_plausible_acceleration_rpm_s'])}, "
                f"{f(channel['outlier_relative_tolerance'])}}};",
            ]
        )
    lines.extend(["", "inline const TachEstimatorConfig &tachConfig(TachChannel channel) {", "  switch (channel) {"])
    for channel in channels:
        name = channel["channel"].upper()
        lines.append(f"    case TachChannel::{name}: return {name}_TACH_CONFIG;")
    lines.extend(["  }", "  return SHREDDER_TACH_CONFIG;", "}", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(json.loads(SOURCE.read_text(encoding="utf-8")))
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != expected:
            print(f"STALE {TARGET.relative_to(ROOT)}")
            return 1
        print("TACH_CONTRACT_SYNC_OK")
        return 0
    TARGET.write_text(expected, encoding="utf-8")
    print(TARGET.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
