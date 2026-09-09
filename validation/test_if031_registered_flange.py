"""IF-031 direct hopper/feeder flange geometry regression check (FreeCADCmd)."""

import sys
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad/freecad/compact"))
import geometry


def main():
    hopper = geometry.sealed_feed_hopper_shape()
    feeder = geometry.feeder_housing_shape()
    gasket = geometry.feed_hopper_gasket_shape()
    assert all(shape.isValid() and len(shape.Solids) == 1 for shape in (hopper, feeder, gasket))

    hopper.translate(App.Vector(354, 347, 559.5))
    feeder.translate(App.Vector(354, 347, 399))
    gasket.translate(App.Vector(354, 347, 504))
    assert hopper.common(feeder).Volume < 1e-6
    assert hopper.common(gasket).Volume < 1e-6
    assert feeder.common(gasket).Volume < 1e-6
    assert hopper.distToShape(gasket)[0] < 1e-6
    assert feeder.distToShape(gasket)[0] < 1e-6
    assert 0.045 <= hopper.distToShape(feeder)[0] <= 0.065

    ids = {part["id"] for part in geometry.machine_fabrication_parts()}
    assert "FD-GSK-01" in ids and "FD-TRN-01" not in ids
    print("IF031_REGISTERED_FLANGE_PASS radial_register_clearance=0.050mm transfer_removed=True")


if __name__ == "__main__":
    main()
