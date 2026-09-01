# Puller–spooler–traverse 제어

Puller는 diameter PI가 목표 line speed를 만들고, roller diameter로 목표 RPM을 변환한 뒤 tach PI가 PWM을 만든다. CRC calibration에는 roller diameter, puller tach PPR, screw/spool tach PPR, traverse steps/mm가 들어간다. 실제 elapsed time, startup ramp, minimum useful PWM, bounds, conditional integration, tach timeout을 사용한다. saturation은 bound 근처 명령과 큰 속도오차가 0.8 s 지속될 때만 true다.

Spooler는 dancer target을 기준으로 PI 보정하고 wound length/known geometry에서 26–100 mm radius를 추정한다. dedicated tach가 있으면 turns와 jam evidence에 사용한다. radius는 추정값이며 winding packing 품질을 주장하지 않는다.

Traverse는 spool cumulative turns×1.85 mm pitch로 68 mm triangular target을 만든다. reversal은 wall clock이 아니라 turns/endpoints에서 발생하며 A5/A6 limit와 missed-limit timeout을 사용한다. production spool eligibility가 false이면 disabled다.
