Wenyan Programming Language in Python
=====================================

Benchmark
---------

Run the pyperf/pyperformance-style Wenyan benchmark suite:

```bash
uv run python scripts/wyperformance.py run
```

List benchmarks and groups:

```bash
uv run python scripts/wyperformance.py list
uv run python scripts/wyperformance.py list_groups
```

Run only selected benchmarks (supports include/exclude):

```bash
uv run python scripts/wyperformance.py run --benchmarks compiler,-compile_code
```

Compare two result JSON files (normal or table style):

```bash
uv run python scripts/wyperformance.py compare base.json changed.json
uv run python scripts/wyperformance.py compare base.json changed.json -O table
```

Default output:

- `benchmark/results/wyperformance.json`

Run the runtime matrix benchmark (examples as dataset):

```bash
uv run python scripts/benchmark_runtime_matrix.py
```

Run the compiler pipeline microbench (lexer/parser/compiler on examples as dataset):

```bash
uv run python scripts/benchmark_compiler_pipeline.py run
```

Quick/smoke mode (fewer samples, shorter min-time):

```bash
uv run python scripts/benchmark_compiler_pipeline.py run --quick
```

Compare two benchmark JSON results (similar to `pyperformance compare`):

```bash
uv run python scripts/benchmark_compiler_pipeline.py compare \
  benchmark/results/compiler_pipeline_benchmark.json \
  /path/to/other/compiler_pipeline_benchmark.json
```

Include free-threading builds and use 100 startup probe runs:

```bash
uv run python scripts/benchmark_runtime_matrix.py --include-free-threading --startup-rounds 100
```

Outputs:

- `benchmark/results/examples_runtime_benchmark.json`
- `benchmark/results/examples_runtime_benchmark.csv`
- `benchmark/results/examples_runtime_benchmark.md`

`examples_runtime_benchmark.md` is formatted for direct embedding into README
as a table/chart-like summary.
