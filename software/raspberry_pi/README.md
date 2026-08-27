# Raspberry Pi 4 감독 소프트웨어

`recycler/`는 표준 라이브러리만 사용하는 시험 가능한 core다.

- `protocol.py`: Mega FRP1 CRC/sequence protocol
- `diameter.py`: dual-view backlight silhouette, radial-distortion 역보정, 3×3 homography, 4-pin scale fit, contamination gate와 U95 qualification
- `classifier.py`: camera transparency + motor current/speed/vibration prototype fusion, confidence와 fixed CIELAB 6-bin+Reject
- `history.py`: SQLite batch, source batch, recycling generation, raw diameter, 통계와 연속 불량구간
- `supervisor.py`: 250 ms heartbeat, 3 s camera-dropout PAUSE, profile/phase/purge와 bounded UI snapshot/command adapter
- `dataset.py`: source-object group ID와 image SHA-256을 강제하는 append-only 수집 manifest
- `runtime.py`: qualified gauge만 허용하고 5회 연속 직경/ovality 불량 또는 3회 오염 frame에서 PAUSE와 event를 남기는 production core

시험:

```bash
PYTHONPATH=software/raspberry_pi \
  python3 -m unittest discover -s software/raspberry_pi/tests -v
```

`config/material_prototypes.example.json`의 숫자는 software path 시험용 provisional 시작점이며 실제 분류 모델이 아니다. PLA/PET/UNKNOWN, 색상 6범주, 서로 다른 두께·투명도·오염 lot를 수집하고 train/validation batch를 source object 기준으로 분리하기 전 정확도·recall을 선언하지 않는다. Confidence가 0.80 이상이면 자동 승인, 0.55–0.80이면 사용자 확인, 그 아래 또는 out-of-distribution이면 Reject를 기본으로 한다.

## 실제 장치 adapter

Production image adapter는 Raspberry Pi OS의 Picamera2/libcamera로 exposure, white balance, focus와 frame ID를 고정하고 grayscale frame을 `DualViewGauge`에 전달한다. USB serial은 pyserial 또는 POSIX serial adapter가 `MegaSupervisor`의 binary stream interface를 구현한다. 이 hardware-specific package는 Pi image와 Camera Module 3가 정해진 뒤 lock file로 고정한다.

Gauge release에는 1.50/1.75/2.00/2.50 mm traceable pin, 두 광로의 lens distortion/homography, field 위치별 반복측정과 `U95≤0.020 mm`가 필요하다. Core의 synthetic test 통과는 실제 optic을 승인하지 않는다. Camera frame이 3 s 이상 끊기면 Pi가 PAUSE를 요청하지만, 요청 전달 실패와 무관하게 Mega의 750 ms heartbeat timeout이 위험 출력을 차단한다.

SQLite에는 평균·표준편차·최소·최대·ovality와 contaminated frame을 분리 저장한다. 생산 batch는 원료 source batch ID와 recycling generation을 가져야 하며 원시 telemetry/frame metadata를 삭제하지 않고 파생 통계와 함께 export한다.

Dryer recipe는 Pi가 임의 온도를 보내지 않고 `PLA_45`, `PET_140`, `PET_160` 중 하나만 요청한다. Mega는 현재 material profile과 맞지 않는 stage를 무시하고 PLA/PET heater 출력을 같은 loop에서 동시에 0으로 만든 뒤 선택 branch 하나만 허용한다.

`UI_CLASS`, `UI_PROD`, `UI_STOCK`은 TFT 표시용 정수 snapshot이다. Mega의 `UI_CMD`는 whitelist로 parsing한 뒤 application이 batch/recipe/calibration workflow에서 다시 승인한다. UI 명령은 `RUN`으로 변환하지 않는다. 재질 변경 purge 완료는 Pi의 `PURGE_ACK`만으로 끝나지 않고, Mega가 정지 상태와 local BACK/ABORT 동시 입력을 요구한다.
