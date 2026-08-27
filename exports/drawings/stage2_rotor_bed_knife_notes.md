# Stage 2 rotor / bed knife proof notes

## rotor

- OD envelope: 50 mm
- core OD: 38 mm
- active width: 64 mm
- shaft bore: 20 mm + provisional 6 mm keyway
- blade rows: 3; each row has 8 axial segments
- segment width / total stagger: 8 mm / 14°
- blade tangential thickness: 4 mm
- proof mass at steel density: 약 0.437 kg

현재 CAD는 core와 staggered segment를 fuse한 staircase kinematic proof다. 실제 제작에는 replaceable blade pocket, positive dowel/shoulder, bolt preload, thread engagement, centrifugal retention, 120 rpm balance feature와 edge grind를 새 revision으로 추가한다. 이 STEP을 그대로 가공 주문하지 않는다.

## bed knife / carrier

- knife proof block: radial 8 mm × tangential 20 mm × width 64 mm
- carrier: radial 20 mm × tangential 32 mm × axial 68 mm
- four nominal 6.6 mm through holes, two tangential rows × two axial stations
- blade swept envelope와 nominal 0.2 mm clearance

bolt friction만으로 절삭 반력을 받지 않도록 knife 뒤 shoulder/dowel을 상세 설계한다. shim은 금속 ground stock을 사용하고 좌우 동일 두께만 가정하지 않는다. dial-indicator로 rotor runout과 plate 평행도를 측정한 뒤 각 위치의 feeler-gauge 최소 간극을 기록한다.

## plate

- 110×100×14 mm
- shaft center `(40,50)`
- 6004 counterbore nominal Ø42, depth 11.8 mm
- through shoulder Ø36
- 외측 bearing face 0.2 mm proud + retainer

counterbore fit, retainer preload, plate material과 carrier-to-plate fastener는 미확정이다. DXF layer 이름은 depth 의도만 표시하며 2D profile만으로 가공 깊이를 추측하지 않는다.
