#include <cuda_runtime.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>


constexpr double G = 9.80665;
constexpr std::uint64_t SEED = 20260828ULL;


__host__ __device__ std::uint64_t xorshift64star(std::uint64_t &state) {
    state ^= state >> 12;
    state ^= state << 25;
    state ^= state >> 27;
    return state * 2685821657736338717ULL;
}


__host__ __device__ double uniform01(std::uint64_t &state) {
    return static_cast<double>(xorshift64star(state) >> 11) * (1.0 / 9007199254740992.0);
}


__host__ __device__ double one_sample(std::uint64_t index, bool *unanchored_overturn) {
    std::uint64_t state = SEED ^ ((index + 1ULL) * 0x9E3779B97F4A7C15ULL);
    const double mass = 57.5 * (0.80 + 0.40 * uniform01(state));
    const double cg_m = 0.6754 + 0.10 * (uniform01(state) - 0.5);
    const double acceleration_g = 0.25 + 0.20 * uniform01(state);
    const double cutter_force_n = 40.0 + 60.0 * uniform01(state);
    const double cutter_height_m = 0.8925 + 0.10 * uniform01(state);
    const double dynamic_factor = 1.20 + 0.60 * uniform01(state);
    const double base_depth_m = 0.58 + 0.04 * uniform01(state);
    const double anchor_spacing_m = 0.52;

    const double inertial_force = mass * G * acceleration_g;
    const double overturning = dynamic_factor * (
        inertial_force * cg_m + cutter_force_n * cutter_height_m
    );
    const double restoring = mass * G * base_depth_m / 2.0;
    *unanchored_overturn = overturning > restoring;
    return fmax(0.0, overturning - restoring) / anchor_spacing_m;
}


__global__ void stability_kernel(double *tensions, unsigned int *overturn_flags, std::uint64_t count) {
    const std::uint64_t index = static_cast<std::uint64_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (index >= count) return;
    bool overturn = false;
    tensions[index] = one_sample(index, &overturn);
    overturn_flags[index] = overturn ? 1U : 0U;
}


void check(cudaError_t result, const char *operation) {
    if (result != cudaSuccess) {
        std::cerr << operation << ": " << cudaGetErrorString(result) << "\n";
        std::exit(2);
    }
}


std::string escaped(const char *text) {
    std::string out;
    for (const char *p = text; *p; ++p) {
        if (*p == '\\' || *p == '"') out.push_back('\\');
        out.push_back(*p);
    }
    return out;
}


int main(int argc, char **argv) {
    const std::uint64_t count = argc > 1 ? std::strtoull(argv[1], nullptr, 10) : (1ULL << 22);
    if (count < 100000ULL) {
        std::cerr << "sample count must be at least 100000\n";
        return 2;
    }

    int device = 0;
    cudaDeviceProp props{};
    check(cudaSetDevice(device), "cudaSetDevice");
    check(cudaGetDeviceProperties(&props, device), "cudaGetDeviceProperties");

    double *device_tensions = nullptr;
    unsigned int *device_flags = nullptr;
    check(cudaMalloc(&device_tensions, count * sizeof(double)), "cudaMalloc tensions");
    check(cudaMalloc(&device_flags, count * sizeof(unsigned int)), "cudaMalloc flags");

    cudaEvent_t start{}, stop{};
    check(cudaEventCreate(&start), "cudaEventCreate start");
    check(cudaEventCreate(&stop), "cudaEventCreate stop");
    const int threads = 256;
    const int blocks = static_cast<int>((count + threads - 1) / threads);
    check(cudaEventRecord(start), "cudaEventRecord start");
    stability_kernel<<<blocks, threads>>>(device_tensions, device_flags, count);
    check(cudaGetLastError(), "stability_kernel launch");
    check(cudaEventRecord(stop), "cudaEventRecord stop");
    check(cudaEventSynchronize(stop), "cudaEventSynchronize");
    float elapsed_ms = 0.0F;
    check(cudaEventElapsedTime(&elapsed_ms, start, stop), "cudaEventElapsedTime");

    std::vector<double> tensions(count);
    std::vector<unsigned int> flags(count);
    check(cudaMemcpy(tensions.data(), device_tensions, count * sizeof(double), cudaMemcpyDeviceToHost), "copy tensions");
    check(cudaMemcpy(flags.data(), device_flags, count * sizeof(unsigned int), cudaMemcpyDeviceToHost), "copy flags");

    double max_crosscheck_error = 0.0;
    const std::uint64_t crosscheck_count = std::min<std::uint64_t>(8192ULL, count);
    for (std::uint64_t i = 0; i < crosscheck_count; ++i) {
        bool overturn = false;
        const double cpu = one_sample(i, &overturn);
        max_crosscheck_error = std::max(max_crosscheck_error, std::abs(cpu - tensions[i]));
        if ((overturn ? 1U : 0U) != flags[i]) {
            std::cerr << "CPU/GPU overturn flag mismatch at " << i << "\n";
            return 3;
        }
    }

    std::uint64_t overturn_count = 0;
    std::uint64_t capacity_exceed_count = 0;
    double sum = 0.0;
    double maximum = 0.0;
    for (std::uint64_t i = 0; i < count; ++i) {
        overturn_count += flags[i];
        capacity_exceed_count += tensions[i] > 2000.0 ? 1ULL : 0ULL;
        sum += tensions[i];
        maximum = std::max(maximum, tensions[i]);
    }
    std::sort(tensions.begin(), tensions.end());
    const auto quantile = [&](double q) {
        return tensions[static_cast<std::size_t>(q * static_cast<double>(count - 1))];
    };

    int runtime_version = 0;
    int driver_version = 0;
    check(cudaRuntimeGetVersion(&runtime_version), "cudaRuntimeGetVersion");
    check(cudaDriverGetVersion(&driver_version), "cudaDriverGetVersion");
    std::cout.precision(12);
    std::cout << "{\n"
              << "  \"backend\": \"CUDA\",\n"
              << "  \"device_name\": \"" << escaped(props.name) << "\",\n"
              << "  \"compute_capability\": \"" << props.major << "." << props.minor << "\",\n"
              << "  \"global_memory_bytes\": " << props.totalGlobalMem << ",\n"
              << "  \"cuda_runtime_version\": " << runtime_version << ",\n"
              << "  \"cuda_driver_api_version\": " << driver_version << ",\n"
              << "  \"sample_count\": " << count << ",\n"
              << "  \"random_seed\": " << SEED << ",\n"
              << "  \"kernel_elapsed_ms\": " << elapsed_ms << ",\n"
              << "  \"cpu_gpu_crosscheck_samples\": " << crosscheck_count << ",\n"
              << "  \"cpu_gpu_max_abs_error_n\": " << max_crosscheck_error << ",\n"
              << "  \"unanchored_overturn_probability\": " << static_cast<double>(overturn_count) / count << ",\n"
              << "  \"anchor_pair_capacity_exceed_probability\": " << static_cast<double>(capacity_exceed_count) / count << ",\n"
              << "  \"anchor_pair_tension_mean_n\": " << sum / count << ",\n"
              << "  \"anchor_pair_tension_p95_n\": " << quantile(0.95) << ",\n"
              << "  \"anchor_pair_tension_p99_n\": " << quantile(0.99) << ",\n"
              << "  \"anchor_pair_tension_max_n\": " << maximum << "\n"
              << "}\n";

    cudaEventDestroy(start);
    cudaEventDestroy(stop);
    cudaFree(device_tensions);
    cudaFree(device_flags);
    return 0;
}
