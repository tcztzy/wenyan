# Wenyan Compiler Pipeline Benchmark (examples/*.wy)

- generated_at_utc: `2026-06-17T14:40:54+00:00`
- python: `3.12.13 (main, Mar 25 2026, 03:16:06) [Clang 22.1.1 ]`
- wenyan.py: `0.1.0`
- samples: `3`
- min_time_s: `0.05`
- skipped_examples:
  - clock.wy: 需圖形/DOM 環境，非純 stdout。
  - tree.wy: 需圖形輸出，非純 stdout。
  - tree2.wy: 需圖形輸出，非純 stdout。

## Cases (lower is better)

| case | status | median_total_s | median_per_example_s | note |
|---|---|---:|---:|---|
| lexer | ok | 0.007115 | 0.000165 | - |
| parser | ok | 0.013981 | 0.000325 | - |
| preprocess | ok | 0.104150 | 0.002422 | - |
| compile_ast | ok | 0.785492 | 0.018267 | - |
| compile_code | ok | 0.903726 | 0.021017 | - |
