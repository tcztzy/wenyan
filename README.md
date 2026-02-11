Wenyan Programming Language in Python
=====================================

Benchmark
---------

Run the runtime matrix benchmark (examples as dataset):

```bash
uv run python scripts/benchmark_runtime_matrix.py
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
