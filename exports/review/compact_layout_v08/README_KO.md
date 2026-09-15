# 공용 경로 소형 배치 검토본

정식 제조도면이 아니다. 공개 rc1 또는 exports/final의 GGM-FULL-ASM과 혼용하지 않는다. 이 디렉터리의 STEP/FCStd는 같은 원본 부품의 강체 재배치 검토다. 제작·통전·구매 승인은 없다.

- 생성기: analysis/compact_layout_v08/review.py
- 조건: analysis/compact_layout_v08/contract.json
- 결과와 정확한 생성물 SHA-256: analysis/compact_layout_v08/results/review.json
- 목적/결과/제한: docs/reviews/compact-purpose-v08/PURPOSE_AND_LAYOUT_KO.md
- 검사: validation/test_compact_layout_review.py

저장소 루트의 고정 Nix 환경에서 FreeCADCmd -c를 실행하고 Python 콘솔에서 다음을 실행한다.

```python
import runpy
runpy.run_path('analysis/compact_layout_v08/review.py', run_name='__main__')
```

생성 파일은 PPR-COMPACT-PLACEMENT-REVIEW.step 및 PPR-COMPACT-PLACEMENT-REVIEW.FCStd다. 큰 재생성 모델은 검토 머신에 보존하고 소스/계약/결과를 Git으로 추적한다. FreeCAD 문서의 저장 메타데이터는 재생성에 따라 달라질 수 있다. 재생성 결과의 새로운 해시와 실제 solid 차집합 검사를 사용하며 과거 파일 해시와 무조건 동일하다고 주장하지 않는다.

작동 외형470x700x930 mm, 기존과 동일한266개 객체/276개 solid. 뚜껑 개방 작업 폭679 mm가 별도로 필요하다. 형상 검토를 최종 프레임 하중 검증·입자 회수·안전장치 시험·전체 설계 승격으로 취급하지 않는다.
