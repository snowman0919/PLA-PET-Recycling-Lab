#!/usr/bin/env python3
"""Generate the PPR safety-monitor/interface KiCad 9 project.

The generated board is deliberately outside the safety chain.  It monitors
isolated auxiliary contacts and makes reset-safe logic drive signals available
to qualified external driver modules.  It does not switch hazardous energy.

Authoring dependency: kiutils==1.4.8.  Electrical acceptance uses kicad-cli,
not the authoring library.
"""

from __future__ import annotations

import argparse
import copy
import heapq
import json
import math
import re
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from kiutils.board import Board
from kiutils.footprint import Footprint
from kiutils.items.brditems import Segment, Via
from kiutils.items.common import Effects, Font, Net, PageSettings, Position, Property, TitleBlock
from kiutils.items.gritems import GrLine, GrText
from kiutils.items.zones import FillSettings, Hatch, Zone, ZonePolygon
from kiutils.items.schitems import GlobalLabel, SchematicSymbol, SymbolProjectInstance, SymbolProjectPath, Text
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PROJECT = "ppr_interface"
SHEET_NS = uuid.UUID("351d67c4-9b6c-5a6d-8bf8-9bb850ec8bf1")
SHEET_UUID = str(uuid.uuid5(SHEET_NS, "root-sheet"))

SYMBOL_ROOT = Path("/usr/share/kicad/symbols")
FOOTPRINT_ROOT = Path("/usr/share/kicad/footprints")
BOARD_WIDTH = 190.0
BOARD_HEIGHT = 130.0
ROUTE_GRID = 0.635

INPUT_CHANNELS = (
    "E_STOP_AUX",
    "CONTACTOR_FB",
    "LID_AUX",
    "SERVICE_AUX",
    "THERMAL_AUX",
    "PRESSURE_AUX",
    "AIRFLOW_AUX",
    "FORMING_GUARD_AUX",
)
OUTPUT_CHANNELS = (
    "HEATER_EXT_Z1",
    "HEATER_EXT_Z2",
    "HEATER_EXT_Z3",
    "HEATER_EXT_DIE",
    "DRYER_PLA",
    "DRYER_PET",
    "CONTACTOR_REQUEST",
    "SHREDDER_ENABLE",
)


def stable_uuid(kind: str, name: str) -> str:
    return str(uuid.uuid5(SHEET_NS, f"{kind}:{name}"))


@dataclass(frozen=True)
class LibPart:
    library: str
    name: str
    parent: str | None = None


@dataclass
class Component:
    ref: str
    part: LibPart
    value: str
    footprint: str
    x: float
    y: float
    angle: float = 0.0
    nets: dict[str, str] = field(default_factory=dict)
    datasheet: str = "~"
    manufacturer: str = "TBD"
    mpn: str = "TBD"
    sourcing: str = "BUY"
    comments: str = ""
    in_bom: bool = True
    on_board: bool = True


R = LibPart("Device", "R")
D = LibPart("Device", "D")
C = LibPart("Device", "C")
OPTO = LibPart("Isolator", "LTV-817S")
# The upstream 74AHCT541 symbol inherits the complete pin geometry from
# 74LS541.  Self-contained schematic embedding of inherited symbols is not
# accepted by KiCad CLI 9.0.9, so use the concrete, pin-identical family symbol
# and keep the exact SN74AHCT541N MPN/value/datasheet on the instance.
BUFFER = LibPart("74xx", "74LS541")
CONN_1X10 = LibPart("Connector_Generic", "Conn_01x10")
CONN_2X08 = LibPart("Connector_Generic", "Conn_02x08_Odd_Even")
CONN_2X10 = LibPart("Connector_Generic", "Conn_02x10_Odd_Even")
PWR_FLAG = LibPart("power", "PWR_FLAG")
TEST_POINT = LibPart("Connector", "TestPoint")


