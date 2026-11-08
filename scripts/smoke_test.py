"""Run Streamlit integration tests without external AI calls."""

from pathlib import Path

import pytest

if __name__ == "__main__":
    raise SystemExit(
        pytest.main([str(Path(__file__).resolve().parents[1] / "tests/test_smoke.py"), "-q"])
    )
