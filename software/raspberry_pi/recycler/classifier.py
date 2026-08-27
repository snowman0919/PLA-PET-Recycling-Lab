"""Provisional sensor-fusion and fixed CIELAB color classification."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, pow, sqrt
from typing import Mapping, Sequence


COLOR_CENTERS_LAB: dict[str, tuple[float, float, float]] = {
    "CLEAR_NATURAL_WHITE": (88.0, 0.0, 3.0),
    "BLACK_DARK_GRAY": (22.0, 0.0, 0.0),
    "RED_ORANGE": (55.0, 55.0, 42.0),
    "YELLOW_GREEN": (72.0, -30.0, 58.0),
    "BLUE_PURPLE": (42.0, 30.0, -48.0),
    "BROWN_MIXED_OTHER": (42.0, 18.0, 24.0),
}


def _linearize(value: float) -> float:
    value /= 255.0
    return ((value + 0.055) / 1.055) ** 2.4 if value > 0.04045 else value / 12.92


def srgb_to_lab(red: float, green: float, blue: float) -> tuple[float, float, float]:
    r, g, b = (_linearize(value) for value in (red, green, blue))
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(value: float) -> float:
        return value ** (1.0 / 3.0) if value > 0.008856 else 7.787 * value + 16.0 / 116.0

    fx, fy, fz = f(x), f(y), f(z)
    return 116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)


def classify_color(lab: Sequence[float], maximum_delta_e: float = 45.0) -> str:
    distances = {
        label: sqrt(sum((value - center) ** 2 for value, center in zip(lab, prototype)))
        for label, prototype in COLOR_CENTERS_LAB.items()
    }
    label = min(distances, key=distances.get)
    return label if distances[label] <= maximum_delta_e else "REJECT"


@dataclass(frozen=True)
class FusionResult:
    label: str
    confidence: float
    disposition: str
    distances: Mapping[str, float]


class FusionClassifier:
    """Standardized prototype distance; remains provisional until sample validation."""

    def __init__(self, prototypes: Mapping[str, Mapping[str, Sequence[float]]]) -> None:
        self.prototypes = prototypes

    def classify(self, features: Mapping[str, float]) -> FusionResult:
        distances: dict[str, float] = {}
        for label, model in self.prototypes.items():
            names = list(model["feature_names"])
            mean = list(model["mean"])
            scale = list(model["scale"])
            if not all(name in features for name in names) or any(value <= 0 for value in scale):
                raise ValueError(f"invalid/missing features for {label}")
            squared = sum(
                pow((features[name] - expected) / deviation, 2)
                for name, expected, deviation in zip(names, mean, scale)
            )
            distances[label] = sqrt(squared / len(names))
        if not distances:
            raise ValueError("no prototypes")
        ordered = sorted(distances, key=distances.get)
        best = ordered[0]
        weights = {label: exp(-0.5 * distance * distance) for label, distance in distances.items()}
        confidence = weights[best] / sum(weights.values()) if sum(weights.values()) else 0.0
        if distances[best] > 3.5 or confidence < 0.55:
            return FusionResult("UNKNOWN", confidence, "REJECT", distances)
        disposition = "AUTO_APPROVE" if confidence >= 0.80 else "USER_CONFIRM"
        return FusionResult(best, confidence, disposition, distances)
