# Wenyan Runtime Matrix Compare

- baseline: `benchmark/results/examples_runtime_benchmark.json`
- contender: `benchmark/results/runtime_matrix.release.json`
- baseline_profile: `-`
- contender_profile: `release`
- baseline_workloads: `42`
- contender_workloads: `17`

## Notes

- Baseline uses the historical examples_runtime_benchmark.json corpus (42 examples), while contender uses the new release workload manifest (17 workloads).
- Per-workload ratios are directional only because the workload set and startup probe rounds differ between the two runs.

## Cases

| runtime | baseline_per_example_s | contender_per_example_s | delta | ratio |
|---|---:|---:|---:|---:|
| `cli[bun]` | 0.055355 | 0.066852 | +0.011498 | 1.208 |
| `cli[deno]` | 0.054670 | 0.215915 | +0.161245 | 3.949 |
| `cli[node]` | 0.082823 | 0.099910 | +0.017087 | 1.206 |
| `wenyan.py[graalpy310]` | 1.232842 | 0.872569 | -0.360272 | 0.708 |
| `wenyan.py[graalpy311]` | 0.788569 | 0.954224 | +0.165655 | 1.210 |
| `wenyan.py[graalpy312]` | 0.760152 | 0.790676 | +0.030524 | 1.040 |
| `wenyan.py[py310]` | 0.188814 | 0.101056 | -0.087758 | 0.535 |
| `wenyan.py[py311]` | 0.167991 | 0.114317 | -0.053674 | 0.680 |
| `wenyan.py[py312]` | 0.148272 | 0.101229 | -0.047042 | 0.683 |
| `wenyan.py[py313]` | 0.148760 | 0.096157 | -0.052603 | 0.646 |
| `wenyan.py[py314]` | 0.143656 | 0.094772 | -0.048884 | 0.660 |
| `wenyan.py[pypy310]` | 0.249987 | 0.222275 | -0.027712 | 0.889 |
| `wywy[bun]` | 0.148484 | 0.173833 | +0.025349 | 1.171 |
| `wywy[deno]` | 0.102550 | 0.136656 | +0.034106 | 1.333 |
| `wywy[graalpy310]` | 5.858512 | 4.484904 | -1.373607 | 0.766 |
| `wywy[graalpy311]` | 4.739638 | 4.152050 | -0.587587 | 0.876 |
| `wywy[graalpy312]` | 4.319703 | 3.980472 | -0.339231 | 0.921 |
| `wywy[node]` | 0.130449 | 0.133446 | +0.002997 | 1.023 |
| `wywy[py310]` | 2.807217 | 0.670830 | -2.136387 | 0.239 |
| `wywy[py311]` | 2.221932 | 0.541963 | -1.679969 | 0.244 |
| `wywy[py312]` | 2.187305 | 0.518014 | -1.669291 | 0.237 |
| `wywy[py313]` | 1.917925 | 0.456792 | -1.461133 | 0.238 |
| `wywy[py314]` | 1.939682 | 0.471362 | -1.468319 | 0.243 |
| `wywy[pypy310]` | 2.267352 | 1.087941 | -1.179410 | 0.480 |

- geometric_mean_ratio: `1.431x faster`
