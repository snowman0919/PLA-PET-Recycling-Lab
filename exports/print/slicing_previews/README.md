# Slicing preview package

`validation/slice_prints.py`가 PrusaSlicer 2.9.6 G-code의 첫 extrusion layer를 220×220 mm bed 좌표로 읽어 각 plate와 `PPR-TC01` coupon의 `*-first-layer.svg`를 생성한다.

- SVG는 사람이 bed 배치, skirt/brim, perimeter, infill과 support-contact 유무를 검토하기 위한 경량 release artifact다.
- 같은 폴더의 `.gcode`는 약 49 MB인 재생성 가능 raw output이므로 Git과 artifact manifest에서 제외한다.
- 실제 출력에는 committed slicer profile과 3MF를 사용하고, SVG를 toolpath 또는 machine code로 사용하지 않는다.
- 재생성: `python3 validation/slice_prints.py` (`nix develop` 환경)
