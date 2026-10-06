"""Builds the MLB Bet Lab web page for a slate: runs the model, then drops the results into
web/template.html as JSON (the page draws itself from that, and its calculator runs the same model)."""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from .model import League, effective_fip, project, starter_innings
from .parlay import Parlay, game_legs, leg_ev, likeliest, search
from .slate import abbr, bet_rows, prop_legs

TEMPLATE = Path(__file__).with_name("web") / "template.html"
PICK_EV = 0.03  # a single bet is a "pick" at +3% expected profit or better


def tag(ev: float) -> str:
    return "pick" if ev >= PICK_EV else "thin" if ev >= 0 else "pass"


def nickname(team: str) -> str:
    """"Milwaukee Brewers" -> "Brewers", "Boston Red Sox" -> "Red Sox"."""
    words = team.split()
    return " ".join(words[-2:]) if words[-1] in ("Sox", "Jays") else words[-1]


def plain(leg, names: dict) -> str:
    """A bet in everyday words: "MIL +1.5" -> "Brewers win, or lose by just 1"."""
    if leg.market == "ml":
        return f"{names[leg.team]} win"
    if leg.market == "rl":
        spread = float(leg.name.rsplit(" ", 1)[1])
        if spread > 0:
            margin = math.ceil(spread) - 1
            return f"{names[leg.team]} win, or lose by just {margin}" if margin == 1 else \
                f"{names[leg.team]} win, or lose by {margin} or less"
        return f"{names[leg.team]} win by {math.floor(-spread) + 1} or more"
    if leg.market == "total":
        side, line = leg.name.split()
        line = float(line)
        refund = f" (exactly {line:g} = money back)" if line.is_integer() else ""
        if side == "Over":
            return f"{math.floor(line) + 1} or more total runs{refund}"
        return f"{math.ceil(line) - 1} or fewer total runs{refund}"
    if leg.market.startswith("k:"):
        who, line = leg.market[2:].split()[-1], float(leg.name.split()[-2][1:])
        if leg.name.split()[-2].startswith("o"):
            return f"{who} gets {math.floor(line) + 1}+ strikeouts"
        return f"{who} gets {math.ceil(line) - 1} or fewer strikeouts"
    if leg.market.startswith("hr:"):
        return f"{leg.market[3:]} hits a home run"
    return leg.name


def first_pitch(info: str) -> str:
    m = re.search(r"\d{1,2}:\d{2}\s*[AP]M(?:\s*ET)?", info)
    return m.group(0) if m else ""


def leg_json(leg, games, ctx: dict, row: dict | None = None) -> dict:
    c = ctx[leg.game]
    out = {"name": leg.name, "plain": plain(leg, c["names"]), "game": c["short"], "when": c["when"],
           "odds": leg.odds, "model": leg.model_prob(games)}
    if row:
        out.update(fair=row["fair"], ev=row["ev"], tag=tag(row["ev"]), push=row["push"])
    return out


def parlay_json(p: Parlay, games, ctx: dict) -> dict:
    return {"legs": [leg_json(leg, games, ctx) for leg in p.legs],
            "payout": p.payout, "hit": p.hit, "ev": p.ev, "same_game": p.same_game}


def _side(m, side: str, lg: League) -> dict:
    team, sp = (m.away, m.away_sp) if side == "away" else (m.home, m.home_sp)
    fip = effective_fip(sp, lg)
    return {"abbr": abbr(team.name), "g": team.games, "rs": team.runs_scored, "ra": team.runs_allowed,
            "sp": sp.name, "era": sp.era, "ip": sp.ip, "fip": round(fip, 2) if fip is not None else None,
            "xip": round(starter_innings(sp, m.postseason), 2)}


def _calc_odds(odds: dict) -> dict:
    rl, tot, ml = odds.get("run_line") or {}, odds.get("total") or {}, odds.get("ml") or {}
    away_rl = rl.get("away") or [None, None]
    return {"aml": ml.get("away"), "hml": ml.get("home"), "arl": away_rl[0], "arlp": away_rl[1],
            "hrlp": (rl.get("home") or [None, None])[1], "tot": tot.get("line"),
            "over": tot.get("over"), "under": tot.get("under")}


