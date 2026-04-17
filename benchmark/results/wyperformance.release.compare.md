# Wenyan Compiler Benchmark Compare

- baseline: `benchmark/results/wyperformance.release.json`
- contender: `benchmark/results/wyperformance.release.v2.json`
- baseline_profile: `release`
- contender_profile: `release`
- excluded_benchmarks: `compile_code`

## Notes

- compile_code benchmark definition changed in release.v2 and now measures only Python compile().
- Use lexer_only, parse_total, preprocess_total, compile_ast, and compile_total for historical comparison.

## Cases

| benchmark | baseline_mean_s | contender_mean_s | change | significance |
|---|---:|---:|---:|---|
| `compile_ast` | 0.285307 | 0.396535 | 1.39x slower | Significant (t=-13.98) |
| `compile_total` | 0.346109 | 0.433514 | 1.25x slower | Significant (t=-7.06) |
| `lexer_only` | 0.001505 | 0.001452 | 1.04x faster | Significant (t=3.50) |
| `parse_total` | 0.003116 | 0.002910 | 1.07x faster | Significant (t=2.73) |
| `preprocess_total` | 0.036924 | 0.048240 | 1.31x slower | Significant (t=-6.02) |

- geometric_mean_ratio: `1.15x slower`
