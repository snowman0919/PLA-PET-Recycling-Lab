# 16 mm × 16 L/D screw — RPM/처리량 sensitivity

`m_dot = channel displacement × bulk density × fill × conveying efficiency × (1-backflow-leakage) × RPM`이며 radial clearance 0.14–0.16 mm, pressure backflow와 flight-tip leakage를 melt factor에 포함했다. 실제 feed/melt 시험은 `PHYSICAL_NOT_RUN`이다.

|재질|RPM|low|nominal|high|residence s|
|---|---:|---:|---:|---:|---:|
|PLA|10|27.3|62.1|96.0|134.4–229.7|
|PLA|14|38.2|86.9|134.4|96.0–164.0|
|PLA|18|49.1|111.8|172.8|74.7–127.6|
|PLA|20|54.5|124.2|192.0|67.2–114.8|
|PLA|24|65.4|149.0|230.4|56.0–95.7|
|PLA|28|76.3|173.9|268.8|48.0–82.0|
|PLA|32|87.2|198.7|307.3|42.0–71.8|
|PLA|36|98.2|223.5|345.7|37.3–63.8|
|PET|10|19.4|54.2|85.8|141.0–256.4|
|PET|14|27.2|75.9|120.1|100.7–183.2|
|PET|18|35.0|97.5|154.4|78.3–142.5|
|PET|20|38.9|108.4|171.6|70.5–128.2|
|PET|24|46.6|130.0|205.9|58.8–106.8|
|PET|28|54.4|151.7|240.2|50.4–91.6|
|PET|32|62.2|173.4|274.5|44.1–80.1|
|PET|36|69.9|195.1|308.8|39.2–71.2|

PLA profile 18 rpm nominal 111.8 g/h, PET profile 20 rpm nominal 108.4 g/h다. 200 g/h는 선택 범위 14–28 rpm의 nominal prediction으로 지지되지 않으며 optimistic fill corner 또는 32–36 rpm 검증이 필요한 stretch target이다.
