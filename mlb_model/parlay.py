"""Bets ("legs") and parlays, priced with the model.

Legs from the same game are priced together off that game's score distribution, so a same-game
parlay like "Dodgers ML + Under 6" gets its real joint probability, not a naive product.
Sportsbooks know about that correlation too: their same-game parlay price is usually worse than
the product of the leg prices shown here. Always check the price the book actually offers.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable

from .model import Game
from .odds import implied, to_american, to_decimal


@dataclass
class Leg:
    game: str  # which game; legs in one game share its score distribution
    market: str  # "ml", "rl", "total", or a prop key
    name: str
    odds: int  # American
    win: Callable | None = None  # (away_runs, home_runs) -> bool, for score-based legs
    push: Callable | None = None
    prob: float | None = None  # props: the model's probability, independent of the score

    def model_prob(self, games: dict[str, Game]) -> float:
        return self.prob if self.win is None else games[self.game].prob(self.win)

    def push_prob(self, games: dict[str, Game]) -> float:
        return 0.0 if self.push is None else games[self.game].prob(self.push)


def game_legs(label: str, away: str, home: str, odds: dict) -> list[Leg]:
    """Moneyline, run line and total legs from an odds dict:
    {"ml": {"away": -115, "home": -105},
     "run_line": {"away": [-1.5, 161], "home": [1.5, -196]},
     "total": {"line": 6, "over": -115, "under": -105}}"""
    legs = []
    ml = odds.get("ml") or {}
    if ml.get("away"):
        legs.append(Leg(label, "ml", f"{away} ML", ml["away"], lambda a, h: a > h))
    if ml.get("home"):
        legs.append(Leg(label, "ml", f"{home} ML", ml["home"], lambda a, h: h > a))
    for side, team in (("away", away), ("home", home)):
        spread, cost = (odds.get("run_line") or {}).get(side) or (None, None)
        if cost is None:
            continue
        sign = 1 if side == "away" else -1  # margin from this team's point of view
        legs.append(Leg(label, "rl", f"{team} {spread:+g}", cost,
                        lambda a, h, s=spread, g=sign: g * (a - h) + s > 0,
                        lambda a, h, s=spread, g=sign: g * (a - h) + s == 0))
    total = odds.get("total") or {}
    if total.get("line") is not None:
        line = total["line"]
        if total.get("over"):
            legs.append(Leg(label, "total", f"Over {line:g}", total["over"],
                            lambda a, h, t=line: a + h > t, lambda a, h, t=line: a + h == t))
        if total.get("under"):
            legs.append(Leg(label, "total", f"Under {line:g}", total["under"],
                            lambda a, h, t=line: a + h < t, lambda a, h, t=line: a + h == t))
    return legs


@dataclass
class Parlay:
    legs: tuple
    hit: float  # chance every leg wins
    payout: float  # decimal odds if the book simply multiplies the legs
    ev: float  # model's expected profit per $1 (pushes knock that leg out, as books do)

    @property
    def same_game(self) -> bool:
        return len({leg.game for leg in self.legs}) < len(self.legs)


def price(legs, games: dict[str, Game]) -> Parlay:
    hit = mult = payout = 1.0
    by_game: dict[str, list[Leg]] = {}
    for leg in legs:
        payout *= to_decimal(leg.odds)
        if leg.win is None:
            hit *= leg.prob
            mult *= leg.prob * to_decimal(leg.odds)
        else:
            by_game.setdefault(leg.game, []).append(leg)
    for name, game_legs_ in by_game.items():
        g_hit = g_mult = 0.0
        for (a, h), p in games[name].scores.items():
            x, clean = 1.0, True
            for leg in game_legs_:
                if leg.win(a, h):
                    x *= to_decimal(leg.odds)
                elif leg.push and leg.push(a, h):
                    clean = False  # leg is void; parlay pays on the rest
                else:
                    x, clean = 0.0, False
                    break
            g_hit += p if clean else 0.0
            g_mult += p * x
        hit *= g_hit
        mult *= g_mult
    return Parlay(tuple(legs), hit, payout, mult - 1)


def search(legs: list[Leg], games: dict[str, Game], target: float | None = None,
           min_legs: int = 2, max_legs: int = 6, top: int = 5) -> list[Parlay]:
    """Best parlays by model EV; with a target, only those paying 0.75x-1.5x of it."""
    found = []
    for n in range(min_legs, max_legs + 1):
        for combo in combinations(legs, n):
            keys = [(leg.game, "side" if leg.market in ("ml", "rl") else leg.market) for leg in combo]
            if len(set(keys)) < n:
                continue  # two bets on one market (both sides, ML + run line, over + under...)
            payout = 1.0
            for leg in combo:
                payout *= to_decimal(leg.odds)
            if target and not 0.75 * target <= payout <= 1.5 * target:
                continue
            p = price(combo, games)
            if p.hit > 0:
                found.append(p)
    found.sort(key=lambda p: p.ev, reverse=True)
    return found[:top]


def describe(p: Parlay) -> str:
    names = " + ".join(f"{leg.name} ({leg.odds:+d})" for leg in p.legs)
    fair = to_american(1 / p.hit) if 0 < p.hit < 1 else 0
    return (f"{names}\n      pays {p.payout:.1f}x ({to_american(p.payout):+d})  "
            f"model hit chance {p.hit:.1%} (fair {fair:+d})  model EV {p.ev:+.1%} per $1"
            + ("  [same-game: book price will be lower]" if p.same_game else ""))


def edge(leg: Leg, games: dict[str, Game]) -> float:
    """Model probability minus the book's implied probability (vig included)."""
    return leg.model_prob(games) - implied(leg.odds)
