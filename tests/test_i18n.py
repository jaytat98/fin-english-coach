import string

from core.i18n import STRINGS, t


def test_required_languages_and_placeholders():
    for key, values in STRINGS.items():
        assert len(values) >= 2 and all(values), key
        if key.startswith(("roadmap.", "admin.")) or key in ("roadmap", "admin"):
            assert len(values) == 3, key
        fields = [
            {name for _, name, _, _ in string.Formatter().parse(value) if name} for value in values
        ]
        assert all(item == fields[0] for item in fields), key


def test_vietnamese_falls_back_to_english():
    assert t("today", "vi") == t("today", "en")
    assert t("roadmap", "vi") != t("roadmap", "en")