def components() -> list[Component]:
    items: list[Component] = []

    # Field connector: odd pins are a replicated 24 V sense source; even pins
    # return through one external dry contact per channel.
    field_nets: dict[str, str] = {}
    for index, channel in enumerate(INPUT_CHANNELS, start=1):
        field_nets[str(2 * index - 1)] = "+24V_SENSE"
        field_nets[str(2 * index)] = f"FIELD_{channel}"
    field_nets.update({"17": "+24V_SENSE", "18": "+24V_SENSE", "19": "FIELD_0V", "20": "FIELD_0V"})
    items.append(
        Component(
            "J1",
            CONN_2X10,
            "FIELD_DRY_CONTACTS",
            "Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical",
            25,
            125,
            nets=field_nets,
            comments="TBD keyed field connector; one +24V/return pair per dry contact",
        )
    )
    items.extend(
        (
            Component(
                "#FLG01",
                PWR_FLAG,
                "PWR_FLAG",
                "",
                238,
                125,
                nets={"1": "+5V"},
                sourcing="DNP",
                comments="ERC declaration: external regulated +5V source",
                in_bom=False,
                on_board=False,
            ),
            Component(
                "#FLG02",
                PWR_FLAG,
                "PWR_FLAG",
                "",
                238,
                137,
                nets={"1": "GND"},
                sourcing="DNP",
                comments="ERC declaration: external logic return",
                in_bom=False,
                on_board=False,
            ),
            Component(
                "#FLG03",
                PWR_FLAG,
                "PWR_FLAG",
                "",
                238,
                149,
                nets={"1": "+24V_SENSE"},
                sourcing="DNP",
                comments="ERC declaration: external protected +24V sense source",
                in_bom=False,
                on_board=False,
            ),
        )
    )

    # Eight identical monitor-only optocoupler channels.  A reverse diode
    # protects each optocoupler LED against field wiring polarity mistakes.
    for index, channel in enumerate(INPUT_CHANNELS, start=1):
        y = 28 + (index - 1) * 27
        led_a = f"LED_{channel}_A"
        led_k = "FIELD_0V"
        diag = f"DIAG_{channel}"
        items.extend(
            (
                Component(
                    f"R{index}",
                    R,
                    "4.7k 1%",
                    "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                    72,
                    y,
                    angle=90,
                    nets={"1": f"FIELD_{channel}", "2": led_a},
                    comments="24V sense LED current limit; recalc after connector/source tolerance is known",
                ),
                Component(
                    f"D{index}",
                    D,
                    "1N4148-TAP",
                    "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
                    112,
                    y + 9,
                    nets={"1": led_a, "2": led_k},
                    manufacturer="Vishay",
                    mpn="1N4148-TAP",
                    datasheet="https://www.vishay.com/docs/81857/1n4148.pdf",
                    comments="Antiparallel LED reverse-voltage clamp",
                ),
                Component(
                    f"U{index}",
                    OPTO,
                    "LTV-817S-TA1",
                    "Package_DIP:SMDIP-4_W9.53mm",
                    132,
                    y,
                    nets={"1": led_a, "2": led_k, "4": diag, "3": "GND"},
                    manufacturer="Lite-On",
                    mpn="LTV-817S-TA1",
                    datasheet="https://optoelectronics.liteon.com/upload/download/DS-70-96-0016/LTV-8X7%20series%20RevQ.PDF",
                    comments="Diagnostic isolation only; no functional-safety credit",
                ),
                Component(
                    f"R{8 + index}",
                    R,
                    "10k 1%",
                    "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                    172,
                    y,
                    angle=90,
                    nets={"1": "+5V", "2": diag},
                    comments="Logic-side optocoupler pull-up; healthy closed contact reads LOW",
                ),
            )
        )

    # Logic diagnostic connector: isolated diagnostic inputs plus rails.
    diag_nets = {str(i): f"DIAG_{name}" for i, name in enumerate(INPUT_CHANNELS, start=1)}
    diag_nets.update({"9": "+5V", "10": "GND"})
    items.append(
        Component(
            "J2",
            CONN_1X10,
            "MEGA_DIAGNOSTICS",
            "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical",
            218,
            125,
            nets=diag_nets,
            comments="To Mega D22-D29; cable pinout is controlled by mega_pinout.csv",
        )
    )

    # MCU command connector, input pull-downs, non-inverting buffer, series
    # resistors, output pull-downs, and external-driver connector.
    cmd_nets = {str(i): f"CMD_{name}" for i, name in enumerate(OUTPUT_CHANNELS, start=1)}
    cmd_nets.update({"9": "+5V", "10": "GND"})
    items.append(
        Component(
            "J3",
            CONN_1X10,
            "MEGA_COMMANDS",
            "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical",
            252,
            58,
            nets=cmd_nets,
            comments="Default-OFF command input cable from Mega",
        )
    )

    buffer_nets = {"1": "GND", "19": "GND", "20": "+5V", "10": "GND"}
    input_pins = ("2", "3", "4", "5", "6", "7", "8", "9")
    output_pins = ("18", "17", "16", "15", "14", "13", "12", "11")
    for index, channel in enumerate(OUTPUT_CHANNELS):
        buffer_nets[input_pins[index]] = f"CMD_{channel}"
        buffer_nets[output_pins[index]] = f"BUF_{channel}"
        y = 28 + index * 11
        items.extend(
            (
                Component(
                    f"R{17 + index}",
                    R,
                    "47k 1%",
                    "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                    287,
                    y,
                    angle=90,
                    nets={"1": f"CMD_{channel}", "2": "GND"},
                    comments="Disconnected/reset MCU command defaults LOW",
                ),
                Component(
                    f"R{25 + index}",
                    R,
                    "100R 1%",
                    "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                    347,
                    y,
                    angle=90,
                    nets={"1": f"BUF_{channel}", "2": f"OUT_{channel}"},
                    comments="Logic-output edge/current limiting; not a power-driver resistor",
                ),
                Component(
                    f"R{33 + index}",
                    R,
                    "47k 1%",
                    "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
                    378,
                    y,
                    angle=90,
                    nets={"1": f"OUT_{channel}", "2": "GND"},
                    comments="External-driver command remains LOW when this board is unpowered",
                ),
            )
        )

    items.append(
        Component(
            "U9",
            BUFFER,
            "SN74AHCT541N",
            "Package_DIP:DIP-20_W7.62mm_LongPads",
            317,
            73,
            nets=buffer_nets,
            manufacturer="Texas Instruments",
            mpn="SN74AHCT541N",
            datasheet="https://www.ti.com/lit/ds/symlink/sn74ahct541.pdf",
            comments="5V TTL-compatible non-inverting buffer; both active-low OE pins tied LOW",
        )
    )
    items.append(
        Component(
            "C1",
            C,
            "100n X7R",
            "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm",
            317,
            118,
            nets={"1": "+5V", "2": "GND"},
            comments="Local U9 bypass; dielectric/voltage rating TBD before release",
        )
    )
    out_nets = {str(i): f"OUT_{name}" for i, name in enumerate(OUTPUT_CHANNELS, start=1)}
    out_nets.update({"9": "+5V", "10": "GND"})
    items.append(
        Component(
            "J4",
            CONN_1X10,
            "EXTERNAL_DRIVER_COMMANDS",
            "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical",
            410,
            58,
            nets=out_nets,
            comments="Logic only; qualified external default-off heater/motor/contactor interfaces required",
        )
    )
    test_nets = ("+24V_SENSE", "FIELD_0V", "+5V", "GND") + tuple(
        f"DIAG_{name}" for name in INPUT_CHANNELS
    )
    for index, net in enumerate(test_nets, start=1):
        items.append(
            Component(
                f"TP{index}",
                TEST_POINT,
                net,
                "TestPoint:TestPoint_THTPad_D3.0mm_Drill1.5mm",
                245 + ((index - 1) % 6) * 22,
                174 + ((index - 1) // 6) * 18,
                nets={"1": net},
                sourcing="PCB_FEATURE",
                comments="Bare plated commissioning/service probe point; do not use as a field connector",
                in_bom=False,
            )
        )

    # All connection points stay on KiCad's 50 mil grid.  This also makes the
    # generated schematic easy to edit manually after generation.
    for item in items:
        item.x = round(item.x / 1.27) * 1.27
        item.y = round(item.y / 1.27) * 1.27
    return items


class SymbolCache:
    def __init__(self) -> None:
        self._libraries: dict[str, SymbolLib] = {}
        self._symbols: dict[tuple[str, str], object] = {}

    def get(self, part: LibPart):
        key = (part.library, part.name)
        if key not in self._symbols:
            lib = self._libraries.setdefault(
                part.library,
                SymbolLib.from_file(str(SYMBOL_ROOT / f"{part.library}.kicad_sym")),
            )
            self._symbols[key] = next(s for s in lib.symbols if s.entryName == part.name)
        return self._symbols[key]

    def pins(self, part: LibPart):
        source = self.get(LibPart(part.library, part.parent)) if part.parent else self.get(part)
        result = {}
        for unit in source.units:
            for pin in unit.pins:
                result[str(pin.number)] = pin
        return result


def rotate_point(x: float, y: float, angle: float) -> tuple[float, float]:
    # Library coordinates use +Y upward while the schematic canvas uses +Y
    # downward.  KiCad symbol rotation is clockwise in canvas coordinates.
    normalized = int(angle) % 360
    if normalized == 0:
        return x, -y
    if normalized == 90:
        return -y, -x
    if normalized == 180:
        return -x, y
    if normalized == 270:
        return y, x
    raise ValueError(f"unsupported symbol angle: {angle}")


def hidden_effects() -> Effects:
    return Effects(font=Font(height=1.27, width=1.27), hide=True)


def visible_effects(size: float = 1.27) -> Effects:
    return Effects(font=Font(height=size, width=size))


def make_schematic() -> Schematic:
    cache = SymbolCache()
    schematic = Schematic.create_new()
    # kiutils 1.4.8 serializes the stable KiCad 8 schema.  KiCad 9 imports
    # this schema natively and then remains the final parser/ERC authority.
    schematic.version = "20231120"
    schematic.generator = "ppr_interface_generator"
    schematic.uuid = SHEET_UUID
    schematic.paper = PageSettings(paperSize="A3")
    schematic.titleBlock = TitleBlock(
        title="PPR isolated monitor and default-OFF logic interface",
        date="2026-08-28",
        revision="A-DRAFT",
        company="PPR — CERN-OHL-P-2.0",
        comments={
            1: "MONITOR ONLY / NO SAFETY CREDIT / NOT FOR FABRICATION",
            2: "24 V hazardous-energy switching remains off-board in qualified hardware",
        },
    )

    parts = components()
    embedded: list[object] = []
    embedded_keys: set[tuple[str, str]] = set()
    for component in parts:
        # Preserve upstream inheritance exactly.  The parent is embedded before
        # a derived symbol so KiCad can resolve ``extends`` without a project
        # library and can compare the copy against its installed library.
        for name in filter(None, (component.part.parent, component.part.name)):
            key = (component.part.library, str(name))
            if key not in embedded_keys:
                symbol = copy.deepcopy(cache.get(LibPart(*key)))
                symbol.entryName = f"{component.part.library}:{name}"
                embedded.append(symbol)
                embedded_keys.add(key)
    schematic.libSymbols = embedded

    for component in parts:
        pin_defs = cache.pins(component.part)
        missing = sorted(set(component.nets) - set(pin_defs))
        if missing:
            raise ValueError(f"{component.ref}: unknown pins {missing}")
        props = [
            Property("Reference", component.ref, position=Position(component.x, component.y - 5.5, 0), effects=visible_effects()),
            Property("Value", component.value, position=Position(component.x, component.y + 5.5, 0), effects=visible_effects()),
            Property("Footprint", component.footprint, position=Position(component.x, component.y, 0), effects=hidden_effects()),
            Property("Datasheet", component.datasheet, position=Position(component.x, component.y, 0), effects=hidden_effects()),
            Property("Description", component.comments, position=Position(component.x, component.y, 0), effects=hidden_effects()),
            Property("Manufacturer", component.manufacturer, position=Position(component.x, component.y, 0), effects=hidden_effects()),
            Property("MPN", component.mpn, position=Position(component.x, component.y, 0), effects=hidden_effects()),
            Property("Sourcing", component.sourcing, position=Position(component.x, component.y, 0), effects=hidden_effects()),
            Property("BOM_Comments", component.comments, position=Position(component.x, component.y, 0), effects=hidden_effects()),
        ]
        symbol = SchematicSymbol(
            libraryNickname=component.part.library,
            entryName=component.part.name,
            position=Position(component.x, component.y, component.angle),
            unit=1,
            inBom=component.in_bom,
            onBoard=component.on_board,
            fieldsAutoplaced=False,
            uuid=stable_uuid("symbol", component.ref),
            properties=props,
            pins={pin: stable_uuid("pin", f"{component.ref}:{pin}") for pin in pin_defs},
            instances=[
                SymbolProjectInstance(
                    name=PROJECT,
                    paths=[SymbolProjectPath(f"/{SHEET_UUID}", component.ref, 1)],
                )
            ],
        )
        schematic.schematicSymbols.append(symbol)

        for pin_number, net in component.nets.items():
            pin = pin_defs[pin_number]
            dx, dy = rotate_point(pin.position.X, pin.position.Y, component.angle)
            shape = "bidirectional"
            if component.ref == "J3" and net.startswith("CMD_"):
                shape = "output"
            elif component.ref == "U9" and net.startswith("CMD_"):
                shape = "input"
            elif component.ref == "U9" and net.startswith("BUF_"):
                shape = "output"
            schematic.globalLabels.append(
                GlobalLabel(
                    text=net,
                    shape=shape,
                    position=Position(component.x + dx, component.y + dy, 0),
                    effects=Effects(font=Font(height=0.9, width=0.9), hide=True),
                    uuid=stable_uuid("label", f"{component.ref}:{pin_number}:{net}"),
                )
            )

    schematic.texts.extend(
        (
            Text(
                "MONITOR ONLY — NO SAFETY CREDIT — NOT FOR FABRICATION",
                Position(215, 12, 0),
                Effects(font=Font(height=2.5, width=2.5, bold=True)),
                stable_uuid("text", "warning"),
            ),
            Text(
                "E-stop, contactor, branch fuses, independent thermal cutoffs and all high-current drivers are external qualified hardware.",
                Position(215, 18, 0),
                visible_effects(1.2),
                stable_uuid("text", "boundary"),
            ),
            Text(
                "FIELD SIDE: dry-contact diagnostic isolation only",
                Position(102, 258, 0),
                visible_effects(1.5),
                stable_uuid("text", "field"),
            ),
            Text(
                "LOGIC SIDE: default-OFF command conditioning only",
                Position(330, 138, 0),
                visible_effects(1.5),
                stable_uuid("text", "logic"),
            ),
        )
    )
    return schematic


def make_project_file() -> dict:
    field_nets = ["+24V_SENSE", "FIELD_0V"]
    field_nets += [f"FIELD_{name}" for name in INPUT_CHANNELS]
    field_nets += [f"LED_{name}_A" for name in INPUT_CHANNELS]
    return {
        "board": {
            "3dviewports": [],
            "design_settings": {
                "drc_exclusions": [],
                "meta": {"version": 2},
                # kiutils normalizes KiCad 9 footprint field formatting while
                # preserving copper/pads/courtyard geometry.  This known
                # authoring-only delta is checked in the review and is not an
                # electrical/DFM violation.
                "rule_severities": {"lib_footprint_mismatch": "ignore"},
            },
        },
        "boards": [],
        "cvpcb": {},
        "erc": {},
        "libraries": {},
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1},
        "net_settings": {
            "classes": [
                {
                    "bus_width": 12,
                    "clearance": 0.25,
                    "diff_pair_gap": 0.25,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.25,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "Default",
                    "pcb_color": "rgba(0, 0, 0, 0.000)",
                    "schematic_color": "rgba(0, 0, 0, 0.000)",
                    "track_width": 0.25,
                    "via_diameter": 0.8,
                    "via_drill": 0.4,
                    "wire_width": 6,
                },
                {
                    "bus_width": 12,
                    "clearance": 0.5,
                    "diff_pair_gap": 0.25,
                    "diff_pair_via_gap": 0.25,
                    "diff_pair_width": 0.25,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "name": "FIELD_24V",
                    "pcb_color": "rgba(255, 120, 0, 1.000)",
                    "schematic_color": "rgba(255, 120, 0, 1.000)",
                    "track_width": 0.5,
                    "via_diameter": 1.0,
                    "via_drill": 0.5,
                    "wire_width": 6,
                },
            ],
            "meta": {"version": 4},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": [{"netclass": "FIELD_24V", "pattern": net} for net in field_nets],
        },
        "pcbnew": {},
        "schematic": {},
        "sheets": [],
        "text_variables": {},
    }


