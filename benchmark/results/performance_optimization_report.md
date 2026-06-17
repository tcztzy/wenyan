# Wenyan.py Performance Optimization Report

Date: 2026-06-17

## Goal

Optimize Wenyan.py runtime performance with a profile-first loop, evaluate JIT/AOT options, and keep Python 3.10+ plus zero runtime dependency constraints intact.

## Environment

- Host: macOS 26.5.1 arm64, Darwin 25.5.0
- Primary benchmark Python: CPython 3.12.13
- Baseline: clean `HEAD` archive at `/tmp/wenyan-baseline.iPdu8G`
- Contender: current working tree
- Runtime dependency policy: unchanged `[project] dependencies = []`
- Optional dev dependency added: `llvmlite>=0.47.0` for `--jit=llvm` development/testing only

## Profiling And Optimization Loop

### Loop 1: Runtime Matrix And JIT Coverage

Command:

```bash
/Users/tcztzy/GitHub/wenyan.py/.venv/bin/python scripts/benchmark_runtime_matrix.py run \
  --profile ci --rounds 1 --startup-rounds 1 --timeout 60 \
  --no-cli-setup --no-install-missing-python \
  --result-json /tmp/wenyan-current-runtime-matrix.json \
  --result-csv /tmp/wenyan-current-runtime-matrix.csv \
  --result-md /tmp/wenyan-current-runtime-matrix.md
```

Finding: `--jit` now has measurable benefit on runtimes where repeated full-program execution cost dominates. CI workload, 5 programs:

| Engine | Non-JIT total | JIT total | Speedup |
|---|---:|---:|---:|
| py310 | 0.481612s | 0.439045s | 1.10x |
| py311 | 0.419163s | 0.418818s | 1.00x |
| py312 | 0.447267s | 0.444746s | 1.01x |
| py313 | 0.560757s | 0.449846s | 1.25x |
| py314 | 0.449786s | 0.444589s | 1.01x |
| pypy310 | 0.948098s | 0.655080s | 1.45x |
| graalpy311 | 3.251212s | 2.214016s | 1.47x |
| graalpy312 | 2.890307s | 1.755177s | 1.65x |

Optimization applied in current tree:

- Expanded the optional LLVM JIT integer subset beyond single arithmetic return forms.
- Added `wenyan.py[jit-*]` runtime-matrix targets so JIT is measured next to normal execution.
- Kept LLVM as optional: missing backend or unsupported code silently falls back.

### Loop 2: Correctness And Native Lifetime Regression

Profile/test evidence:

```bash
PYTHONFAULTHANDLER=1 uv run python -m unittest \
  tests.test_runtime_features.執行測試.test_LLVM_JIT夫句與減法鏈 \
  tests.test_runtime_features.執行測試.test_LLVM_JIT支援三句算術鏈 \
  tests.test_runtime_features.執行測試.test_LLVM_JIT支援乘除取餘 \
  tests.test_runtime_features.執行測試.test_LLVM_JIT支援多語句函數體 -v
```

Finding: llvmlite execution engines stored only in a generated exec namespace could be garbage-collected later, and their `_dispose` path segfaulted during a later AST parse.

Fix:

- Store LLVM backend state and compiled `(engine, module, ctypes function)` references in process-level `builtins.__wenyan_llvm_state__`.
- Preserve native fast-path integer guards after a function has already been compiled, so oversized Python integers still run through the Python fallback path.
- Backpropagated the invariant as `SPEC.md` `V30` and bug row `B2`.

Regression tests added:

- `test_LLVM_JIT引擎跨作用域回收不崩潰`
- `test_LLVM_JIT已編譯快路仍守衛超界整數`

### Loop 3: Compiler Pipeline Guardrail

Commands:

```bash
/Users/tcztzy/GitHub/wenyan.py/.venv/bin/python scripts/wyperformance.py run \
  --profile ci \
  --output /tmp/wenyan-current-wyperf-ci-py312.json \
  --summary-md /tmp/wenyan-current-wyperf-ci-py312.md

/Users/tcztzy/GitHub/wenyan.py/.venv/bin/python scripts/wyperformance.py compare \
  /tmp/wenyan-baseline-wyperf-ci-py312.json \
  /tmp/wenyan-current-wyperf-ci-py312.json --output-style table
```

