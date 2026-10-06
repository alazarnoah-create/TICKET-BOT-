"""Odds math: American <-> decimal, implied probability, removing the vig, EV and Kelly sizing."""
from __future__ import annotations


def to_decimal(american: float) -> float:
    """-150 -> 1.667, +200 -> 3.0 (what $1 returns, stake included)."""
    if american == 0:
        raise ValueError("American odds can't be 0")
    return 1 + (american / 100 if american > 0 else 100 / -american)


def to_american(decimal: float) -> int:
    if decimal <= 1:
        raise ValueError("decimal odds must be above 1")
    return round((decimal - 1) * 100) if decimal >= 2 else round(-100 / (decimal - 1))


def implied(american: float) -> float:
    """The win probability the price implies, vig included."""
    return 1 / to_decimal(american)


def no_vig(*americans: float) -> list[float]:
    """Fair probabilities for a two- (or more-) way market: scale the implied ones to sum to 1."""
    raw = [implied(a) for a in americans]
    return [p / sum(raw) for p in raw]


def ev(prob: float, american: float, push: float = 0.0) -> float:
    """Expected profit per $1 staked."""
    return prob * (to_decimal(american) - 1) - (1 - prob - push)


def kelly(prob: float, american: float, fraction: float = 0.25, cap: float = 0.05) -> float:
    """Share of bankroll to stake. Quarter Kelly by default, capped at 5%: full Kelly assumes
    the model's probabilities are exact, which they never are."""
    b = to_decimal(american) - 1
    full = (b * prob - (1 - prob)) / b
    return max(0.0, min(cap, full * fraction))
