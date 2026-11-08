import pytest

from core import pronunciation


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("0", ["zero"]),
        ("3", ["three"]),
        ("12", ["twelve"]),
        ("42", ["forty", "two"]),
        ("101", ["one", "hundred", "and", "one"]),
        ("2000", ["two", "thousand"]),
        ("2.5", ["two", "point", "five"]),
    ],
)
def test_fallback_normalization(monkeypatch, raw, expected):
    monkeypatch.setattr(pronunciation, "num2words", None)
    assert pronunciation.normalize(raw) == expected