Result: no significant compiler-pipeline regression on the non-fast CI run.

| Benchmark | Baseline | Current | Change |
|---|---:|---:|---:|
| preprocess_total | 0.000542s | 0.000542s | 1.00x slower |
| lexer_only | 0.000197s | 0.000195s | 1.01x faster |
| parse_total | 0.000369s | 0.000370s | 1.00x slower |
| compile_ast | 0.027067s | 0.027349s | 1.01x slower |
| compile_code | 0.006141s | 0.006272s | 1.02x slower |
| compile_total | 0.034603s | 0.034568s | 1.00x faster |

### Loop 4: Hotspot Profile

Commands:

```bash
/Users/tcztzy/GitHub/wenyan.py/.venv/bin/python -m cProfile \
  -o /tmp/wenyan-current-compile-ast.prof \
  scripts/wyperformance.py run --profile ci --fast --benchmarks compile_ast \
  --output /tmp/wenyan-current-profile-compile-ast.json \
  --summary-md /tmp/wenyan-current-profile-compile-ast.md

/Users/tcztzy/GitHub/wenyan.py/.venv/bin/python -m cProfile \
  -o /tmp/wenyan-current-runtime-jit.prof \
  wenyan.py --jit --no-outputHanzi \
  benchmark/workloads/synthetic/macro_heavy/macro_heavy_s.wy
```

Top `compile_ast` cumulative hotspots:

- `wenyan.py:_補齊AST位置`: 0.543s cumulative in profile run
- `ast.iter_child_nodes`: 0.297s cumulative
- `wenyan.py:_造輸出格式函`: 0.215s cumulative
- `wenyan.py:_標注AST子樹`: 0.347s cumulative

Runtime cProfile for the small JIT workload is dominated by interpreter startup/import/dataclass setup. That matches the matrix result: `--jit` is most valuable for longer or slower host runtimes, while tiny CPython workloads remain startup-bound.

## AOT Evaluation

Native AOT was not added. Shipping generated native artifacts or a required native compiler would conflict with the current zero runtime dependency and simple distribution constraints. The practical AOT-compatible path remains:

- existing persistent Python code cache for compiled source;
- `wywy`/self-hosted path reusing host code cache with fresh execution scope;
- future optional AOT experiment can emit Python bytecode/cache artifacts, not required runtime native binaries.

## Summary

- LLVM JIT path is now broader and benchmarked in the runtime matrix.
- CI runtime matrix shows up to 1.65x speedup on GraalPy 3.12 and 1.45x on PyPy 3.10; CPython 3.11/3.12 is effectively neutral on the small CI workload.
- Compiler pipeline is guarded against regression; current vs clean `HEAD` is statistically neutral on the non-fast CI benchmark.
- Native JIT lifetime and oversized-int guard bugs were fixed and specified.

## Verification

Passed:

```bash
uv run ruff check .
uv run ruff format --check .
uv run python -m unittest discover -s tests -p 'test_*.py'
uv run python -m unittest tests.test_runtime_features
```

Full unittest result: 189 tests passed in 216.476s. `tests.test_runtime_features` was rerun after formatting and passed 55 tests in 0.857s.

Not completed:

```bash
uv run python scripts/check_line_coverage.py --source wenyan.py --fail-under 100 --quiet
```

This was interrupted after several minutes. Under stdlib `trace`, the run was still inside the full unittest suite, amplified by `Path.resolve()` in the trace callback while compiling `wenyan.wy` for bootstrap tests.

## Remaining Risk

- `wywy` fails the current synthetic `macro_heavy_s.wy` runtime matrix target with `文法之禍：句首非關鍵`; this predates the JIT comparison and should be handled as a separate self-hosted parser compatibility task.
- LLVM JIT currently targets a guarded integer subset; unsupported forms must continue to fall back silently.
- Compile-time hotspots are still AST location propagation and generated output-format function construction. Further optimization should target those only with separate failing/perf tests because they affect all compile paths.
