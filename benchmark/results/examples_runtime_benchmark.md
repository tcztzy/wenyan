# Wenyan Runtime Benchmark (examples/*.wy)

- generated_at_utc: `2026-02-14T12:12:41+00:00`
- benchmark_examples: `42`
- full_rounds: `1`
- startup_probe_rounds: `5`
- skipped_examples:
  - clock.wy: 需圖形/DOM 環境，非純 stdout。
  - tree.wy: 需圖形輸出，非純 stdout。
  - tree2.wy: 需圖形輸出，非純 stdout。

## Matrix

| runtime | group | version | status | total_median_s | per_example_median_s | startup_median_s | note |
|---|---|---|---|---:|---:|---:|---|
| cli[deno] | cli-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 2.296143 | 0.054670 | 0.039829 | - |
| cli[bun] | cli-js | 1.3.6 | ok | 2.324889 | 0.055355 | 0.039212 | - |
| cli[node] | cli-js | v22.19.0 | ok | 3.478572 | 0.082823 | 0.074663 | - |
| wywy[deno] | wywy-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 4.307083 | 0.102550 | 0.077756 | - |
| wywy[node] | wywy-js | v22.19.0 | ok | 5.478873 | 0.130449 | 0.128298 | - |
| wenyan.py[py314] | wenyan.py | Python 3.14.3 | ok | 6.033547 | 0.143656 | 0.125927 | - |
| wenyan.py[py312] | wenyan.py | Python 3.12.12 | ok | 6.227421 | 0.148272 | 0.184175 | - |
| wywy[bun] | wywy-js | 1.3.6 | ok | 6.236334 | 0.148484 | 0.127974 | - |
| wenyan.py[py313] | wenyan.py | Python 3.13.12 | ok | 6.247909 | 0.148760 | 0.127646 | - |
| wenyan.py[py311] | wenyan.py | Python 3.11.14 | ok | 7.055625 | 0.167991 | 0.129082 | - |
| wenyan.py[py310] | wenyan.py | Python 3.10.19 | ok | 7.930190 | 0.188814 | 0.127819 | - |
| wenyan.py[pypy310] | wenyan.py | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 10.499441 | 0.249987 | 0.127831 | - |
| wenyan.py[graalpy312] | wenyan.py | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 31.926400 | 0.760152 | 0.447814 | - |
| wenyan.py[graalpy311] | wenyan.py | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 33.119887 | 0.788569 | 0.503700 | - |
| wenyan.py[graalpy310] | wenyan.py | GraalPy 3.10.13 (Oracle GraalVM Native 24.0.2) | ok | 51.779351 | 1.232842 | 1.023920 | - |
| wywy[py313] | wywy-python | Python 3.13.12 | ok | 80.552863 | 1.917925 | 0.338452 | - |
| wywy[py314] | wywy-python | Python 3.14.3 | ok | 81.466628 | 1.939682 | 0.287601 | - |
| wywy[py312] | wywy-python | Python 3.12.12 | ok | 91.866809 | 2.187305 | 0.397445 | - |
| wywy[py311] | wywy-python | Python 3.11.14 | ok | 93.321145 | 2.221932 | 0.339855 | - |
| wywy[pypy310] | wywy-python | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 95.228780 | 2.267352 | 0.973091 | - |
| wywy[py310] | wywy-python | Python 3.10.19 | ok | 117.903109 | 2.807217 | 0.346667 | - |
| wywy[graalpy312] | wywy-python | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 181.427535 | 4.319703 | 2.375736 | - |
| wywy[graalpy311] | wywy-python | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 199.064775 | 4.739638 | 2.494106 | - |
| wywy[graalpy310] | wywy-python | GraalPy 3.10.13 (Oracle GraalVM Native 24.0.2) | ok | 246.057489 | 5.858512 | 2.612883 | - |

## Per-example Bar (lower is better)

| runtime | per_example_median_s | bar |
|---|---:|---|
| cli[deno] | 0.054670 | `#` |
| cli[bun] | 0.055355 | `#` |
| cli[node] | 0.082823 | `#` |
| wywy[deno] | 0.102550 | `#` |
| wywy[node] | 0.130449 | `#` |
| wenyan.py[py314] | 0.143656 | `#` |
| wenyan.py[py312] | 0.148272 | `#` |
| wywy[bun] | 0.148484 | `#` |
| wenyan.py[py313] | 0.148760 | `#` |
| wenyan.py[py311] | 0.167991 | `#` |
| wenyan.py[py310] | 0.188814 | `#` |
| wenyan.py[pypy310] | 0.249987 | `#` |
| wenyan.py[graalpy312] | 0.760152 | `####` |
| wenyan.py[graalpy311] | 0.788569 | `####` |
| wenyan.py[graalpy310] | 1.232842 | `#######` |
| wywy[py313] | 1.917925 | `###########` |
| wywy[py314] | 1.939682 | `###########` |
| wywy[py312] | 2.187305 | `#############` |
| wywy[py311] | 2.221932 | `#############` |
| wywy[pypy310] | 2.267352 | `#############` |
| wywy[py310] | 2.807217 | `#################` |
| wywy[graalpy312] | 4.319703 | `##########################` |
| wywy[graalpy311] | 4.739638 | `#############################` |
| wywy[graalpy310] | 5.858512 | `####################################` |
