"""A day's games ("slate"): load one from JSON, turn its odds and props into bets, and price them.

Slate JSON (see games/2026-10-06.json for a full example):
  {"date": "YYYY-MM-DD", "postseason": bool, "league": {...}, "notes": [...], "sources": [...],
   "games": [{"info": "...", "away": {Team + "record"}, "home": {...}, "away_sp": {Pitcher},
              "home_sp": {...}, "odds": {...}, "props": [...], "why": [...], "moves": [...]}]}
"""
from __future__ import annotations

import dataclasses
import json

from . import props as P
from .model import TEAMS, Game, League, Matchup, Pitcher, Team
from .odds import ev, kelly, no_vig
from .parlay import Leg


def abbr(name: str) -> str:
    return TEAMS[name][1] if name in TEAMS else name.split()[-1][:3].upper()


def build(cls, data: dict):
    """A dataclass from a dict, ignoring keys it doesn't know (notes, record...)."""
    names = {f.name for f in dataclasses.fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in names})


def load_file(path: str) -> tuple[League, list[dict], dict]:
    """(league, games, the slate's other fields). Each game keeps its raw JSON under "raw"."""
    with open(path) as f:
        data = json.load(f)
    entries = []
    for g in data.get("games", []):
        m = Matchup(build(Team, g["away"]), build(Team, g["home"]), build(Pitcher, g["away_sp"]),
                    build(Pitcher, g["home_sp"]), park=g.get("park"),
                    postseason=data.get("postseason", False), weather=g.get("weather", 1.0))
        entries.append({"label": f"{m.away.name} @ {m.home.name}", "info": g.get("info", ""),
                        "matchup": m, "odds": g.get("odds") or {}, "props": g.get("props") or [], "raw": g})
    meta = {k: v for k, v in data.items() if k != "games"}
    return build(League, data.get("league", {})), entries, meta


def prop_legs(label: str, m: Matchup, specs: list[dict], lg: League) -> list[Leg]:
    legs = []
    for s in specs:
        if s["kind"] == "strikeouts":
            p = m.away_sp if s["pitcher"] == "away" else m.home_sp
            over = P.strikeout_over(s["line"], P.strikeout_mean(p, m.postseason, s.get("opp_k_factor", 1.0)))
            last = p.name.split()[-1]
            if s.get("over"):
                legs.append(Leg(label, f"k:{p.name}", f"{last} o{s['line']:g} K", s["over"], prob=over))
            if s.get("under"):
                legs.append(Leg(label, f"k:{p.name}", f"{last} u{s['line']:g} K", s["under"], prob=1 - over))
        elif s["kind"] == "homer":
            opp = m.home_sp if s["team"] == "away" else m.away_sp
            factor = 0.6 * P.pitcher_hr_factor(opp, lg) + 0.4  # the starter sees ~60% of his PAs
            prob = P.homer_prob(s["hr"], s["pa"], s.get("slot", 5), factor, m.park or m.home.home_park)
            legs.append(Leg(label, f"hr:{s['player']}", f"{s['player']} HR", s["odds"], prob=prob,
                            team=s["team"]))
    return legs


def bet_rows(legs: list[Leg], games: dict[str, Game], bankroll: float) -> list[dict]:
    """Per bet: the book's no-vig chance (when both sides are posted), the model's chance,
    push chance, expected profit per $1 and a quarter-Kelly stake."""
    rows = []
    for leg in legs:
        twin = [x for x in legs if x.game == leg.game and x.market == leg.market and x is not leg]
        p, push = leg.model_prob(games), leg.push_prob(games)
        rows.append({"leg": leg, "fair": no_vig(leg.odds, twin[0].odds)[0] if twin else None,
                     "model": p, "push": push, "ev": ev(p, leg.odds, push),
                     "stake": kelly(p / (1 - push) if push < 1 else 0, leg.odds) * bankroll})
    return rows
