"""FRP1 protocol shared semantically with the Arduino implementation."""

from __future__ import annotations

from dataclasses import dataclass

MAXIMUM_FRAME_BYTES = 160


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Frame:
    message_type: str
    sequence: int
    payload: str


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def encode_frame(message_type: str, sequence: int, payload: str = "") -> bytes:
    if not 0 <= sequence <= 0xFFFFFFFF:
        raise ProtocolError("sequence outside uint32")
    if not message_type or len(message_type) >= 16:
        raise ProtocolError("invalid type length")
    if len(payload) >= 96 or any(character in message_type + payload for character in "|\r\n"):
        raise ProtocolError("invalid payload/type character or length")
    protected = f"FRP1|{message_type}|{sequence}|{payload}".encode("ascii")
    frame = protected + f"|{crc16_ccitt(protected):04X}\n".encode("ascii")
    if len(frame) >= MAXIMUM_FRAME_BYTES:
        raise ProtocolError("frame too long")
    return frame


def decode_frame(raw: bytes) -> Frame:
    if not raw or len(raw) >= MAXIMUM_FRAME_BYTES:
        raise ProtocolError("empty or oversized frame")
    try:
        text = raw.rstrip(b"\r\n").decode("ascii")
    except UnicodeDecodeError as error:
        raise ProtocolError("non-ASCII frame") from error
    fields = text.split("|")
    if len(fields) != 5:
        raise ProtocolError("field count")
    version, message_type, sequence_text, payload, crc_text = fields
    if version != "FRP1":
        raise ProtocolError("version")
    if not sequence_text.isdecimal():
        raise ProtocolError("sequence")
    sequence = int(sequence_text)
    if sequence > 0xFFFFFFFF:
        raise ProtocolError("sequence")
    if len(message_type) >= 16 or len(payload) >= 96:
        raise ProtocolError("field length")
    try:
        transmitted_crc = int(crc_text, 16)
    except ValueError as error:
        raise ProtocolError("crc syntax") from error
    if len(crc_text) != 4 or not 0 <= transmitted_crc <= 0xFFFF:
        raise ProtocolError("crc syntax")
    protected = "|".join(fields[:4]).encode("ascii")
    if crc16_ccitt(protected) != transmitted_crc:
        raise ProtocolError("crc mismatch")
    return Frame(message_type, sequence, payload)


def sequence_is_newer(candidate: int, previous: int) -> bool:
    difference = (candidate - previous) & 0xFFFFFFFF
    return difference != 0 and difference < 0x80000000
