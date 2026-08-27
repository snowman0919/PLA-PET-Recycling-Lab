# RTX 3080 virtual-validation runs

이 디렉터리의 JSON은 **VIRTUAL/SIMULATION EVIDENCE**이며 물리시험이 아니다. `two_tower_stability.cu`는 Tower A 질량·CG·가속도·cutter 반력·동적계수·base 깊이 불확실성을 CUDA kernel로 sweep하고 첫 8,192 sample을 같은 식의 host 계산과 교차검산한다.

## 2026-08-28 재현 명령

CUDA EULA package는 시스템 설정을 바꾸지 않고 단일 Nix 호출에서만 허용했다.

```bash
NIXPKGS_ALLOW_UNFREE=1 nix shell --impure \
  nixpkgs#cudaPackages.cuda_nvcc -c nvcc -O3 -std=c++17 \
  -I/nix/store/m7lm9m6nd16xggmgffjqkgvjlpm94n4z-cuda12.9-cuda_cudart-12.9.79/include \
  -L/nix/store/m7lm9m6nd16xggmgffjqkgvjlpm94n4z-cuda12.9-cuda_cudart-12.9.79/lib \
  -lcudart simulation/gpu/two_tower_stability.cu -o /tmp/two_tower_stability
```

Nix binary가 host NVIDIA driver library를 찾도록 재생성 가능한 임시 directory에 `libcuda.so.1`, `libnvidia-ptxjitcompiler.so.1`, `libnvidia-gpucomp.so.595.84` symlink를 만들고 다음을 실행했다.

```bash
LD_LIBRARY_PATH=/tmp/ppr-cuda-driver-libs \
python3 simulation/gpu/run_two_tower_stability.py \
  /tmp/two_tower_stability --samples 4194304
```

2-tower CAD와 단일 baseline 계약 통합 뒤 재실행한 저장 결과는 RTX 3080 compute capability 8.6에서 4,194,304 sample, kernel 0.929 ms, CPU/GPU 최대차 `3.41e-13 N`이다. Unanchored overturn 확률은 0.9990, anchor pair tension p99는 509.3 N, maximum은 683.3 N이며 2 kN screening pair capacity 초과 sample은 없었다. 이 결과는 anchor 필요성을 지지하지만 실제 substrate의 point당 1 kN pullout을 증명하지 않는다.

Store path는 해당 실행환경의 Nix result이므로 다른 시스템에서는 `nix build --no-link --print-out-paths nixpkgs#cudaPackages.cuda_cudart`로 include/lib path를 다시 구한다.
