#!/usr/bin/env python3
from __future__ import annotations

"""Run self-hosted interpreter entrypoint as a standalone Python script.

Usage:
    python scripts/wywy_runner.py wenyan.wy examples/helloworld.wy
"""

import sys
from pathlib import Path

# Keep repository root first so `import wenyan` resolves local `wenyan.py`
# rather than an installed package in site-packages.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wenyan import 自舉主術


if __name__ == "__main__":
    if sys.argv:
        sys.argv[0] = "wywy"
    raise SystemExit(自舉主術())
