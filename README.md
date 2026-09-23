# PPR VP1 통합 가상제품

현재 기준은 `KODEX.md`의 경성 목표와 `STATUS.md`의 실행 증거다. VP1은
`호퍼 → S1 → 능동 이송 슈트 → S2 → 버퍼 → 압출 → 냉각 → 풀러 → 스풀`
전 구간을 하나의 CAD/Isaac/BOM 패키지로 통합한다.

## 고정 조건

- S1/S2는 공용 M1 한 개에 종속된 1-DOF 구동계다. 압출기는 별도 M2를 쓴다.
- M1/M2와 웜/휠/베어링은 미선정 또는 미정격이다.
- PSU는 24V 33A, 명판 800W다. 500W는 소프트 운전 목표, 792W는
  전류 정격에서 유도한 강제 상한이다.
- 본체 상한 700×420×520 mm, 추가비 soft limit 100,000 KRW.
- PLA/PET/TPU 물성·파쇄 성능·토크·열·수명은 물리 시험 전 미보정이다.

## 현재 산출물

- `c2.1/cad/PPR_VP1.step`: 전체 기계 조립 STEP.
- `c2.1/cad/PPR_C2_1_machine_integration.FCStd`: 편집 가능한 FreeCAD 조립.
- `c2.1/bom/system_bom.csv` / `.xlsx`: 활성 시스템 BOM.
- `c2.1/electrical/`, `c2.1/firmware/`: 배선과 host-tested 제어 core.
- `c2.2/sim/assets/usd/full_machine.usda`: STEP 대응 전체 기계 Isaac 씬.
- `c2.2/results/full_machine/`: 운동 추적, 소재 경로, 검토 이미지 증거.

정확한 SHA-256, 객체/솔리드 수, 실행 결과와 남은 결함은 `STATUS.md`에만
기록한다. 과거 C1/C2/C2.2 문서의 PASS는 해당 당시 범위의 역사 기록이다.

## 재현 진입점

```sh
python c2/src/run_study.py
python -m unittest discover -s c2/tests -v
python -m unittest discover -s c2.1/tests -v
python c2.1/src/build_machine_integration.py
python c2.1/src/build_machine_freecad.py
python c2.1/src/build_system_bom.py
python c2.1/src/build_machine_wiring.py
python c2.1/src/build_firmware.py
python c2.1/src/build_release_manifest.py
python c2.1/src/verify_artifacts.py
```

디지털 검증은 구매·제작·통전·물리 성능 승인 또는 main 병합 승인이 아니다.
해당 단계는 명시적 사용자 승인 전 **HOLD**다.
