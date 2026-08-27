"""Dependency-free dual-view silhouette measurement and calibration core."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import median, pstdev
from typing import Sequence


@dataclass(frozen=True)
class Region:
    x0: int
    y0: int
    x1: int
    y1: int


@dataclass(frozen=True)
class ViewCalibration:
    mm_per_pixel: float
    bias_mm: float
    u95_mm: float
    homography: tuple[tuple[float, float, float], ...] = (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    radial_distortion: tuple[float, float] = (0.0, 0.0)
    principal_point_px: tuple[float, float] = (0.0, 0.0)
    focal_length_px: tuple[float, float] = (1.0, 1.0)

    @property
    def qualified(self) -> bool:
        return self.u95_mm <= 0.020

    def pixel_to_rectified(self, x: float, y: float) -> tuple[float, float]:
        """Invert radial distortion then apply the calibrated 3x3 homography."""
        cx, cy = self.principal_point_px
        fx, fy = self.focal_length_px
        if fx <= 0 or fy <= 0:
            raise ValueError("focal length must be positive")
        distorted_x = (x - cx) / fx
        distorted_y = (y - cy) / fy
        undistorted_x, undistorted_y = distorted_x, distorted_y
        k1, k2 = self.radial_distortion
        for _ in range(6):
            radius_squared = undistorted_x**2 + undistorted_y**2
            factor = 1.0 + k1 * radius_squared + k2 * radius_squared**2
            if abs(factor) < 1e-9:
                raise ValueError("singular radial distortion")
            undistorted_x = distorted_x / factor
            undistorted_y = distorted_y / factor
        pixel_x = cx + undistorted_x * fx
        pixel_y = cy + undistorted_y * fy
        h = self.homography
        denominator = h[2][0] * pixel_x + h[2][1] * pixel_y + h[2][2]
        if abs(denominator) < 1e-12:
            raise ValueError("singular homography")
        return (
            (h[0][0] * pixel_x + h[0][1] * pixel_y + h[0][2]) / denominator,
            (h[1][0] * pixel_x + h[1][1] * pixel_y + h[1][2]) / denominator,
        )

    def edge_distance_mm(self, left_x: float, right_x: float, y: float) -> float:
        left = self.pixel_to_rectified(left_x, y)
        right = self.pixel_to_rectified(right_x, y)
        rectified_pixels = sqrt((right[0] - left[0]) ** 2 + (right[1] - left[1]) ** 2)
        return self.mm_per_pixel * rectified_pixels + self.bias_mm


@dataclass(frozen=True)
class DiameterMeasurement:
    diameter_x_mm: float
    diameter_y_mm: float
    average_mm: float
    ovality_mm: float
    contaminated: bool
    valid_row_fraction_x: float
    valid_row_fraction_y: float


def fit_view_scale(
    samples: Sequence[tuple[float, float]], pin_u95_mm: float = 0.005
) -> ViewCalibration:
    """Fit diameter = scale*pixel_width+bias and report conservative U95."""
    if len(samples) < 3:
        raise ValueError("at least three calibration diameters are required")
    xs = [sample[1] for sample in samples]
    ys = [sample[0] for sample in samples]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denominator = sum((value - x_mean) ** 2 for value in xs)
    if denominator <= 0:
        raise ValueError("pixel widths have no span")
    scale = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
    bias = y_mean - scale * x_mean
    residuals = [y - (scale * x + bias) for x, y in zip(xs, ys)]
    residual_standard = sqrt(sum(value * value for value in residuals) / max(1, len(xs) - 2))
    u95 = 2.0 * sqrt(residual_standard**2 + (pin_u95_mm / 2.0) ** 2)
    return ViewCalibration(scale, bias, u95)


class DualViewGauge:
    def __init__(
        self,
        region_x: Region,
        region_y: Region,
        calibration_x: ViewCalibration,
        calibration_y: ViewCalibration,
        threshold: int = 128,
    ) -> None:
        self.regions = (region_x, region_y)
        self.calibrations = (calibration_x, calibration_y)
        self.threshold = threshold

    def _measure_region(
        self, image: Sequence[Sequence[int]], region: Region
    ) -> tuple[float, float, float, float, bool]:
        if region.x0 < 0 or region.y0 < 0 or region.y1 > len(image):
            raise ValueError("region outside image")
        widths: list[int] = []
        left_edges: list[int] = []
        right_edges: list[int] = []
        row_positions: list[int] = []
        centers: list[float] = []
        background: list[int] = []
        for row_index in range(region.y0, region.y1):
            row = image[row_index]
            if region.x1 > len(row):
                raise ValueError("region outside image")
            values = row[region.x0 : region.x1]
            dark = [index for index, value in enumerate(values) if value < self.threshold]
            if dark:
                start, end = dark[0], dark[-1]
                if all(values[index] < self.threshold for index in range(start, end + 1)):
                    widths.append(end - start + 1)
                    left_edges.append(region.x0 + start)
                    right_edges.append(region.x0 + end + 1)
                    row_positions.append(row_index)
                    centers.append((start + end) / 2.0)
                    background.extend(values[:start])
                    background.extend(values[end + 1 :])
            else:
                background.extend(values)
        total_rows = region.y1 - region.y0
        valid_fraction = len(widths) / total_rows if total_rows else 0.0
        if not widths:
            raise ValueError("no silhouette")
        width_scatter = pstdev(widths) if len(widths) > 1 else 0.0
        center_scatter = pstdev(centers) if len(centers) > 1 else 0.0
        background_scatter = pstdev(background) if len(background) > 1 else 0.0
        contaminated = (
            valid_fraction < 0.80
            or width_scatter > 1.5
            or center_scatter > 2.0
            or background_scatter > 12.0
        )
        return (
            float(median(left_edges)),
            float(median(right_edges)),
            float(median(row_positions)),
            valid_fraction,
            contaminated,
        )

    def measure(self, image: Sequence[Sequence[int]]) -> DiameterMeasurement:
        left_x, right_x, row_x, fraction_x, dirty_x = self._measure_region(image, self.regions[0])
        left_y, right_y, row_y, fraction_y, dirty_y = self._measure_region(image, self.regions[1])
        diameter_x = self.calibrations[0].edge_distance_mm(left_x, right_x, row_x)
        diameter_y = self.calibrations[1].edge_distance_mm(left_y, right_y, row_y)
        return DiameterMeasurement(
            diameter_x,
            diameter_y,
            (diameter_x + diameter_y) / 2.0,
            abs(diameter_x - diameter_y),
            dirty_x or dirty_y,
            fraction_x,
            fraction_y,
        )
