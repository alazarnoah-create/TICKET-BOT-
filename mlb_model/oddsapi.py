"""Live odds from The Odds API (the-odds-api.com; free key, 500 requests a month).
Set ODDS_API_KEY to use it. Takes the best price across US books for each bet (line shopping)."""
from __future__ import annotations

import urllib.parse
from collections import Counter

from .statsapi import http_json

URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/"


def _fetch(api_key: str) -> list[dict]:
    params = urllib.parse.urlencode({"apiKey": api_key, "regions": "us", "oddsFormat": "american",
                                     "markets": "h2h,spreads,totals"})
    return http_json(f"{URL}?{params}")


def _best(outcomes: list[dict], name: str, point=None):
    prices = [o["price"] for o in outcomes if o["name"] == name and (point is None or o.get("point") == point)]
    return max(prices, key=lambda a: a if a > 0 else 10000 / -a) if prices else None  # best payout


def odds_by_game(api_key: str) -> dict[str, dict]:
    """{"Away Team @ Home Team": odds dict in the format parlay.game_legs reads}"""
    out = {}
    for ev in _fetch(api_key):
        away, home = ev["away_team"], ev["home_team"]
        markets: dict[str, list] = {}
        for book in ev.get("bookmakers", []):
            for m in book.get("markets", []):
                markets.setdefault(m["key"], []).extend(m["outcomes"])
        odds: dict = {}
        if "h2h" in markets:
            odds["ml"] = {"away": _best(markets["h2h"], away), "home": _best(markets["h2h"], home)}
        if "spreads" in markets:
            pts = Counter(o["point"] for o in markets["spreads"] if o["name"] == away)
            if pts:
                pt = pts.most_common(1)[0][0]
                odds["run_line"] = {"away": [pt, _best(markets["spreads"], away, pt)],
                                    "home": [-pt, _best(markets["spreads"], home, -pt)]}
        if "totals" in markets:
            pts = Counter(o["point"] for o in markets["totals"])
            if pts:
                pt = pts.most_common(1)[0][0]
                odds["total"] = {"line": pt, "over": _best(markets["totals"], "Over", pt),
                                 "under": _best(markets["totals"], "Under", pt)}
        out[f"{away} @ {home}"] = odds
    return out
