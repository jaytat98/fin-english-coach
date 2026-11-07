from core.patterns import (
    _RAW,
    CATEGORIES,
    PATTERNS,
    category_of,
    is_valid_key,
    label_ko,
    pressure_point_for,
)


def test_count_and_uniqueness():
    assert len(PATTERNS) >= 40
    assert len(_RAW) == len(PATTERNS)


def test_categories_and_fields():
    for p in PATTERNS.values():
        assert p.category in CATEGORIES
        for value in (p.label_ko, p.label_en, p.description_ko, p.example_wrong, p.example_right):
            assert value.strip()


def test_every_category_used():
    assert {p.category for p in PATTERNS.values()} == set(CATEGORIES)


def test_key_validation():
    assert is_valid_key("preposition:until_vs_by")
    assert is_valid_key("other:double_negative")
    assert not is_valid_key("random")
    assert not is_valid_key("other:")


def test_helpers():
    assert category_of("konglish:claim") == "konglish"
    assert category_of("other:x_y") == "grammar_other"
    assert label_ko("other:double_negative") == "double negative"
    assert "politely" in pressure_point_for("politeness:blunt_no")