def slate_data(lg: League, entries: list[dict], meta: dict, target: float = 50, bankroll: float = 100) -> dict:
    games, ctx, out, every = {}, {}, [], []
    for e in entries:
        m = e["matchup"]
        games[e["label"]] = project(m, lg)
        names = {"away": nickname(m.away.name), "home": nickname(m.home.name)}
        ctx[e["label"]] = {"names": names, "short": f"{names['away']} @ {names['home']}",
                           "when": first_pitch(e["info"])}
    for e in entries:
        m, raw, g = e["matchup"], e["raw"], games[e["label"]]
        a, h = abbr(m.away.name), abbr(m.home.name)
        legs = game_legs(e["label"], a, h, e["odds"]) + prop_legs(e["label"], m, e["props"], lg)
        every += legs
        # a 3-leg parlay when one is worth it, else the best 2-leg (side + total)
        best = sorted(search(legs, games, min_legs=3, max_legs=3, top=1)
                      + search(legs, games, min_legs=2, max_legs=2, top=1), key=lambda p: p.ev, reverse=True)
        names = ctx[e["label"]]["names"]
        out.append({
            "label": f"{a} @ {h}", "short": ctx[e["label"]]["short"], "when": ctx[e["label"]]["when"],
            "info": e["info"], "why": raw.get("why", []), "moves": raw.get("moves", []),
            "away": {"abbr": a, "name": m.away.name, "nick": names["away"], "record": raw["away"].get("record", ""),
                     "sp": m.away_sp.name, "hand": m.away_sp.hand, "runs": g.away_mean, "win": g.away_win},
            "home": {"abbr": h, "name": m.home.name, "nick": names["home"], "record": raw["home"].get("record", ""),
                     "sp": m.home_sp.name, "hand": m.home_sp.hand, "runs": g.home_mean, "win": g.home_win},
            "fair_total": g.fair_total(), "posted_total": (e["odds"].get("total") or {}).get("line"),
            "bets": [leg_json(r["leg"], games, ctx, r) for r in bet_rows(legs, games, bankroll)],
            "parlay": parlay_json(best[0], games, ctx) if best else None,
            "calc": {"away": _side(m, "away", lg), "home": _side(m, "home", lg),
                     "odds": _calc_odds(e["odds"]), "post": m.postseason},
        })
    rows = {id(r["leg"]): r for r in bet_rows(every, games, bankroll)}
    safest = sorted((leg for leg in every if leg_ev(leg, games) > -0.05 and leg.model_prob(games) >= 0.55),
                    key=lambda leg: leg.model_prob(games), reverse=True)[:5]
    value = sorted((leg for leg in every if rows[id(leg)]["ev"] >= PICK_EV),
                   key=lambda leg: rows[id(leg)]["ev"], reverse=True)[:4]
    return {
        "date": meta.get("date", ""), "headline": meta.get("headline", ""), "notice": meta.get("notice", ""),
        "notes": meta.get("notes", []), "sources": meta.get("sources", []),
        "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "league": {"rpg": lg.rpg, "era": lg.era}, "target": target, "games": out,
        "safest": [leg_json(leg, games, ctx, rows[id(leg)]) for leg in safest],
        "value": [leg_json(leg, games, ctx, rows[id(leg)]) for leg in value],
        "likeliest": [parlay_json(p, games, ctx) for p in likeliest(every, games)],
        "longshots": [parlay_json(p, games, ctx) for p in search(every, games, target=target, min_legs=2,
                                                                  max_legs=6, top=2)],
    }


def render(data: dict) -> str:
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")  # can't end the <script> early
    return TEMPLATE.read_text().replace("__SLATE_JSON__", blob)


def write_page(lg: League, entries: list[dict], meta: dict, path: str, target: float = 50,
               bankroll: float = 100) -> None:
    Path(path).write_text(render(slate_data(lg, entries, meta, target, bankroll)))
