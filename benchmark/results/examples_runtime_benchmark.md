# Wenyan Runtime Benchmark (examples/*.wy)

- generated_at_utc: `2026-02-11T10:09:33+00:00`
- benchmark_examples: `42`
- full_rounds: `1`
- startup_probe_rounds: `100`
- skipped_examples:
  - clock.wy: 需圖形/DOM 環境，非純 stdout。
  - tree.wy: 需圖形輸出，非純 stdout。
  - tree2.wy: 需圖形輸出，非純 stdout。

## Matrix

| runtime | group | version | status | total_median_s | per_example_median_s | startup_median_s | note |
|---|---|---|---|---:|---:|---:|---|
| cli[bun] | cli-js | 1.3.6 | ok | 2.518644 | 0.059968 | 0.043900 | - |
| cli[deno] | cli-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 2.604114 | 0.062003 | 0.046053 | - |
| cli[node] | cli-js | v22.19.0 | ok | 3.845735 | 0.091565 | 0.079694 | - |
| wywy[deno] | wywy-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 4.294254 | 0.102244 | 0.083869 | - |
| wenyan.py[py312] | wenyan.py | Python 3.12.12 | ok | 4.778081 | 0.113764 | 0.127075 | - |
| wenyan.py[py310] | wenyan.py | Python 3.10.19 | ok | 4.778838 | 0.113782 | 0.074348 | - |
| wenyan.py[py314] | wenyan.py | Python 3.14.3 | ok | 5.305193 | 0.126314 | 0.074956 | - |
| wenyan.py[py313] | wenyan.py | Python 3.13.12 | ok | 5.416928 | 0.128974 | 0.076110 | - |
| wenyan.py[py38] | wenyan.py | Python 3.8.20 | ok | 5.728758 | 0.136399 | 0.075056 | - |
| wywy[node] | wywy-js | v22.19.0 | ok | 5.903200 | 0.140552 | 0.137436 | - |
| wenyan.py[py313t] | wenyan.py | Python 3.13.12 | ok | 5.933199 | 0.141267 | 0.127752 | - |
| wenyan.py[py311] | wenyan.py | Python 3.11.14 | ok | 5.975168 | 0.142266 | 0.123994 | - |
| wenyan.py[py314t] | wenyan.py | Python 3.14.3 | ok | 6.288766 | 0.149733 | 0.124393 | - |
| wenyan.py[py39] | wenyan.py | Python 3.9.25 | ok | 6.417085 | 0.152788 | 0.075606 | - |
| wywy[bun] | wywy-js | 1.3.6 | ok | 7.071123 | 0.168360 | 0.138978 | - |
| wenyan.py[pypy310] | wenyan.py | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 9.711928 | 0.231236 | 0.181181 | - |
| wenyan.py[pypy38] | wenyan.py | Python 3.8.16 (a9dbdca6fc3286b0addd2240f11d97d8e8de187a, Dec 29 2022, 11:45:30) | ok | 9.786232 | 0.233006 | 0.127745 | - |
| wenyan.py[pypy39] | wenyan.py | Python 3.9.19 (a2113ea87262, Apr 21 2024, 05:41:07) | ok | 11.648222 | 0.277339 | 0.129740 | - |
| wenyan.py[graalpy312] | wenyan.py | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 25.737946 | 0.612808 | 0.373364 | - |
| wenyan.py[graalpy311] | wenyan.py | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 38.771152 | 0.923123 | 0.616240 | - |
| wenyan.py[graalpy310] | wenyan.py | GraalPy 3.10.13 (Oracle GraalVM Native 24.0.2) | ok | 40.582561 | 0.966251 | 0.717751 | - |
| wywy[py314] | wywy-python | Python 3.14.3 | ok | 73.936067 | 1.760383 | 0.237768 | - |
| wywy[py313] | wywy-python | Python 3.13.12 | ok | 80.447394 | 1.915414 | 0.288332 | - |
| wywy[py314t] | wywy-python | Python 3.14.3 | ok | 80.860682 | 1.925254 | 0.283634 | - |
| wywy[py311] | wywy-python | Python 3.11.14 | ok | 81.364244 | 1.937244 | 0.283425 | - |
| wywy[py312] | wywy-python | Python 3.12.12 | ok | 83.758949 | 1.994261 | 0.288416 | - |
| wywy[pypy310] | wywy-python | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 114.848246 | 2.734482 | 0.715068 | - |
| wywy[py313t] | wywy-python | Python 3.13.12 | ok | 117.524816 | 2.798210 | 0.394847 | - |
| wywy[pypy39] | wywy-python | Python 3.9.19 (a2113ea87262, Apr 21 2024, 05:41:07) | ok | 118.324983 | 2.817262 | 0.982705 | - |
| wywy[pypy38] | wywy-python | Python 3.8.16 (a9dbdca6fc3286b0addd2240f11d97d8e8de187a, Dec 29 2022, 11:45:30) | ok | 125.870512 | 2.996917 | 1.035251 | - |
| wywy[py310] | wywy-python | Python 3.10.19 | ok | 126.173237 | 3.004125 | 0.338011 | - |
| wywy[py38] | wywy-python | Python 3.8.20 | ok | 129.160844 | 3.075258 | 0.344439 | - |
| wywy[py39] | wywy-python | Python 3.9.25 | ok | 133.950480 | 3.189297 | 0.336388 | - |
| wywy[graalpy312] | wywy-python | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 165.547254 | 3.941601 | 1.910908 | - |
| wywy[graalpy311] | wywy-python | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 215.754198 | 5.137005 | 2.449378 | - |
| wywy[graalpy310] | wywy-python | GraalPy 3.10.13 (Oracle GraalVM Native 24.0.2) | ok | 325.741879 | 7.755759 | 3.053905 | - |

