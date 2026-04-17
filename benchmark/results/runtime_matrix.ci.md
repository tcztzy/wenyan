# Wenyan Runtime Benchmark

- generated_at_utc: `2026-04-04T09:34:49+00:00`
- benchmark_examples: `5`
- full_rounds: `1`
- startup_probe_rounds: `3`

## Matrix

| runtime | group | version | status | total_median_s | per_example_median_s | startup_median_s | note |
|---|---|---|---|---:|---:|---:|---|
| cli[node] | cli-js | v25.6.1 | ok | 0.385021 | 0.077004 | 0.076638 | - |
| cli[bun] | cli-js | 1.3.11 | ok | 0.398144 | 0.079629 | 0.040474 | - |
| wenyan.py[py310] | wenyan.py | Python 3.10.20 | ok | 0.434224 | 0.086845 | 0.075579 | - |
| wenyan.py[py311] | wenyan.py | Python 3.11.15 | ok | 0.437440 | 0.087488 | 0.076208 | - |
| wenyan.py[py314] | wenyan.py | Python 3.14.3 | ok | 0.437766 | 0.087553 | 0.074066 | - |
| wenyan.py[py312] | wenyan.py | Python 3.12.13 | ok | 0.479830 | 0.095966 | 0.074430 | - |
| wenyan.py[py313] | wenyan.py | Python 3.13.12 | ok | 0.540106 | 0.108021 | 0.075694 | - |
| wywy[deno] | wywy-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 0.596371 | 0.119274 | 0.132778 | - |
| wywy[node] | wywy-js | v25.6.1 | ok | 0.646226 | 0.129245 | 0.129509 | - |
| wywy[bun] | wywy-js | 1.3.11 | ok | 0.796085 | 0.159217 | 0.177794 | - |
| wenyan.py[pypy310] | wenyan.py | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 0.857713 | 0.171543 | 0.132216 | - |
| cli[deno] | cli-js | deno 2.2.4 (stable, release, aarch64-apple-darwin) | ok | 0.883945 | 0.176789 | 0.076107 | - |
| wywy[py314] | wywy-python | Python 3.14.3 | ok | 1.517135 | 0.303427 | 0.291068 | - |
| wywy[py313] | wywy-python | Python 3.13.12 | ok | 1.518782 | 0.303756 | 0.287273 | - |
| wywy[py311] | wywy-python | Python 3.11.15 | ok | 1.582797 | 0.316559 | 0.294935 | - |
| wywy[py312] | wywy-python | Python 3.12.13 | ok | 1.664705 | 0.332941 | 0.293276 | - |
| wywy[py310] | wywy-python | Python 3.10.20 | ok | 1.876579 | 0.375316 | 0.345027 | - |
| wenyan.py[graalpy312] | wenyan.py | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 3.114169 | 0.622834 | 0.448303 | - |
| wenyan.py[graalpy311] | wenyan.py | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 3.322712 | 0.664542 | 0.507558 | - |
| wenyan.py[graalpy310] | wenyan.py | GraalPy 3.10.13 (Oracle GraalVM Native 24.0.2) | ok | 3.422197 | 0.684439 | 0.557978 | - |
| wywy[pypy310] | wywy-python | Python 3.10.16 (64367dfeb263, Feb 24 2025, 17:31:22) | ok | 4.539711 | 0.907942 | 0.834105 | - |
| wywy[graalpy311] | wywy-python | GraalPy 3.11.7 (Oracle GraalVM Native 24.2.2) | ok | 13.314049 | 2.662810 | 2.361229 | - |
| wywy[graalpy310] | wywy-python | GraalPy 3.10.13 (Oracle GraalVM Native 24.0.2) | ok | 13.462634 | 2.692527 | 2.491974 | - |
| wywy[graalpy312] | wywy-python | GraalPy 3.12.8 (Oracle GraalVM Native 25.0.2) | ok | 13.598035 | 2.719607 | 2.255652 | - |

## Per-example Bar (lower is better)

| runtime | per_example_median_s | bar |
|---|---:|---|
| cli[node] | 0.077004 | `#` |
| cli[bun] | 0.079629 | `#` |
| wenyan.py[py310] | 0.086845 | `#` |
| wenyan.py[py311] | 0.087488 | `#` |
| wenyan.py[py314] | 0.087553 | `#` |
| wenyan.py[py312] | 0.095966 | `#` |
| wenyan.py[py313] | 0.108021 | `#` |
| wywy[deno] | 0.119274 | `#` |
| wywy[node] | 0.129245 | `#` |
| wywy[bun] | 0.159217 | `##` |
| wenyan.py[pypy310] | 0.171543 | `##` |
| cli[deno] | 0.176789 | `##` |
| wywy[py314] | 0.303427 | `####` |
| wywy[py313] | 0.303756 | `####` |
| wywy[py311] | 0.316559 | `####` |
| wywy[py312] | 0.332941 | `####` |
| wywy[py310] | 0.375316 | `####` |
| wenyan.py[graalpy312] | 0.622834 | `########` |
| wenyan.py[graalpy311] | 0.664542 | `########` |
| wenyan.py[graalpy310] | 0.684439 | `#########` |
| wywy[pypy310] | 0.907942 | `############` |
| wywy[graalpy311] | 2.662810 | `###################################` |
| wywy[graalpy310] | 2.692527 | `###################################` |
| wywy[graalpy312] | 2.719607 | `####################################` |
