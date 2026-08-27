"""Transport-neutral Mega supervisor; hardware serial is an injected adapter."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import BinaryIO, Callable

from .protocol import Frame, ProtocolError, decode_frame, encode_frame, sequence_is_newer


@dataclass
class LinkHealth:
    last_rx_monotonic: float | None = None
    last_rx_sequence: int | None = None
    malformed_count: int = 0


def parse_telemetry(payload: str) -> dict[str, int | float | str]:
    parsed: dict[str, int | float | str] = {}
    for field in payload.split(","):
        if "=" not in field:
            raise ProtocolError("telemetry field")
        key, value = field.split("=", 1)
        if not key or key in parsed:
            raise ProtocolError("telemetry key")
        if key == "fault":
            parsed[key] = int(value, 16)
        elif key in {"state", "phase", "jam", "retry"}:
            parsed[key] = int(value)
        else:
            try:
                parsed[key] = float(value)
            except ValueError:
                parsed[key] = value
    return parsed


def parse_ui_command(payload: str) -> tuple[str, str]:
    """Parse a display request; callers still enforce workflow and safety state."""
    if payload.count("=") != 1:
        raise ProtocolError("UI command field")
    command, value = payload.split("=", 1)
    fixed = {
        "ACK_STARTUP": {"1"},
        "MATERIAL": {"AUTO", "PLA", "PET"},
        "CALIBRATION": {"REQUEST"},
        "MAINTENANCE": {"REQUEST"},
    }
    if command in {"COLOR", "BATCH"}:
        if not value.isdecimal() or str(int(value)) != value:
            raise ProtocolError("non-canonical UI integer")
        numeric = int(value)
        if (command == "COLOR" and not 0 <= numeric <= 7) or (
            command == "BATCH" and not 1 <= numeric <= 999
        ):
            raise ProtocolError("UI integer outside range")
    elif command not in fixed or value not in fixed[command]:
        raise ProtocolError("unsupported UI command")
    return command, value


class MegaSupervisor:
    def __init__(self, stream: BinaryIO, clock: Callable[[], float] = monotonic) -> None:
        self.stream = stream
        self.clock = clock
        self.tx_sequence = 0
        self.health = LinkHealth()
        self.last_heartbeat_sent: float | None = None
        self.last_camera_frame: float | None = None
        self.camera_pause_sent = False

    def _send(self, message_type: str, payload: str = "") -> bytes:
        self.tx_sequence = (self.tx_sequence + 1) & 0xFFFFFFFF
        frame = encode_frame(message_type, self.tx_sequence, payload)
        self.stream.write(frame)
        return frame

    def heartbeat(self) -> bytes:
        self.last_heartbeat_sent = self.clock()
        return self._send("HB", f"uptime_ms={int(self.last_heartbeat_sent * 1000)}")

    def record_camera_frame(self) -> None:
        self.last_camera_frame = self.clock()
        self.camera_pause_sent = False

    def service_periodic(self, camera_required: bool) -> list[bytes]:
        """Send 250 ms heartbeat and one PAUSE after a 3 s camera dropout."""
        now = self.clock()
        frames: list[bytes] = []
        if self.last_heartbeat_sent is None or now - self.last_heartbeat_sent >= 0.250:
            frames.append(self.heartbeat())
        if (
            camera_required
            and self.last_camera_frame is not None
            and now - self.last_camera_frame > 3.0
            and not self.camera_pause_sent
        ):
            frames.append(self.request_pause())
            self.camera_pause_sent = True
        return frames

    def select_profile(self, material: str) -> bytes:
        if material not in {"PLA", "PET"}:
            raise ValueError("profile must be PLA or PET")
        return self._send("PROFILE", material)

    def select_dryer_stage(self, stage: str) -> bytes:
        if stage not in {"PLA_45", "PET_140", "PET_160"}:
            raise ValueError("unknown fixed dryer stage")
        return self._send("DRY_STAGE", stage)

    def request_reset(self) -> bytes:
        return self._send("RESET")

    def request_run(self, phase: str) -> bytes:
        if phase not in {"SORT_SHRED", "DRY_PREHEAT", "EXTRUDE_SPOOL", "COOLDOWN_CLEAN"}:
            raise ValueError("unknown phase")
        return self._send("RUN", phase)

    def request_pause(self) -> bytes:
        return self._send("PAUSE")

    def acknowledge_purge(self) -> bytes:
        """Request purge completion; Mega also requires local BACK while stopped."""
        return self._send("PURGE_ACK")

    def send_ui_classification(
        self,
        detected: int,
        confidence_pct: int,
        selected: int,
        color_bin: int,
        batch_number: int,
        purge_required: bool,
        classifier_qualified: bool,
    ) -> bytes:
        if not 0 <= detected <= 4 or not 0 <= selected <= 4:
            raise ValueError("UI material code outside enum")
        if not 0 <= confidence_pct <= 100 or not 0 <= color_bin <= 7:
            raise ValueError("UI classification value outside range")
        if not 0 <= batch_number <= 999:
            raise ValueError("UI batch outside range")
        payload = (
            f"det={detected},conf={confidence_pct},selected={selected},"
            f"color={color_bin},batch={batch_number},purge={int(purge_required)},"
            f"classok={int(classifier_qualified)}"
        )
        return self._send("UI_CLASS", payload)

    def send_ui_production(
        self,
        diameter_x_mm: float,
        diameter_y_mm: float,
        length_m: float,
        weight_g: int,
        eta_minutes: int,
        gauge_qualified: bool,
    ) -> bytes:
        dx_um = round(diameter_x_mm * 1000)
        dy_um = round(diameter_y_mm * 1000)
        length_mm = round(length_m * 1000)
        if not 0 <= dx_um <= 10000 or not 0 <= dy_um <= 10000:
            raise ValueError("UI diameter outside range")
        if (
            not 0 <= length_mm <= 0xFFFFFFFF
            or not 0 <= weight_g <= 0xFFFFFFFF
            or not 0 <= eta_minutes <= 65535
        ):
            raise ValueError("UI production value outside range")
        return self._send(
            "UI_PROD",
            f"dx_um={dx_um},dy_um={dy_um},len_mm={length_mm},weight_g={weight_g},"
            f"eta_min={eta_minutes},gaugeok={int(gauge_qualified)}",
        )

    def send_ui_stock(self, hopper_fill_pct: int, full_bin_mask: int) -> bytes:
        if not 0 <= hopper_fill_pct <= 100 or not 0 <= full_bin_mask <= 0xFF:
            raise ValueError("UI stock value outside range")
        return self._send("UI_STOCK", f"hopper={hopper_fill_pct},full={full_bin_mask:02X}")

    def receive(self, raw: bytes) -> Frame | None:
        try:
            frame = decode_frame(raw)
        except ProtocolError:
            self.health.malformed_count += 1
            return None
        if self.health.last_rx_sequence is not None and not sequence_is_newer(
            frame.sequence, self.health.last_rx_sequence
        ):
            self.health.malformed_count += 1
            return None
        self.health.last_rx_sequence = frame.sequence
        self.health.last_rx_monotonic = self.clock()
        self.health.malformed_count = 0
        return frame
