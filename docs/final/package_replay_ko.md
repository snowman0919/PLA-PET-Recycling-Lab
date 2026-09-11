# 패키지 해석 재실행 안내 — 전체 제작 승인 아님

현재 `dist/PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION.zip`은 최신 패키지가
아니다. 현행 `package_layout.json`과 기존 ZIP의 경로·해시가 일치하지 않으며 실제
ZIP 검증기는 `package differs from current required layout`로 거부했다.
기존 ZIP은 이력 보존을 위해 남겨뒀으며 구매·가공·조립 입력으로 사용하지
않는다. 아래 재실행 결과는 현행 소스 목록에서 만든 별도 사본의 증거다.

ZIP 압축 해제 위치가 아니라 그 아래 `10_DESIGN_SOURCE/`를 작업 디렉터리로
사용한다. Python 스크립트는 자신의 위치를 기준으로 입력 경로를 찾는다.
다른 섹션의 파일을 이 디렉터리로 임의 복사해 누락을 숨기지 않는다.

`flake.nix`, `flake.lock`, `nix/openmodelica.nix`도 같은 소스 루트에 포함한다.
Nix 설치 환경에서는 그 위치에서 `nix develop`로 잠금된 개발 환경을 연다.
이 shell은 OpenModelica 스크립트가 사용하는 `FILAMENT_RECYCLER_ROOT`를 현재
소스 루트로 설정하므로, 다른 디렉터리에서 shell을 열어 실행하지 않는다.
다른 Git 저장소 아래에 압축 해제한 미추적 사본은 `nix develop path:.`로
실제 디렉터리를 명시한다. 일반 호출이 Git 미추적 flake를 제외한다고 해서
검증용 사본을 사용자 저장소에 임의로 git add하지 않는다.
잠금 파일을 갱신하지 않는다. 캐시가 없으면 도구 다운로드가 필요하므로
오프라인 사용을 보장하지 않는다. 사용자 정의 OpenModelica 패키지는
x86_64-linux만 지원하며 aarch64-linux 개발 환경에는 포함되지 않는다.

## 확인한 실행 순서

최종 ZIP 생성기도 무압축 ZIP_STORED와 고정 엔트리 메타데이터를 사용하도록
수정했다. 이는 압축 라이브러리 차이로 생기는 바이트 차이를 없애기 위한
변경이며 최종 ZIP을 발행한 것은 아니다. 엔트리 반복 생성·두 Python 환경
해시 일치 테스트는 통과했지만 전체 릴리스의 두 번 생성 검증은 아직 남아 있다.

설치된 FreeCAD Python 모듈, Gmsh, CalculiX, OpenModelica/Modelica4.0.0,
GCC 및 Python이 필요하다. 도구 자체는 이 소스 패키지에 번들되지 않는다.
검증 시 FreeCAD0.21.2, CalculiX2.21, Gmsh4.15.2,
OpenModelica1.27.0 개발 빌드를 사용했다. 다른 버전의 수치 일치는 미검증이다.

현재 Nix 개발 환경의 FreeCAD는1.1.3으로 위0.21.2와 다르다. 별도 사본에서
1.1.3으로 해석 입력2개를 재생성한 결과, 단일 solid·STEP 재수입 검사는
통과하고 station 값과 bounding box는 같았다. 배럴 체적 차이는
−0.000018 mm³였으나 두 STEP 해시는 달랐다. 따라서 버전 간 파일 해시
동일성을 주장하지 않으며 1.1.3 입력의 메시·전체 해석 재검증은 별도다.
증거 위치: `analysis/final_validation/results/v0.8/package-freecad113-7h82ykm3/`.

후속 LC04 한정 검사: 위1.1.3 생성 bearing_plate STEP을 Gmsh/CalculiX에
연결해 기존3단계 메시를 실행했다. 각 단계의 최대 변위 차이는1e−9 mm 미만,
최대 von Mises 응력 차이는1e−6 MPa 미만으로0.21.2 입력의 기존 결과와
일치했다. 최세밀 최대 변위0.001260654346 mm, LC04 PASS이며 증거는
같은 폴더 하위 `analysis/final_validation/results/v0.8/freecad113_lc04.json`이다.
이 비교는 같은 Gmsh/CalculiX 환경의 LC04만 다룬다. 다른 부품·고온부·
전체 Nix 도구 조합의 수치 동등성으로 확대하지 않는다.

