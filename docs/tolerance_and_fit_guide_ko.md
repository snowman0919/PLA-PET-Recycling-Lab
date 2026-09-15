# v0.8 공차·끼워맞춤 지침

모든 수치는 component limit의 worst-case 산술 결과다. 실제 수령검사와 물리 조립 시험을 대신하지 않는다.

|ID|인터페이스|Worst-case|계산|
|---|---|---:|---|
|TS-01|CUT-01 discs ↔ CUT-02 spacers/collars|0.25–0.5 mm|0.375 ± 0.125|
|TS-02|CUT-05 shafts ↔ CUT-03 matched plates|0.05–0.2 mm|0.125 ± (0.050 + 0.025)|
|TS-03|DRV-03 phase gears ↔ CUT-03 bearing centres|0.15–0.35 mm|0.25 ± (0.03 + 0.05 + 0.02)|
|TS-04|CUT-03 front plate ↔ CUT-03 rear plate|0–0.05 mm/140mm||front| + |rear| = 0.050 max|
|TS-05|EX-SCR-01 flight ↔ EX-BAR-01 bore|0.14–0.16 mm|(ID limit − OD opposite limit) / 2|
|TS-06|EX-BAR-01 bore axis ↔ EX-DIE-01 channel axis|0–0.05 mm||barrel| + |die| = 0.050 max|
|TS-07|TH-BH-01 heater ID ↔ EX-BAR-01 OD|0.0–0.13 mm|heater ID limit − barrel OD opposite limit|
|TS-08|TEMP-01..03 bore tip ↔ EX-BAR-01 melt bore|3.325–3.45 mm|OD radius − melt radius − blind depth|
|TS-09|FD-MET-02 auger ↔ FD-MET-01 housing|0.2–0.25 mm|(housing ID limit − auger OD opposite limit) / 2|
|TS-10|FM-RL-01 roller pair ↔ 1.75 mm strand|1.6–1.9 mm|1.75 ± (0.10 + 0.05)|
|TS-11|PPR-C06 X gauge ↔ PPR-C06 Y gauge|0–0.1 mm||X| + |Y| = 0.10 max|
|TS-12|SP-TR-01 traverse ↔ Ø8 rods|0–0.1 mm/160mm||left| + |right| + straightness = 0.10 max|
|TS-13|guards/panels ↔ moving envelopes|2.0–4.0 mm|3.0 ± (0.5 + 0.5)|
|TS-14|hot shield ↔ 300 °C hot envelope|10–14 mm|12.0 ± (1.0 + 1.0)|
|TS-15|EX-MT-02 radial guide ↔ EX-BAR-01|0.1338–0.3338 mm|available travel limit − predicted growth|
|TS-16|EX-SCR-01 flight ↔ EX-BAR-01 bore|0.138–0.1629 mm|(hot bore ID − hot screw OD) / 2|

Cutter/blade gap은 출력 공차가 아니라 금속 shim으로만 맞춘다. Heater, cutter, screw 및 고전류 작업의 물리 합격은 별도 lockout·사용자 확인 전까지 `NOT_RUN`이다.
