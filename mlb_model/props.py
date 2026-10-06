"""Player props: a starter's strikeouts and a batter's chance to homer.

These are priced on their own, independent of the final score. That's fine across games, but in
a same-game parlay a homer and the Over are positively linked, so treat those combos as rougher.
"""
from __future__ import annotations

from math import exp, lgamma, log

from .model import League, Pitcher, starter_innings

LEAGUE_K_RATE = 0.22   # strikeouts per batter faced
LEAGUE_HR_RATE = 0.030  # homers per plate appearance
PA_BY_SLOT = {1: 4.65, 2: 4.55, 3: 4.45, 4: 4.35, 5: 4.25, 6: 4.1, 7: 4.0, 8: 3.9, 9: 3.8}


def _nb_at_least(n: int, mean: float, size: float) -> float:
    p = size / (size + mean)
    below = sum(exp(lgamma(k + size) - lgamma(size) - lgamma(k + 1) + size * log(p) + k * log(1 - p))
                for k in range(n))
    return 1 - below


def strikeout_mean(p: Pitcher, postseason: bool, opp_k_factor: float = 1.0) -> float:
    """Expected strikeouts today. opp_k_factor: opposing lineup's K% / league K% (1.0 = average)."""
    bf_per_ip = p.bf / p.ip if p.bf and p.ip else 2.95 + (p.whip if p.whip else 1.28)
    season_bf = p.bf or p.ip * bf_per_ip
    if p.k is None or not season_bf:
        rate = LEAGUE_K_RATE
    else:
        w = season_bf / (season_bf + 150)
        rate = w * p.k / season_bf + (1 - w) * LEAGUE_K_RATE
    return rate * opp_k_factor * starter_innings(p, postseason) * bf_per_ip


def strikeout_over(line: float, mean: float) -> float:
    """P(more strikeouts than the line). Size 15: a little wider than Poisson, since how long
    he stays in the game is uncertain too."""
    return _nb_at_least(int(line) + 1, mean, 15)


def homer_prob(hr: int, pa: int, slot: int = 5, pitcher_hr_factor: float = 1.0,
               park: float = 1.0) -> float:
    """P(at least one HR today). pitcher_hr_factor: the starter's HR/9 vs league (0.8 = stingy)."""
    w = pa / (pa + 200)
    rate = (w * hr / pa + (1 - w) * LEAGUE_HR_RATE) * pitcher_hr_factor * park
    return 1 - (1 - rate) ** PA_BY_SLOT.get(slot, 4.2)


def pitcher_hr_factor(p: Pitcher, lg: League) -> float:
    if p.hr is None or not p.ip:
        return 1.0
    w = p.ip / (p.ip + 100)
    return w * (p.hr * 9 / p.ip) / lg.hr9 + (1 - w)