def board_positions() -> dict[str, tuple[float, float, float]]:
    result: dict[str, tuple[float, float, float]] = {
        "J1": (7.62, 45.72, 0),
        "J2": (91.44, 43.18, 0),
        "J3": (109.22, 12.70, 0),
        "U9": (134.62, 35.56, 0),
        # Place the bypass directly beside U9 pins 20 (+5V) and 19 (GND).
        "C1": (145.415, 35.56, 270),
        "J4": (182.88, 12.70, 0),
    }
    for index in range(8):
        y = 10.16 + index * 13.335
        result[f"R{index + 1}"] = (27.94, y, 0)
        result[f"D{index + 1}"] = (42.545, y, 0)
        result[f"U{index + 1}"] = (59.3725, y, 0)
        result[f"R{index + 9}"] = (70.485, y, 0)
        result[f"R{index + 17}"] = (116.84, 10.16 + index * 12.065, 0)
        result[f"R{index + 25}"] = (148.59, 10.16 + index * 12.065, 0)
        result[f"R{index + 33}"] = (163.83, 10.16 + index * 12.065, 0)
    test_positions = [
        (15.24, 116.84),
        (30.48, 116.84),
        (70.485, 116.84),
        (80.645, 116.84),
    ] + [(91.44 + index * 10.16, 116.84) for index in range(8)]
    for index, (x, y) in enumerate(test_positions, start=1):
        result[f"TP{index}"] = (x, y, 0)
    return result


