# Wenyan Runtime Benchmark

- generated_at_utc: `2026-05-23T03:31:26+00:00`
- benchmark_workloads: `5`
- full_rounds: `3`
- startup_probe_rounds: `5`

## Matrix

| runtime | group | version | status | total_median_s | per_example_median_s | startup_median_s | note |
|---|---|---|---|---:|---:|---:|---|
| cli[deno] | cli-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 0.236168 | 0.047234 | 0.047875 | - |
| cli[bun] | cli-js | 1.3.13 | ok | 0.239115 | 0.047823 | 0.047873 | - |
| cli[node] | cli-js | v25.6.1 | ok | 0.450074 | 0.090015 | 0.089304 | - |
| wenyan.py[py311] | wenyan.py | Python 3.11.15 | ok | 0.637620 | 0.127524 | 0.128795 | - |
| wenyan.py[py314] | wenyan.py | Python 3.14.4 | ok | 0.643130 | 0.128626 | 0.132269 | - |
| wenyan.py[jit-py311] | wenyan.py-jit | Python 3.11.15 | ok | 0.646721 | 0.129344 | 0.129519 | - |
| wenyan.py[jit-py310] | wenyan.py-jit | Python 3.10.20 | ok | 0.647627 | 0.129525 | 0.122703 | - |
| wenyan.py[py310] | wenyan.py | Python 3.10.20 | ok | 0.648571 | 0.129714 | 0.129867 | - |
| wenyan.py[jit-py312] | wenyan.py-jit | Python 3.12.13 | ok | 0.648734 | 0.129747 | 0.133512 | - |
| wenyan.py[jit-py314] | wenyan.py-jit | Python 3.14.4 | ok | 0.649363 | 0.129873 | 0.129972 | - |
| wenyan.py[py313] | wenyan.py | Python 3.13.13 | ok | 0.649712 | 0.129942 | 0.128889 | - |
| wenyan.py[py312] | wenyan.py | Python 3.12.13 | ok | 0.651424 | 0.130285 | 0.128162 | - |
| wenyan.py[jit-py313] | wenyan.py-jit | Python 3.13.13 | ok | 0.661096 | 0.132219 | 0.128880 | - |
| wywy[node] | wywy-js | v25.6.1 | ok | 0.668333 | 0.133667 | 0.090134 | - |
| wywy[deno] | wywy-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 0.700652 | 0.140130 | 0.090307 | - |
| wywy[bun] | wywy-js | 1.3.13 | ok | 0.749598 | 0.149920 | 0.149133 | - |
| wenyan.py[jit-pypy310] | wenyan.py-jit | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 0.866644 | 0.173329 | 0.129667 | - |
| wenyan.py[pypy310] | wenyan.py | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 1.127281 | 0.225456 | 0.184503 | - |
| wenyan.py[graalpy311] | wenyan.py | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 5.726830 | 1.145366 | 17.299944 | - |
| wenyan.py[jit-graalpy312] | wenyan.py-jit | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 8.310966 | 1.662193 | 0.821395 | - |
| wenyan.py[graalpy312] | wenyan.py | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 25.399821 | 5.079964 | 2.300607 | - |
| wenyan.py[jit-graalpy311] | wenyan.py-jit | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 53.758533 | 10.751707 | 5.515348 | - |
| wywy[graalpy311] | wywy-python | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | failed | - | - | - | macro_heavy_s.wy: rc=1, benchmark/workloads/synthetic/macro_heavy/macro_heavy_s.wy: 文法之禍：句首非關鍵 |
| wywy[graalpy312] | wywy-python | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | failed | - | - | - | macro_heavy_s.wy: rc=1, benchmark/workloads/synthetic/macro_heavy/macro_heavy_s.wy: 文法之禍：句首非關鍵 |
| wywy[py310] | wywy-python | Python 3.10.20 | failed | - | - | - | macro_heavy_s.wy: rc=1, benchmark/workloads/synthetic/macro_heavy/macro_heavy_s.wy: 文法之禍：句首非關鍵 |
| wywy[py311] | wywy-python | Python 3.11.15 | failed | - | - | - | macro_heavy_s.wy: rc=1, benchmark/workloads/synthetic/macro_heavy/macro_heavy_s.wy: 文法之禍：句首非關鍵 |
| wywy[py312] | wywy-python | Python 3.12.13 | failed | - | - | - | macro_heavy_s.wy: rc=1, benchmark/workloads/synthetic/macro_heavy/macro_heavy_s.wy: 文法之禍：句首非關鍵 |
| wywy[py313] | wywy-python | Python 3.13.13 | failed | - | - | - | macro_heavy_s.wy: rc=1, benchmark/workloads/synthetic/macro_heavy/macro_heavy_s.wy: 文法之禍：句首非關鍵 |
| wywy[py314] | wywy-python | Python 3.14.4 | failed | - | - | - | macro_heavy_s.wy: rc=1, benchmark/workloads/synthetic/macro_heavy/macro_heavy_s.wy: 文法之禍：句首非關鍵 |
| wywy[pypy310] | wywy-python | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | failed | - | - | - | macro_heavy_s.wy: rc=1, benchmark/workloads/synthetic/macro_heavy/macro_heavy_s.wy: 文法之禍：句首非關鍵 |

## Per-example Bar (lower is better)

| runtime | per_example_median_s | bar |
|---|---:|---|
| cli[deno] | 0.047234 | `#` |
| cli[bun] | 0.047823 | `#` |
| cli[node] | 0.090015 | `#` |
| wenyan.py[py311] | 0.127524 | `#` |
| wenyan.py[py314] | 0.128626 | `#` |
| wenyan.py[jit-py311] | 0.129344 | `#` |
| wenyan.py[jit-py310] | 0.129525 | `#` |
| wenyan.py[py310] | 0.129714 | `#` |
| wenyan.py[jit-py312] | 0.129747 | `#` |
| wenyan.py[jit-py314] | 0.129873 | `#` |
| wenyan.py[py313] | 0.129942 | `#` |
| wenyan.py[py312] | 0.130285 | `#` |
| wenyan.py[jit-py313] | 0.132219 | `#` |
| wywy[node] | 0.133667 | `#` |
| wywy[deno] | 0.140130 | `#` |
| wywy[bun] | 0.149920 | `#` |
| wenyan.py[jit-pypy310] | 0.173329 | `#` |
| wenyan.py[pypy310] | 0.225456 | `#` |
| wenyan.py[graalpy311] | 1.145366 | `###` |
| wenyan.py[jit-graalpy312] | 1.662193 | `#####` |
| wenyan.py[graalpy312] | 5.079964 | `#################` |
| wenyan.py[jit-graalpy311] | 10.751707 | `####################################` |
