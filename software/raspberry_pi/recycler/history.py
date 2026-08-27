"""SQLite production/batch history with diameter statistics."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, pstdev
from typing import Iterable


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS batches (
  batch_id TEXT PRIMARY KEY,
  material TEXT NOT NULL CHECK(material IN ('PLA','PET','UNKNOWN')),
  color_bin TEXT NOT NULL,
  recycling_generation INTEGER NOT NULL CHECK(recycling_generation >= 0),
  source_batch_ids_json TEXT NOT NULL,
  started_utc TEXT NOT NULL,
  completed_utc TEXT
);
CREATE TABLE IF NOT EXISTS diameter_samples (
  batch_id TEXT NOT NULL REFERENCES batches(batch_id),
  monotonic_ms INTEGER NOT NULL,
  dx_mm REAL NOT NULL,
  dy_mm REAL NOT NULL,
  average_mm REAL NOT NULL,
  ovality_mm REAL NOT NULL,
  contaminated INTEGER NOT NULL,
  PRIMARY KEY(batch_id, monotonic_ms)
);
CREATE TABLE IF NOT EXISTS events (
  batch_id TEXT,
  monotonic_ms INTEGER NOT NULL,
  level TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class DiameterStatistics:
    count: int
    mean_mm: float
    standard_deviation_mm: float
    minimum_mm: float
    maximum_mm: float
    off_spec_count: int
    maximum_ovality_mm: float


@dataclass(frozen=True)
class OffSpecInterval:
    start_ms: int
    end_ms: int
    sample_count: int


class ProductionHistory:
    def __init__(self, path: str | Path) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.executescript(SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def create_batch(
        self,
        batch_id: str,
        material: str,
        color_bin: str,
        started_utc: str,
        source_batch_ids: Iterable[str] = (),
        recycling_generation: int = 0,
    ) -> None:
        self.connection.execute(
            "INSERT INTO batches VALUES (?,?,?,?,?,?,NULL)",
            (
                batch_id,
                material,
                color_bin,
                recycling_generation,
                json.dumps(list(source_batch_ids), separators=(",", ":")),
                started_utc,
            ),
        )
        self.connection.commit()

    def add_diameter(
        self, batch_id: str, monotonic_ms: int, dx: float, dy: float, contaminated: bool
    ) -> None:
        self.connection.execute(
            "INSERT INTO diameter_samples VALUES (?,?,?,?,?,?,?)",
            (batch_id, monotonic_ms, dx, dy, (dx + dy) / 2.0, abs(dx - dy), int(contaminated)),
        )
        self.connection.commit()

    def add_event(
        self, batch_id: str | None, monotonic_ms: int, level: str, event_type: str, payload: dict
    ) -> None:
        self.connection.execute(
            "INSERT INTO events VALUES (?,?,?,?,?)",
            (batch_id, monotonic_ms, level, event_type, json.dumps(payload, sort_keys=True)),
        )
        self.connection.commit()

    def suggested_generation(self, source_batch_ids: Iterable[str]) -> int:
        source_ids = list(source_batch_ids)
        if not source_ids:
            return 0
        placeholders = ",".join("?" for _ in source_ids)
        rows = self.connection.execute(
            f"SELECT recycling_generation FROM batches WHERE batch_id IN ({placeholders})",
            source_ids,
        ).fetchall()
        if len(rows) != len(set(source_ids)):
            raise ValueError("unknown source batch")
        return max(row[0] for row in rows) + 1

    def diameter_statistics(self, batch_id: str, tolerance_mm: float = 0.05) -> DiameterStatistics:
        rows = self.connection.execute(
            "SELECT average_mm, ovality_mm FROM diameter_samples WHERE batch_id=? AND contaminated=0 ORDER BY monotonic_ms",
            (batch_id,),
        ).fetchall()
        if not rows:
            raise ValueError("no clean diameter samples")
        diameters = [row[0] for row in rows]
        ovalities = [row[1] for row in rows]
        return DiameterStatistics(
            len(diameters),
            fmean(diameters),
            pstdev(diameters),
            min(diameters),
            max(diameters),
            sum(abs(value - 1.75) > tolerance_mm for value in diameters),
            max(ovalities),
        )

    def off_spec_intervals(
        self, batch_id: str, diameter_tolerance_mm: float = 0.05, ovality_limit_mm: float = 0.05
    ) -> list[OffSpecInterval]:
        rows = self.connection.execute(
            "SELECT monotonic_ms, average_mm, ovality_mm, contaminated FROM diameter_samples WHERE batch_id=? ORDER BY monotonic_ms",
            (batch_id,),
        ).fetchall()
        intervals: list[OffSpecInterval] = []
        start: int | None = None
        end = 0
        count = 0
        for timestamp, average, ovality, contaminated in rows:
            bad = bool(contaminated) or abs(average - 1.75) > diameter_tolerance_mm or ovality > ovality_limit_mm
            if bad:
                if start is None:
                    start = timestamp
                    count = 0
                end = timestamp
                count += 1
            elif start is not None:
                intervals.append(OffSpecInterval(start, end, count))
                start = None
        if start is not None:
            intervals.append(OffSpecInterval(start, end, count))
        return intervals