def footprint_file(lib_id: str) -> Path:
    library, name = lib_id.split(":", 1)
    return FOOTPRINT_ROOT / f"{library}.pretty" / f"{name}.kicad_mod"


def transform_local(position: Position, local: Position) -> tuple[float, float]:
    angle = int(position.angle or 0) % 360
    x, y = local.X, local.Y
    if angle == 0:
        dx, dy = x, y
    elif angle == 90:
        dx, dy = y, -x
    elif angle == 180:
        dx, dy = -x, -y
    elif angle == 270:
        dx, dy = -y, x
    else:
        raise ValueError(f"unsupported footprint angle: {angle}")
    return position.X + dx, position.Y + dy


def grid_point(x: float, y: float) -> tuple[int, int]:
    return round(x / ROUTE_GRID), round(y / ROUTE_GRID)


def mm_point(point: tuple[int, int]) -> Position:
    return Position(point[0] * ROUTE_GRID, point[1] * ROUTE_GRID)


def route_board(board: Board, field_net_numbers: set[int]) -> None:
    """Route the placed board with a deterministic two-layer orthogonal A*.

    Pads and existing tracks are treated as clearance obstacles.  The two
    voltage domains are also confined to opposite sides of the optocoupler
    barrier, making the 6 mm domain rule an input to routing rather than merely
    a post-layout check.
    """

    pad_nodes: dict[int, list[tuple[tuple[int, int], set[int]]]] = {}
    blocked: list[dict[tuple[int, int], set[int]]] = [dict(), dict()]
    plated_pad_nodes: set[tuple[int, int]] = set()
    smd_via_forbidden: set[tuple[int, int]] = set()
    min_x = math.ceil(1.5 / ROUTE_GRID)
    min_y = min_x
    max_x = math.floor((BOARD_WIDTH - 1.5) / ROUTE_GRID)
    max_y = math.floor((BOARD_HEIGHT - 1.5) / ROUTE_GRID)

    for fp in board.footprints:
        if fp.position is None:
            continue
        for pad in fp.pads:
            if not pad.net or pad.net.number == 0:
                continue
            px, py = transform_local(fp.position, pad.position)
            node = grid_point(px, py)
            layers = {0, 1} if "*.Cu" in pad.layers else ({0} if "F.Cu" in pad.layers else {1})
            if "*.Cu" in pad.layers:
                plated_pad_nodes.add(node)
            else:
                # A layer transition creates a 0.8 mm via.  Reserve the full
                # SMD pad radius plus the via radius, not merely the pad centre;
                # otherwise an orthogonal route can place a via just inside a
                # gull-wing pad while still passing KiCad's connectivity DRC.
                via_keepout = math.ceil((max(pad.size.X, pad.size.Y) / 2 + 0.40) / ROUTE_GRID)
                for dx in range(-via_keepout, via_keepout + 1):
                    for dy in range(-via_keepout, via_keepout + 1):
                        if dx * dx + dy * dy <= via_keepout * via_keepout:
                            smd_via_forbidden.add((node[0] + dx, node[1] + dy))
            pad_nodes.setdefault(pad.net.number, []).append((node, layers))
            radius_mm = max(pad.size.X, pad.size.Y) / 2 + 0.40
            radius = max(1, math.ceil(radius_mm / ROUTE_GRID))
            for layer in layers:
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if dx * dx + dy * dy <= radius * radius:
                            blocked[layer].setdefault((node[0] + dx, node[1] + dy), set()).add(pad.net.number)

    occupied: list[dict[tuple[int, int], int]] = [dict(), dict()]
    net_by_number = {net.number: net for net in board.nets}

    def domain_allowed(net_number: int, point: tuple[int, int]) -> bool:
        x_mm = point[0] * ROUTE_GRID
        if net_number in field_net_numbers:
            return x_mm <= 56.515
        return x_mm >= 62.865

    def usable(net_number: int, layer: int, point: tuple[int, int]) -> bool:
        x, y = point
        if not (min_x <= x <= max_x and min_y <= y <= max_y):
            return False
        if not domain_allowed(net_number, point):
            return False
        owners = blocked[layer].get(point, set())
        if owners - {net_number}:
            return False
        owner = occupied[layer].get(point)
        return owner in (None, net_number)

    def heuristic(point: tuple[int, int, int], goals: set[tuple[int, int, int]]) -> int:
        x, y, layer = point
        return min(abs(x - gx) + abs(y - gy) + (8 if layer != gl else 0) for gx, gy, gl in goals)

    def astar(net_number: int, starts: set[tuple[int, int, int]], goals: set[tuple[int, int, int]]):
        queue: list[tuple[int, int, tuple[int, int, int]]] = []
        came_from: dict[tuple[int, int, int], tuple[int, int, int] | None] = {}
        cost: dict[tuple[int, int, int], int] = {}
        serial = 0
        for start in sorted(starts):
            if usable(net_number, start[2], (start[0], start[1])):
                cost[start] = 0
                came_from[start] = None
                heapq.heappush(queue, (heuristic(start, goals), serial, start))
                serial += 1
        while queue:
            _, _, current = heapq.heappop(queue)
            if current in goals:
                path = [current]
                while came_from[current] is not None:
                    current = came_from[current]  # type: ignore[assignment]
                    path.append(current)
                return list(reversed(path))
            x, y, layer = current
            neighbors = [
                (x + 1, y, layer, 1),
                (x - 1, y, layer, 1),
                (x, y + 1, layer, 1),
                (x, y - 1, layer, 1),
            ]
            if (x, y) not in smd_via_forbidden:
                neighbors.append((x, y, 1 - layer, 14))
            for nx, ny, nl, step in neighbors:
                node = (nx, ny, nl)
                if not usable(net_number, nl, (nx, ny)):
                    continue
                new_cost = cost[current] + step
                if new_cost < cost.get(node, 1_000_000_000):
                    cost[node] = new_cost
                    came_from[node] = current
                    heapq.heappush(queue, (new_cost + heuristic(node, goals), serial, node))
                    serial += 1
        return None

    def occupy(net_number: int, layer: int, point: tuple[int, int], radius: int | None = None) -> None:
        if radius is None:
            radius = 1
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                occupied[layer].setdefault((point[0] + dx, point[1] + dy), net_number)

    # Route short local nets before shared rails.  This prevents a long ground
    # trunk from boxing in the adjacent diode/opto pad pairs; two layers leave
    # the later high-fanout rails ample room to go around those local routes.
    order = sorted(pad_nodes, key=lambda n: (len(pad_nodes[n]), net_by_number[n].name))
    for net_number in order:
        pads = pad_nodes[net_number]
        if len(pads) < 2:
            continue
        root_point, root_layers = pads[0]
        tree = {(root_point[0], root_point[1], layer) for layer in root_layers}
        for layer in root_layers:
            occupy(net_number, layer, root_point, 0)
        paths: list[list[tuple[int, int, int]]] = []
        remaining = pads[1:]
        # Nearest-first reduces detours and produces compact rail trees.
        remaining.sort(key=lambda item: abs(item[0][0] - root_point[0]) + abs(item[0][1] - root_point[1]))
        for point, layers in remaining:
            starts = {(point[0], point[1], layer) for layer in layers}
            path = astar(net_number, starts, tree)
            if path is None:
                raise RuntimeError(f"autorouter failed on {net_by_number[net_number].name} at {point}")
            paths.append(path)
            tree.update(path)
            for x, y, layer in path:
                occupy(net_number, layer, (x, y))

        width = 0.5 if net_number in field_net_numbers else 0.25
        for path_index, path in enumerate(paths):
            for index in range(1, len(path)):
                if path[index - 1][2] != path[index][2]:
                    point = path[index - 1][:2]
                    if point not in plated_pad_nodes:
                        board.traceItems.append(
                            Via(
                                position=mm_point(point),
                                size=0.8,
                                drill=0.4,
                                layers=["F.Cu", "B.Cu"],
                                net=net_number,
                                tstamp=stable_uuid("via", f"{net_number}:{path_index}:{index}"),
                            )
                        )

            # Split at layer transitions, then compress collinear grid steps.
            run_start = 0
            runs: list[list[tuple[int, int, int]]] = []
            for index in range(1, len(path)):
                if path[index][2] != path[index - 1][2]:
                    runs.append(path[run_start:index])
                    run_start = index
            runs.append(path[run_start:])
            for run_index, run in enumerate(runs):
                if len(run) < 2:
                    continue
                start = 0
                for index in range(1, len(run) + 1):
                    turn = index == len(run)
                    if 1 <= index < len(run) and index >= 2:
                        px, py, _ = run[index - 2]
                        ax, ay, _ = run[index - 1]
                        bx, by, _ = run[index]
                        turn = (ax - px, ay - py) != (bx - ax, by - ay)
                    if turn:
                        a = run[start]
                        b = run[index - 1]
                        if a[:2] != b[:2]:
                            board.traceItems.append(
                                Segment(
                                    start=mm_point(a[:2]),
                                    end=mm_point(b[:2]),
                                    width=width,
                                    layer="F.Cu" if a[2] == 0 else "B.Cu",
                                    net=net_number,
                                    tstamp=stable_uuid(
                                        "segment",
                                        f"{net_number}:{path_index}:{run_index}:{start}:{index}",
                                    ),
                                )
                            )
                        start = index - 1