후속 전체 실행기 점검: 분리된 소스에서 `nix develop path:. --command python3
analysis/final_validation/run_calculix_v08.py`를 실행해 요약 생성까지 완료했다.
보고된 도구는 FreeCAD1.1.3/Gmsh4.15.2-git/CalculiX2.23이다. 전체 종료코드1과
FAIL은 현재 미폐쇄 판정을 보존한 결과이며 성공으로 바꾸지 않았다.
증거: `analysis/final_validation/results/v0.8/package-nix-core-dl4pwft5/`의
`nix_core_replay.log` 및 원래 상대 경로의 summary.json/raw 디렉터리.

같은 사본·Nix 환경에서 `python3 analysis/final_validation/run_phase_load_v08.py`도
실행했다. 중심거리 이동 상한0.09753718 mm, 하중 백래시0.07899874–0.42100126 mm,
각도 상한1.00506648°로 기존 환경의 판정과 일치한다. 메시 수렴과 양의
백래시는 통과하지만 기존1° 기준 초과, frame/bearing compliance 및 비틀림
qualification 미완료로 종료코드1/HOLD다. 따라서 이번 도구 버전 변경만으로
기존 위상 차단이 해소되지는 않는다. 결과는 같은 사본의
`analysis/final_validation/results/v0.8/loaded_phase.json`에 보존했다.

```sh
cd 10_DESIGN_SOURCE
# FreeCAD 모듈이 설치된 Python 환경에서 실행한다.
python3 cad/freecad/compact/export_validation_geometry_v08.py
python3 analysis/final_validation/run_qualification_v08.py
omc simulation/openmodelica/scripts/run_v08_release.mos
python3 simulation/openmodelica/postprocess/validate_v08_release.py

# Ø25 phase-path 후보: FreeCAD 모듈 명령은 같은 FreeCAD 환경에서 실행
python3 cad/freecad/compact/check_shaft_section_v08.py
python3 analysis/final_validation/run_phase_section_sensitivity_v08.py
python3 cad/freecad/final_v08/check_phase_path_25_candidate.py
python3 analysis/final_validation/run_keyed_shaft_torsion_candidate.py --span 25_153
python3 analysis/final_validation/run_keyed_shaft_torsion_candidate.py --span 25_105
python3 analysis/final_validation/run_phase_gear_elastic_candidate.py
python3 validation/check_phase_path_25_evidence.py

# 센서 보어 조건부 DC3D4→C3D4 열-압력 screen
python3 analysis/final_validation/run_sensor_bore_local_candidate.py
```

첫 명령은 해석용 STEP2개와 geometry_manifest.json을 재생성한다.
qualification은 비틀림·열·모달 벤치마크 및 단순 부품 계산7항목이다.
OpenModelica는 CSV7개를 생성한다. 후처리 성공 문구뿐 아니라 입력 해시,
완료 시간, 결과 파일과 로그를 함께 보존한다. 새 작업 사본에서 실행해
이전 실행의 결과 파일과 혼동하지 않는다.
Ø25 후보 순서는 결과 파일과 STEP을 처음부터 재생성하며, 단일18 mm 기어가
34 N·m를 전부 받는 최신 보수 조건을 사용한다. 이 순서의 HOLD는 정상
판정이고, release CAD 채택이나 실물 강도 승인이 아니다.

## 검증 범위와 남은 제한

이 순서는 별도 패키지 소스 사본에서 실제 실행했다. 작업 저장소의 결과
JSON을 옮겨 놓고 성공으로 간주한 것이 아니다. 다만 최종 FABRICATION ZIP은
아직 발행 게이트가 닫히지 않았으므로 **최종 ZIP 자체의 실행 합격은 아니다**.

`verify_fabrication_release.py`는 현재 원본 저장소·Git 이력과 ZIP을 대조하는
무결성 검사다. 압축 해제한 폴더만으로 실행하는 독립 해석 검증기가 아니다.
일반 배포 생성기8개의 import 확인도 전체 문서/BOM/CAD 재생성 성공과 다르다.
추가 원본·도구 의존성 폐쇄는 계속 필요하다.

현재 LC02/LC05 및 고온부·공차·축방향 고정은 미폐쇄다. 시뮬레이션의
수치 재현성은 소재·구매품 적합성이나 실제 안전 시험을 대체하지 않는다.
물리 시험 NOT_RUN, 안전 인증 NOT_CERTIFIED, 구매·가공·통전 승인 미완료다.
