# Static stress

LC01–LC06, LC09를 각각 수행한다. `materials.csv`, `contact_pairs.csv`, `constraints.csv`의 이름 기반 selection을 검토한 후 coarse/medium/fine tetra mesh를 사용한다. stress, displacement, reaction balance와 SF를 내보낸다. medium→fine 전역 displacement 변화 ≤5%, 허용응력 기준 SF≥2.0이 합격이다. 고정·점하중 인접 singular stress는 별도 태그하고 전역 판정을 지배하지 않는다.
