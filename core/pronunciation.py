"""Word-level comparison between a target sentence and a speech transcript.

The score is an APPROXIMATION based on speech-recognition accuracy, not a
phoneme-level pronunciation assessment.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Literal

try:
    from num2words import num2words
except ImportError:  # pragma: no cover
    num2words = None  # type: ignore[assignment]

Status = Literal["correct", "missed", "substituted", "extra"]

CONTRACTIONS: dict[str, str] = {
    "i'm": "i am", "you're": "you are", "we're": "we are", "they're": "they are",
    "he's": "he is", "she's": "she is", "it's": "it is", "that's": "that is",
    "there's": "there is", "what's": "what is", "let's": "let us",
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "isn't": "is not", "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
    "can't": "can not", "cannot": "can not", "won't": "will not", "wouldn't": "would not",
    "shouldn't": "should not", "couldn't": "could not",
    "i'll": "i will", "you'll": "you will", "we'll": "we will", "they'll": "they will",
    "i'd": "i would", "we'd": "we would", "you'd": "you would",
    "i've": "i have", "we've": "we have", "you've": "you have", "they've": "they have",
}

_TOKEN_RE = re.compile(r"[a-z]+(?:'[a-z]+)?|\d+(?:\.\d+)?")


@dataclass(frozen=True)
class Token:
    """One aligned word. `heard` is what the recognizer heard (None if missed)."""

    word: str
    status: Status
    heard: str | None = None


def _number_to_words(raw: str) -> list[str]:
    if num2words is None:
        from core.number_words import number_words

        return number_words(raw)
    try:
        value: float | int = float(raw) if "." in raw else int(raw)
        words = num2words(value)
    except (ValueError, OverflowError, NotImplementedError):
        return [raw]
    words = words.replace("-", " ").replace(",", " ")
    return words.split()


def normalize(text: str) -> list[str]:
    """Lowercase, expand contractions and numbers, strip punctuation, return tokens."""
    if not text:
        return []
    text = text.lower()
    text = text.replace("\u2019", "'").replace("\u2018", "'").replace("`", "'")
    text = re.sub(r"(?<=\d),(?=\d)", "", text)  # 2,000 -> 2000
    text = text.replace("%", " percent ")
    tokens: list[str] = []
    for tok in _TOKEN_RE.findall(text):
        if tok in CONTRACTIONS:
            tokens.extend(CONTRACTIONS[tok].split())
        elif tok[0].isdigit():
            tokens.extend(_number_to_words(tok))
        else:
            tokens.append(tok)
    return tokens


def align(target: str, transcript: str) -> list[Token]:
    """Align target words with transcript words using difflib."""
    t_words = normalize(target)
    h_words = normalize(transcript)
    matcher = difflib.SequenceMatcher(a=t_words, b=h_words, autojunk=False)
    result: list[Token] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            result.extend(Token(w, "correct", w) for w in t_words[i1:i2])
        elif tag == "delete":
            result.extend(Token(w, "missed", None) for w in t_words[i1:i2])
        elif tag == "insert":
            result.extend(Token(w, "extra", w) for w in h_words[j1:j2])
        else:  # replace
            target_part, heard_part = t_words[i1:i2], h_words[j1:j2]
            for k, word in enumerate(target_part):
                if k < len(heard_part):
                    result.append(Token(word, "substituted", heard_part[k]))
                else:
                    result.append(Token(word, "missed", None))
            result.extend(Token(w, "extra", w) for w in heard_part[len(target_part):])
    return result


def score(tokens: list[Token]) -> int:
    """Percentage of target words recognized correctly (0-100)."""
    target_tokens = [t for t in tokens if t.status != "extra"]
    if not target_tokens:
        return 0
    correct = sum(1 for t in target_tokens if t.status == "correct")
    return round(100 * correct / len(target_tokens))


def summarize(tokens: list[Token]) -> dict[str, list]:
    """Compact summary for prompts: missed words and (target, heard) substitutions."""
    return {
        "missed": [t.word for t in tokens if t.status == "missed"],
        "substituted": [[t.word, t.heard] for t in tokens if t.status == "substituted"],
        "extra": [t.word for t in tokens if t.status == "extra"],
    }


def evaluate(target: str, transcript: str) -> tuple[list[Token], int]:
    """Convenience helper: align and score in one call."""
    tokens = align(target, transcript)
    return tokens, score(tokens)
