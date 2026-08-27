# SHR-PLATE-001 proof bearing plate notes

- plate: 150×120×14 mm
- shaft centers: 50 mm apart at `(50,60)`, `(100,60)`
- bearing candidate: 6004-2RS, 20×42×12 mm
- counterbore: nominal 42 mm, depth 11.8 mm
- through shoulder: 36 mm
- counterbore center web: 8 mm
- frame holes: 5.5 mm through, four corners
- combined retainer holes: 4.2 mm through, four locations

counterbore fit tolerance는 plate material, 실제 bearing lot와 load direction을 확인한 뒤 제조사 fit table로 지정한다. 현재 DXF의 `CBORE_DEPTH_11_8` layer는 depth 의도를 나타내며 2D profile만으로 depth를 추측해 가공하면 안 된다.

combined retainer는 100×60×3 mm, bearing clearance hole 36 mm, 양 shaft를 한 부품으로 잡는다. bearing은 shoulder에 닿고 outer face에서 약 0.2 mm 돌출되도록 한 뒤 retainer preload를 shim/coupon으로 확정한다.

Engineering Recommended 조립에는 동일 계열의 세 번째 timing-support plate가 추가된다. timing envelope는 main right bearing과 support bearing 사이에 위치한다. Target Budget에서 이 plate와 bearing 두 개를 빼려면 overhung gear load와 더 낮은 trip torque를 별도 검증해야 한다.

right retainer–timing gear `0.3 mm`, timing gear–support retainer `0.5 mm`는 CAD nominal gap일 뿐 최소 보장 공차가 아니다. 실제 gear face runout, bearing axial play, plate 평행도, shim, thermal growth를 합산한 worst-case stack에서 양수 간극을 확인하고 필요하면 axial layout을 늘린다.
