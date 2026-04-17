# Wenyan Runtime Benchmark

- generated_at_utc: `2026-04-04T09:41:15+00:00`
- benchmark_workloads: `17`
- full_rounds: `1`
- startup_probe_rounds: `1`

## Matrix

| runtime | group | version | status | total_median_s | per_example_median_s | startup_median_s | note |
|---|---|---|---|---:|---:|---:|---|
| cli[bun] | cli-js | 1.3.11 | ok | 1.136489 | 0.066852 | 0.040399 | - |
| wenyan.py[py314] | wenyan.py | Python 3.14.3 | ok | 1.611120 | 0.094772 | 0.073456 | - |
| wenyan.py[py313] | wenyan.py | Python 3.13.12 | ok | 1.634666 | 0.096157 | 0.072343 | - |
| cli[node] | cli-js | v25.6.1 | ok | 1.698465 | 0.099910 | 0.076732 | - |
| wenyan.py[py310] | wenyan.py | Python 3.10.20 | ok | 1.717948 | 0.101056 | 0.073273 | - |
| wenyan.py[py312] | wenyan.py | Python 3.12.13 | ok | 1.720901 | 0.101229 | 0.072989 | - |
| wenyan.py[py311] | wenyan.py | Python 3.11.15 | ok | 1.943392 | 0.114317 | 0.123139 | - |
| wywy[node] | wywy-js | v25.6.1 | ok | 2.268580 | 0.133446 | 0.131073 | - |
| wywy[deno] | wywy-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 2.323152 | 0.136656 | 0.130602 | - |
| wywy[bun] | wywy-js | 1.3.11 | ok | 2.955158 | 0.173833 | 0.132621 | - |
| cli[deno] | cli-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 3.670557 | 0.215915 | 0.076664 | - |
| wenyan.py[pypy310] | wenyan.py | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 3.778668 | 0.222275 | 0.131358 | - |
| wywy[py313] | wywy-python | Python 3.13.12 | ok | 7.765472 | 0.456792 | 0.286034 | - |
| wywy[py314] | wywy-python | Python 3.14.3 | ok | 8.013157 | 0.471362 | 0.394409 | - |
| wywy[py312] | wywy-python | Python 3.12.13 | ok | 8.806237 | 0.518014 | 0.290134 | - |
| wywy[py311] | wywy-python | Python 3.11.15 | ok | 9.213376 | 0.541963 | 0.294562 | - |
| wywy[py310] | wywy-python | Python 3.10.20 | ok | 11.404116 | 0.670830 | 0.344865 | - |
| wenyan.py[graalpy312] | wenyan.py | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 13.441499 | 0.790676 | 0.558953 | - |
| wenyan.py[graalpy310] | wenyan.py | GraalPy 3.10.13 (Oracle GraalVM Native 24.0.2) | ok | 14.833680 | 0.872569 | 1.379014 | - |
| wenyan.py[graalpy311] | wenyan.py | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 16.221810 | 0.954224 | 1.611499 | - |
| wywy[pypy310] | wywy-python | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 18.495004 | 1.087941 | 0.831241 | - |
| wywy[graalpy312] | wywy-python | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 67.668028 | 3.980472 | 3.392321 | - |
| wywy[graalpy311] | wywy-python | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 70.584856 | 4.152050 | 3.280968 | - |
| wywy[graalpy310] | wywy-python | GraalPy 3.10.13 (Oracle GraalVM Native 24.0.2) | ok | 76.243376 | 4.484904 | 4.531332 | - |

## Per-example Bar (lower is better)

| runtime | per_example_median_s | bar |
|---|---:|---|
| cli[bun] | 0.066852 | `#` |
| wenyan.py[py314] | 0.094772 | `#` |
| wenyan.py[py313] | 0.096157 | `#` |
| cli[node] | 0.099910 | `#` |
| wenyan.py[py310] | 0.101056 | `#` |
| wenyan.py[py312] | 0.101229 | `#` |
| wenyan.py[py311] | 0.114317 | `#` |
| wywy[node] | 0.133446 | `#` |
| wywy[deno] | 0.136656 | `#` |
| wywy[bun] | 0.173833 | `#` |
| cli[deno] | 0.215915 | `#` |
| wenyan.py[pypy310] | 0.222275 | `#` |
| wywy[py313] | 0.456792 | `###` |
| wywy[py314] | 0.471362 | `###` |
| wywy[py312] | 0.518014 | `####` |
| wywy[py311] | 0.541963 | `####` |
| wywy[py310] | 0.670830 | `#####` |
| wenyan.py[graalpy312] | 0.790676 | `######` |
| wenyan.py[graalpy310] | 0.872569 | `#######` |
| wenyan.py[graalpy311] | 0.954224 | `#######` |
| wywy[pypy310] | 1.087941 | `########` |
| wywy[graalpy312] | 3.980472 | `###############################` |
| wywy[graalpy311] | 4.152050 | `#################################` |
| wywy[graalpy310] | 4.484904 | `####################################` |