def make_board() -> Board:
    part_list = [part for part in components() if part.on_board]
    placements = board_positions()
    missing = sorted({part.ref for part in part_list} - set(placements))
    if missing:
        raise ValueError(f"missing PCB placements: {missing}")

    net_names = sorted({net for part in part_list for net in part.nets.values()})
    nets = [Net(0, "")] + [Net(index, name) for index, name in enumerate(net_names, start=1)]
    net_by_name = {net.name: net for net in nets}

    board = Board.create_new()
    board.version = "20241229"
    board.generator = "ppr_interface_generator"
    board.titleBlock = TitleBlock(
        title="PPR isolated monitor and default-OFF logic interface",
        date="2026-08-28",
        revision="A-DRAFT",
        company="PPR — CERN-OHL-P-2.0",
        comments={1: "MONITOR ONLY / NO SAFETY CREDIT / NOT FOR FABRICATION"},
    )
    board.nets = nets

    for part in part_list:
        fp = Footprint.from_file(str(footprint_file(part.footprint)))
        fp.libraryNickname, fp.entryName = part.footprint.split(":", 1)
        x, y, angle = placements[part.ref]
        fp.position = Position(x, y, angle)
        fp.tstamp = stable_uuid("footprint", part.ref)
        fp.path = f"/{SHEET_UUID}/{stable_uuid('symbol', part.ref)}"
        fp.properties["Reference"] = part.ref
        fp.properties["Value"] = part.value
        fp.properties["MPN"] = part.mpn
        fp.properties["Manufacturer"] = part.manufacturer
        fp.properties["Sourcing"] = part.sourcing
        fp.properties["BOM_Comments"] = part.comments
        for pad in fp.pads:
            pad.tstamp = stable_uuid("pad", f"{part.ref}:{pad.number}")
            if str(pad.number) in part.nets:
                pad.net = net_by_name[part.nets[str(pad.number)]]
        board.footprints.append(fp)

    # Four unplated M3 mounting holes are mechanical-only and intentionally
    # absent from the schematic BOM.
    for index, (x, y) in enumerate(
        ((5, 5), (BOARD_WIDTH - 5, 5), (5, BOARD_HEIGHT - 5), (BOARD_WIDTH - 5, BOARD_HEIGHT - 5)),
        start=1,
    ):
        fp = Footprint.from_file(
            str(FOOTPRINT_ROOT / "MountingHole.pretty" / "MountingHole_3.2mm_M3.kicad_mod")
        )
        fp.libraryNickname = "MountingHole"
        fp.entryName = "MountingHole_3.2mm_M3"
        fp.position = Position(x, y, 0)
        fp.tstamp = stable_uuid("footprint", f"H{index}")
        fp.properties["Reference"] = f"H{index}"
        fp.properties["Value"] = "M3_NPTH"
        for pad in fp.pads:
            pad.tstamp = stable_uuid("pad", f"H{index}:{pad.number}")
        board.footprints.append(fp)

    for index, (x, y) in enumerate(((15, 5), (175, 5), (175, BOARD_HEIGHT - 5)), start=1):
        fp = Footprint.from_file(
            str(FOOTPRINT_ROOT / "Fiducial.pretty" / "Fiducial_1mm_Mask2mm.kicad_mod")
        )
        fp.libraryNickname = "Fiducial"
        fp.entryName = "Fiducial_1mm_Mask2mm"
        fp.position = Position(x, y, 0)
        fp.tstamp = stable_uuid("footprint", f"FID{index}")
        fp.properties["Reference"] = f"FID{index}"
        fp.properties["Value"] = "FIDUCIAL_1MM"
        for pad in fp.pads:
            pad.tstamp = stable_uuid("pad", f"FID{index}:{pad.number}")
        board.footprints.append(fp)

    board.graphicItems.extend(
        [
            GrLine(Position(0, 0), Position(BOARD_WIDTH, 0), layer="Edge.Cuts", width=0.1, tstamp=stable_uuid("edge", "top")),
            GrLine(Position(BOARD_WIDTH, 0), Position(BOARD_WIDTH, BOARD_HEIGHT), layer="Edge.Cuts", width=0.1, tstamp=stable_uuid("edge", "right")),
            GrLine(Position(BOARD_WIDTH, BOARD_HEIGHT), Position(0, BOARD_HEIGHT), layer="Edge.Cuts", width=0.1, tstamp=stable_uuid("edge", "bottom")),
            GrLine(Position(0, BOARD_HEIGHT), Position(0, 0), layer="Edge.Cuts", width=0.1, tstamp=stable_uuid("edge", "left")),
            GrLine(Position(56.515, 3), Position(56.515, BOARD_HEIGHT - 3), layer="Dwgs.User", width=0.4, tstamp=stable_uuid("drawing", "barrier-left")),
            GrLine(Position(62.865, 3), Position(62.865, BOARD_HEIGHT - 3), layer="Dwgs.User", width=0.4, tstamp=stable_uuid("drawing", "barrier-right")),
            GrText(
                "MONITOR ONLY / NO SAFETY CREDIT",
                position=Position(125, BOARD_HEIGHT - 4, 0),
                layer="F.SilkS",
                effects=Effects(font=Font(height=2.0, width=2.0, thickness=0.35)),
                tstamp=stable_uuid("text", "pcb-warning"),
            ),
            GrText(
                "FIELD 24V",
                position=Position(25, 3.5, 0),
                layer="F.SilkS",
                effects=visible_effects(1.5),
                tstamp=stable_uuid("text", "pcb-field"),
            ),
            GrText(
                "6.35mm COPPER BARRIER",
                position=Position(59.69, 110, 90),
                layer="Dwgs.User",
                effects=visible_effects(1.0),
                tstamp=stable_uuid("text", "pcb-barrier"),
            ),
            GrText(
                "5V LOGIC — EXTERNAL DRIVERS REQUIRED",
                position=Position(126, 3.5, 0),
                layer="F.SilkS",
                effects=visible_effects(1.3),
                tstamp=stable_uuid("text", "pcb-logic"),
            ),
        ]
    )
    field_net_names = {"+24V_SENSE", "FIELD_0V"}
    field_net_names.update(f"FIELD_{name}" for name in INPUT_CHANNELS)
    field_net_names.update(f"LED_{name}_A" for name in INPUT_CHANNELS)
    route_board(board, {net_by_name[name].number for name in field_net_names})

    # One reference plane per isolated domain.  Their inner edges preserve the
    # explicit 6.35 mm field/logic copper barrier; they are deliberately not
    # joined by stitching or chassis copper.
    for name, x0, x1 in (("FIELD_0V", 1.5, 56.515), ("GND", 62.865, BOARD_WIDTH - 1.5)):
        board.zones.append(
            Zone(
                net=net_by_name[name].number,
                netName=name,
                layers=["F.Cu", "B.Cu"],
                tstamp=stable_uuid("zone", name),
                name=f"{name}_REFERENCE_PLANE",
                hatch=Hatch(style="edge", pitch=0.5),
                # KiCad 9 serializes a solid/direct zone connection as "yes".
                connectPads="yes",
                clearance=0.4,
                minThickness=0.25,
                fillSettings=FillSettings(
                    yes=True,
                    thermalGap=0.3,
                    thermalBridgeWidth=0.3,
                    islandRemovalMode=0,
                ),
                polygons=[
                    ZonePolygon(
                        coordinates=[
                            Position(x0, 1.5),
                            Position(x1, 1.5),
                            Position(x1, BOARD_HEIGHT - 1.5),
                            Position(x0, BOARD_HEIGHT - 1.5),
                        ]
                    )
                ],
            )
        )
    return board


