"""Quality-gated production orchestration around injected hardware adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .diameter import DiameterMeasurement, DualViewGauge
from .history import ProductionHistory
from .supervisor import MegaSupervisor


@dataclass(frozen=True)
class QualityGate:
    target_diameter_mm: float = 1.75
    diameter_tolerance_mm: float = 0.05
    maximum_ovality_mm: float = 0.05
    consecutive_bad_frames_to_pause: int = 5
    consecutive_dirty_frames_to_pause: int = 3


class ProductionRuntime:
    def __init__(
        self,
        supervisor: MegaSupervisor,
        gauge: DualViewGauge,
        history: ProductionHistory,
        batch_id: str,
        quality_gate: QualityGate = QualityGate(),
    ) -> None:
        if not all(calibration.qualified for calibration in gauge.calibrations):
            raise ValueError("diameter calibration U95 is not qualified")
        self.supervisor = supervisor
        self.gauge = gauge
        self.history = history
        self.batch_id = batch_id
        self.quality_gate = quality_gate
        self.bad_frames = 0
        self.dirty_frames = 0
        self.quality_pause_sent = False

    def process_camera_frame(
        self, image: Sequence[Sequence[int]], monotonic_ms: int
    ) -> DiameterMeasurement:
        measurement = self.gauge.measure(image)
        self.supervisor.record_camera_frame()
        self.history.add_diameter(
            self.batch_id,
            monotonic_ms,
            measurement.diameter_x_mm,
            measurement.diameter_y_mm,
            measurement.contaminated,
        )
        bad = (
            abs(measurement.average_mm - self.quality_gate.target_diameter_mm)
            > self.quality_gate.diameter_tolerance_mm
            or measurement.ovality_mm > self.quality_gate.maximum_ovality_mm
        )
        self.bad_frames = self.bad_frames + 1 if bad else 0
        self.dirty_frames = self.dirty_frames + 1 if measurement.contaminated else 0
        if not self.quality_pause_sent and (
            self.bad_frames >= self.quality_gate.consecutive_bad_frames_to_pause
            or self.dirty_frames >= self.quality_gate.consecutive_dirty_frames_to_pause
        ):
            self.supervisor.request_pause()
            self.history.add_event(
                self.batch_id,
                monotonic_ms,
                "FAULT",
                "QUALITY_PAUSE",
                {
                    "bad_frames": self.bad_frames,
                    "dirty_frames": self.dirty_frames,
                    "diameter_mm": measurement.average_mm,
                    "ovality_mm": measurement.ovality_mm,
                },
            )
            self.quality_pause_sent = True
        return measurement

    def acknowledge_quality_pause(self) -> None:
        self.bad_frames = 0
        self.dirty_frames = 0
        self.quality_pause_sent = False

    def service_periodic(self) -> list[bytes]:
        return self.supervisor.service_periodic(camera_required=True)
