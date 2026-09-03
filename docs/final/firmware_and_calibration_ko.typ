#set document(title: "firmware and calibration")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= firmware and calibration
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

== Firmware

Released HEX는 `exports/final/firmware/binaries/filament_recycler_atmega2560.hex`; build evidence는 `validation/results/arduino_mega_compile.json`이다. Source/HEX hash 일치를 검증하고 Mega 2560 target/fuse setting을 확인한다.

== Calibration

Donor label 확인 후 shredder current/RPM, screw tach, puller/spooler tach, traverse limits, X/Y gauge U95, dancer, cooling current와 fan tach를 각각 교정한다. EEPROM CRC/revision/unit/range가 유효하지 않으면 production ready를 금지한다.