def make_dru() -> str:
    return """(version 1)\n\n(rule \"Field-to-logic copper barrier\"\n  (condition \"A.NetClass == 'FIELD_24V' && B.NetClass != 'FIELD_24V'\")\n  (constraint clearance (min 6.0mm)))\n"""


def hide_normalized_footprint_references(path: Path) -> None:
    """Restore explicit KiCad 9 metadata lost by kiutils field parsing.

    kiutils keeps footprint properties as key/value pairs, so imported
    Reference fields lose their placement and otherwise render at pad 1.
    Preserve the reference value for BOM/cross-checking while hiding only that
    malformed display field.  Connector/test labels are separate board text.
    """

    source = path.read_text(encoding="utf-8")

    def replacement(match: re.Match[str]) -> str:
        indent, reference = match.group(1), match.group(2)
        field_uuid = stable_uuid("footprint-field", reference or "EMPTY")
        return (
            f'{indent}(property "Reference" "{reference}"\n'
            f'{indent}  (at 0 0 0)\n'
            f'{indent}  (layer "F.SilkS")\n'
            f'{indent}  (hide yes)\n'
            f'{indent}  (uuid {field_uuid})\n'
            f'{indent}  (effects (font (size 1 1) (thickness 0.15)))\n'
            f'{indent})'
        )

    source = re.sub(r'(?m)^(\s+)\(property "Reference" "([^"]*)"\)$', replacement, source)
    path.write_text(source, encoding="utf-8")


