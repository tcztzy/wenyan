Wenyan Programming Language in Python
=====================================

Wenyan.py is a Python implementation of the Wenyan programming language. It is
packaged as a small, zero-runtime-dependency interpreter/compiler module and
ships two command line entry points:

- `wenyan`: run Wenyan programs through the Python implementation.
- `wywy`: run through the self-hosted `wenyan.wy` path.

Wenyan is also a good fit for token-efficient agent workflows: the syntax is
compact, readable to humans who know classical Chinese, and close to the
language this project implements.

Installation
------------

Install the released CLI tools into uv's user tool directory:

```bash
uv tool install wenyan
```

For a local checkout, install the current tree the same way:

```bash
uv tool install .
```

You can also install into an active Python environment:

```bash
python -m pip install wenyan
```

Quick Start
-----------

Create a small Wenyan program:

```wenyan
吾有一數。曰三。書之。
```

Save it as `hello.wy`, then run:

```bash
wenyan hello.wy
```

Expected output:

```text
3
```

Run the self-hosted path:

```bash
wywy hello.wy
```

From a checkout, you can run without installing:

```bash
uv run wenyan.py examples/helloworld.wy
uv run wenyan.py --help
```

Importing Wenyan Modules from Python
------------------------------------

Importing `wenyan` installs a Python import hook for `.wy` files. A standalone
`foo.wy` can be imported as `foo`, and a Python package can enable Wenyan
submodules from its `__init__.py`:

```python
# pkg/__init__.py
import wenyan

from .core import answer
```

```wenyan
批曰。「「pkg/core.wy」」。
吾有一數。曰四十二。名之曰「answer」。
```

Then Python can import the package and its Wenyan submodule normally:

```python
import pkg
import pkg.core

assert pkg.answer == 42
assert pkg.core.answer == 42
```

Wenyan package init files are also supported with `序.wy`.

Token Efficiency
----------------

Recommended companion projects:

- [wenyanwen-skill](https://github.com/voidborne-d/wenyanwen-skill): an AI
  skill that asks the agent to answer in compact Wenyan-style Chinese, then
  translates locally back to modern Chinese.
- [caveman](https://github.com/JuliusBrussee/caveman): a token-compression
  skill for terse English agent output.

Both projects share the same practical goal: spend fewer output tokens while
keeping enough meaning for humans and tools.

Benchmarks
----------

Performance data is kept for regression checks, but the README only lists the
entry points. Generated reports and charts live under `benchmark/results/`.

Run the Wenyan benchmark suite:

```bash
uv run python scripts/wyperformance.py run
```

Run the quick profile or inspect workloads:

```bash
uv run python scripts/wyperformance.py run --profile ci
uv run python scripts/wyperformance.py list_workloads
```

Compare two result files:

```bash
uv run python scripts/wyperformance.py compare base.json changed.json
```

Run the runtime matrix:

```bash
uv run python scripts/benchmark_runtime_matrix.py
uv run python scripts/benchmark_runtime_matrix.py --profile ci
```

Generate SVG charts through Wenyan + matplotlib:

```bash
uv run --with matplotlib wenyan.py benchmark/charts/compiler_summary.wy
uv run --with matplotlib wenyan.py benchmark/charts/runtime_matrix_summary.wy
```
