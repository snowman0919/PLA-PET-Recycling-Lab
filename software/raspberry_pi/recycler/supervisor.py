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
        elif key in {"state", "phase"}:
            parsed[key] = int(value)
        else:
            try:
                parsed[key] = float(value)
            except ValueError:
                parsed[key] = value
    return parsed


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

    def request_reset(self) -> bytes:
        return self._send("RESET")

    def request_run(self, phase: str) -> bytes:
        if phase not in {"SORT_SHRED", "DRY_PREHEAT", "EXTRUDE_SPOOL", "COOLDOWN_CLEAN"}:
            raise ValueError("unknown phase")
        return self._send("RUN", phase)

    def request_pause(self) -> bytes:
        return self._send("PAUSE")

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
