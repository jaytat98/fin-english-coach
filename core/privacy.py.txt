"""Heuristic detector for likely sensitive content (names, amounts, contacts).

This is a helper, not a guarantee. It warns users before AI generation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<![\d,.])\+?\d[\d\s().-]{8,}\d(?![\d,.])")
LONG_DIGITS_RE = re.compile(r"\d{7,}")
AMOUNT_RE = re.compile(
    r"(?:VND|KRW|USD|US\$|\$|₫)\s?\d[\d,.]*"
    r"|\d[\d,.]*\s?(?:VND|KRW|USD|đồng|₫|원|억|만|tỷ|triệu|billion|million|bn)",
    re.IGNORECASE,
)
ENTITY_RE = re.compile(
    r"\bCo\.?,?\s*Ltd\.?(?![A-Za-z])|\bLtd\.?(?![A-Za-z])|\bJSC\b|\bLLC\b|\bInc\.?(?![A-Za-z])"
    r"|\bCorp\.?(?![A-Za-z])|\bCorporation\b|\bPLC\b|\bGmbH\b"
    r"|주식회사|\(주\)|㈜|Công\s+ty|TNHH|Cổ\s+phần",
    re.IGNORECASE,
)
CAPITALIZED_SEQ_RE = re.compile(r"\b[A-Z][A-Za-z&'-]+(?:\s+[A-Z][A-Za-z&'-]+)+")

MIN_AMOUNT_DIGITS = 5  # "약 10억 원" is fine; "VND 4,215,300,000" is flagged

_COMMON_CAPITALIZED = {
    "i", "the", "a", "an", "and", "of", "for", "to", "in", "on", "at", "we", "our",
    "chief", "financial", "officer", "accountant", "accounting", "finance", "manager",
    "director", "head", "senior", "associate", "partner", "team", "tax", "audit",
    "deals", "advisory", "hq", "headquarters", "cfo", "ceo", "coo", "vat", "fct", "cit",
    "korea", "korean", "vietnam", "vietnamese", "hanoi", "ho", "chi", "minh", "city",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "mr", "ms", "mrs", "dear", "hi",
    "hello", "thanks", "regards", "ifrs", "k-ifrs", "vas", "ebitda", "spa", "nda",
    "board", "steering", "committee", "client", "company", "group",
}


@dataclass(frozen=True)
class Finding:
    """One suspicious fragment."""

    kind: str  # email | phone | long_number | amount | legal_entity | possible_name
    text: str


def _digit_count(s: str) -> int:
    return sum(ch.isdigit() for ch in s)


def detect_sensitive(text: str) -> list[Finding]:
    """Return suspicious fragments (deduplicated, in order of discovery)."""
    if not text:
        return []
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: str, fragment: str) -> None:
        key = (kind, fragment.strip())
        if key not in seen:
            seen.add(key)
            findings.append(Finding(kind, fragment.strip()))

    for m in EMAIL_RE.finditer(text):
        add("email", m.group())
    for m in PHONE_RE.finditer(text):
        if 9 <= _digit_count(m.group()) <= 13:
            add("phone", m.group())
    for m in AMOUNT_RE.finditer(text):
        if _digit_count(m.group()) >= MIN_AMOUNT_DIGITS:
            add("amount", m.group())
    for m in LONG_DIGITS_RE.finditer(text):
        if not any(m.group() in f.text.replace(",", "").replace(".", "") for f in findings):
            add("long_number", m.group())
    for m in ENTITY_RE.finditer(text):
        add("legal_entity", m.group())
    for m in CAPITALIZED_SEQ_RE.finditer(text):
        words = [w.strip("'").lower() for w in m.group().split()]
        if sum(1 for w in words if w not in _COMMON_CAPITALIZED) >= 2:
            add("possible_name", m.group())
    return findings


def has_sensitive(text: str) -> bool:
    return bool(detect_sensitive(text))