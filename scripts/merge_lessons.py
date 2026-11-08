"""Merge supplied lesson batches without changing lesson content."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def merge_lessons(source: Path, output: Path) -> list[dict]:
    lessons = []
    for path in sorted(source.glob("lessons_*.json")):
        batch = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(batch, list):
            raise ValueError(f"{path}: expected a JSON list")
        lessons.extend(batch)
    days = [lesson["day"] for lesson in lessons]
    if any(type(day) is not int for day in days) or sorted(days) != list(range(1, 31)):
        raise ValueError("Expected exactly days 1–30, with no duplicates or gaps")
    lessons.sort(key=lambda lesson: lesson["day"])
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(lessons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return lessons


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data/import")
    parser.add_argument("--output", type=Path, default=ROOT / "data/daily_lessons.json")
    args = parser.parse_args()
    try:
        lessons = merge_lessons(args.source, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Merge failed: {error}\n")
    print(f"Merged {len(lessons)} lessons into {args.output}")


if __name__ == "__main__":
    main()