## Per-example Bar (lower is better)

| runtime | per_example_median_s | bar |
|---|---:|---|
| cli[bun] | 0.059968 | `#` |
| cli[deno] | 0.062003 | `#` |
| cli[node] | 0.091565 | `#` |
| wywy[deno] | 0.102244 | `#` |
| wenyan.py[py312] | 0.113764 | `#` |
| wenyan.py[py310] | 0.113782 | `#` |
| wenyan.py[py314] | 0.126314 | `#` |
| wenyan.py[py313] | 0.128974 | `#` |
| wenyan.py[py38] | 0.136399 | `#` |
| wywy[node] | 0.140552 | `#` |
| wenyan.py[py313t] | 0.141267 | `#` |
| wenyan.py[py311] | 0.142266 | `#` |
| wenyan.py[py314t] | 0.149733 | `#` |
| wenyan.py[py39] | 0.152788 | `#` |
| wywy[bun] | 0.168360 | `#` |
| wenyan.py[pypy310] | 0.231236 | `#` |
| wenyan.py[pypy38] | 0.233006 | `#` |
| wenyan.py[pypy39] | 0.277339 | `#` |
| wenyan.py[graalpy312] | 0.612808 | `##` |
| wenyan.py[graalpy311] | 0.923123 | `####` |
| wenyan.py[graalpy310] | 0.966251 | `####` |
| wywy[py314] | 1.760383 | `########` |
| wywy[py313] | 1.915414 | `########` |
| wywy[py314t] | 1.925254 | `########` |
| wywy[py311] | 1.937244 | `########` |
| wywy[py312] | 1.994261 | `#########` |
| wywy[pypy310] | 2.734482 | `############` |
| wywy[py313t] | 2.798210 | `############` |
| wywy[pypy39] | 2.817262 | `#############` |
| wywy[pypy38] | 2.996917 | `#############` |
| wywy[py310] | 3.004125 | `#############` |
| wywy[py38] | 3.075258 | `##############` |
| wywy[py39] | 3.189297 | `##############` |
| wywy[graalpy312] | 3.941601 | `##################` |
| wywy[graalpy311] | 5.137005 | `#######################` |
| wywy[graalpy310] | 7.755759 | `####################################` |
