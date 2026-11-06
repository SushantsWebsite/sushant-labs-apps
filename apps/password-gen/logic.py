"""Pure logic for Password Generator. No tkinter here so it can be unit-tested."""
import math
import secrets
import string

LOWER, UPPER, DIGITS = string.ascii_lowercase, string.ascii_uppercase, string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?"
AMBIGUOUS = "Il1O0o"


def pools(upper=True, lower=True, digits=True, symbols=True, avoid_ambiguous=False):
    """Return the enabled character sets, optionally without look-alike characters."""
    chosen = []
    for enabled, chars in ((lower, LOWER), (upper, UPPER), (digits, DIGITS), (symbols, SYMBOLS)):
        if enabled:
            if avoid_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS)
            chosen.append(chars)
    return chosen


def pool_size(upper=True, lower=True, digits=True, symbols=True, avoid_ambiguous=False) -> int:
    return len("".join(pools(upper, lower, digits, symbols, avoid_ambiguous)))


def generate(length=16, upper=True, lower=True, digits=True, symbols=True, avoid_ambiguous=False) -> str:
    """Generate a password using the OS CSPRNG, with at least one char from every enabled set."""
    sets = pools(upper, lower, digits, symbols, avoid_ambiguous)
    if not sets:
        raise ValueError("Select at least one character set")
    if length < len(sets):
        raise ValueError("Length is too short for the selected character sets")
    chars = [secrets.choice(s) for s in sets]
    everything = "".join(sets)
    chars += [secrets.choice(everything) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def entropy_bits(length: int, size: int) -> float:
    """Estimated entropy of a uniformly random password."""
    return length * math.log2(size) if size > 1 else 0.0


def strength_label(bits: float) -> str:
    if bits < 40:
        return "Weak"
    if bits < 60:
        return "Fair"
    if bits < 80:
        return "Strong"
    return "Excellent"
