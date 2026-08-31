# Fusion delta queue

v0.6.2 concurrent phase에는 `FUSION_NEUTRAL`과 `FUSION_RESULT_CONSUMER`만 적용한다. invalidating proposal은 `proposals/<change-id>/`에 격리해야 하며 현재 proposal은 없다. `validation/fusion_delta_classification.py`가 frozen path diff와 binding SHA를 검사한다.