def _sexpr_end(source: str, start: int) -> int:
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("unterminated PCB S-expression")


def canonicalize_pcb_object_order(path: Path) -> None:
    """Sort footprint-local user text that pcbnew emits nondeterministically."""

    source = path.read_text(encoding="utf-8")
    footprint_spans = [
        (match.start(), _sexpr_end(source, match.start()))
        for match in re.finditer(r"(?m)^\t\(footprint ", source)
    ]
    for start, end in reversed(footprint_spans):
        block = source[start:end]
        spans = []
        for match in re.finditer(r"(?m)^\t\t\(fp_text user ", block):
            spans.append((match.start(), _sexpr_end(block, match.start())))
        if len(spans) < 2:
            continue
        values = sorted((block[a:b] for a, b in spans), key=lambda item: item.splitlines()[0])
        for (a, b), value in reversed(list(zip(spans, values, strict=True))):
            block = block[:a] + value + block[b:]
        source = source[:start] + block + source[end:]
    path.write_text(source, encoding="utf-8")


def normalize_pcb_object_uuids(path: Path) -> None:
    """Replace pcbnew-created random object UUIDs with ordered UUID5 values.

    The board has no groups or other UUID-member references.  Schematic/PCB
    association is carried by each footprint path, so ordered normalization is
    safe after object order has been canonicalized.
    """

    source = path.read_text(encoding="utf-8")
    index = 0

    def replacement(match: re.Match[str]) -> str:
        nonlocal index
        value = stable_uuid("pcb-object", str(index))
        index += 1
        return f'(uuid "{value}")'

    source = re.sub(r'\(uuid\s+"?[0-9a-fA-F-]{36}"?\)', replacement, source)
    path.write_text(source, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schematic-only", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    make_schematic().to_file(str(OUT / f"{PROJECT}.kicad_sch"))
    (OUT / f"{PROJECT}.kicad_pro").write_text(
        json.dumps(make_project_file(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    generated = [OUT / f"{PROJECT}.kicad_sch", OUT / f"{PROJECT}.kicad_pro"]
    if not args.schematic_only:
        board_path = OUT / f"{PROJECT}.kicad_pcb"
        make_board().to_file(str(board_path))
        hide_normalized_footprint_references(board_path)
        subprocess.run(
            ["/usr/bin/python3", str(OUT / "fill_zones.py"), str(board_path)],
            check=True,
        )
        canonicalize_pcb_object_order(board_path)
        normalize_pcb_object_uuids(board_path)
        (OUT / f"{PROJECT}.kicad_dru").write_text(make_dru(), encoding="utf-8")
        generated.extend((OUT / f"{PROJECT}.kicad_pcb", OUT / f"{PROJECT}.kicad_dru"))
    print("generated " + ", ".join(str(path) for path in generated))


if __name__ == "__main__":
    main()
