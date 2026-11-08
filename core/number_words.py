"""Small English-number fallback when optional num2words is unavailable."""

SMALL = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)
TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
SCALES = (
    (10**15, "quadrillion"),
    (10**12, "trillion"),
    (10**9, "billion"),
    (10**6, "million"),
    (1000, "thousand"),
)


def integer_words(value: int) -> list[str]:
    if value < 20:
        return [SMALL[value]]
    if value < 100:
        return [TENS[value // 10]] + (integer_words(value % 10) if value % 10 else [])
    if value < 1000:
        return [SMALL[value // 100], "hundred"] + (
            ["and", *integer_words(value % 100)] if value % 100 else []
        )
    for scale, name in SCALES:
        if value >= scale:
            quotient, remainder = divmod(value, scale)
            tail = (
                (["and"] if remainder < 100 else []) + integer_words(remainder) if remainder else []
            )
            return [*integer_words(quotient), name, *tail]
    raise ValueError("Unsupported number")


def number_words(raw: str) -> list[str]:
    """Nonnegative tokens produced by pronunciation.normalize; bounded for safety."""
    integer, dot, fraction = raw.partition(".")
    if len(integer) > 18:
        return [raw]
    result = integer_words(int(integer))
    if dot and any(character != "0" for character in fraction):
        result.extend(["point", *(SMALL[int(character)] for character in fraction.rstrip("0"))])
    return result
