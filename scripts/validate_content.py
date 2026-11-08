"""Validate supplied lesson and scenario content against HANDOFF requirements."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.content import validate_files  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    try:
        lessons, scenarios = validate_files(args.data_dir)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Validation failed: {error}\n")
    print(f"Validated {lessons} lessons and {scenarios} scenarios (HANDOFF checks).")


if __name__ == "__main__":
    main()
