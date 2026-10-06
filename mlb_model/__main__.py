"""MLB betting model. Run from the repo folder:

  python3 -m mlb_model today                      today's games, live from the MLB Stats API
  python3 -m mlb_model today --odds odds.json     ...priced against odds you typed in
  python3 -m mlb_model file mlb_model/games/2026-10-06.json   a hand-built slate (no internet)
  python3 -m mlb_model backtest --season 2025     how well-calibrated the team model was

Set ODDS_API_KEY (free at the-odds-api.com) and `today` pulls live odds too.
Options: --target 50 (long-shot parlay size), --bankroll 100 (for stake sizes).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
from datetime import date

from . import props as P
from .model import TEAMS, League, Matchup, Pitcher, Team, project
from .odds import ev, kelly, no_vig
from .parlay import Leg, describe, game_legs, search


def abbr(name: str) -> str:
    return TEAMS[name][1] if name in TEAMS else name.split()[-1][:3].upper()


def build(cls, data: dict):
    """A dataclass from a dict, ignoring keys it doesn't know (notes, sources...)."""
    names = {f.name for f in dataclasses.fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in names})


def load_file(path: str) -> tuple[League, list[dict]]:
    with open(path) as f:
        data = json.load(f)
    entries = []
    for g in data["games"]:
        m = Matchup(build(Team, g["away"]), build(Team, g["home"]), build(Pitcher, g["away_sp"]),
                    build(Pitcher, g["home_sp"]), park=g.get("park"),
                    postseason=data.get("postseason", False), weather=g.get("weather", 1.0))
        entries.append({"label": f"{m.away.name} @ {m.home.name}", "info": g.get("info", ""),
                        "matchup": m, "odds": g.get("odds") or {}, "props": g.get("props") or []})
    return build(League, data.get("league", {})), entries


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
            legs.append(Leg(label, f"hr:{s['player']}", f"{s['player']} HR", s["odds"], prob=prob))
    return legs


def report(lg: League, entries: list[dict], target: float, bankroll: float) -> None:
    games, every_leg = {}, []
    for e in entries:
        m = e["matchup"]
        g = games[e["label"]] = project(m, lg)
        a, h = abbr(m.away.name), abbr(m.home.name)
        print(f"\n=== {e['label']}   {e['info']}")
        print(f"  Starters      {a} {m.away_sp.name} ({m.away_sp.hand})  vs  {h} {m.home_sp.name} ({m.home_sp.hand})")
        print(f"  Proj. runs    {a} {g.away_mean:.2f}   {h} {g.home_mean:.2f}   fair total {g.fair_total():g}")
        print(f"  Win chance    {a} {g.away_win:.1%}   {h} {g.home_win:.1%}")
        legs = game_legs(e["label"], a, h, e["odds"]) + prop_legs(e["label"], m, e["props"], lg)
        every_leg += legs
        if not legs:
            continue
        print(f"  {'Bet':<22}{'Price':>7}{'Fair':>8}{'Model':>8}{'EV/$1':>8}{'Stake':>8}")
        for leg in legs:
            twin = [x for x in legs if x.market == leg.market and x is not leg]
            fair = no_vig(leg.odds, twin[0].odds)[0] if twin else None
            p, push = leg.model_prob(games), leg.push_prob(games)
            stake = kelly(p / (1 - push) if push < 1 else 0, leg.odds) * bankroll
            print(f"  {leg.name:<22}{leg.odds:>+7d}{f'{fair:.1%}' if fair else '':>8}{p:>8.1%}"
                  f"{ev(p, leg.odds, push):>+8.1%}{f'${stake:.2f}' if stake else '-':>8}")
        print("  Best 3-leg same-game parlays (model EV; the book's SGP price will be lower):")
        for par in search(legs, games, min_legs=3, max_legs=3, top=2):
            print("    " + describe(par))
    if target and every_leg:
        print(f"\n=== Long shots paying ~{target:g}x, best model EV first")
        for par in search(every_leg, games, target=target, min_legs=2, max_legs=6) or []:
            print("    " + describe(par))
    print("\nFair = book's no-vig probability. Model = this model. EV/$1 = model's expected profit."
          "\nStake = quarter-Kelly on the bankroll, capped at 5%. Every parlay leg multiplies the vig.")


def main() -> None:
    ap = argparse.ArgumentParser(prog="mlb_model", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["today", "file", "backtest"])
    ap.add_argument("path", nargs="?", help="slate JSON for `file`")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--odds", help='JSON {"Away Team @ Home Team": {odds}} for `today`')
    ap.add_argument("--target", type=float, default=50)
    ap.add_argument("--bankroll", type=float, default=100)
    ap.add_argument("--season", type=int, default=date.today().year - 1)
    ap.add_argument("--start")
    ap.add_argument("--end")
    args = ap.parse_args()

    if args.command == "backtest":
        from .backtest import run, season_games
        print(json.dumps(run(season_games(args.season, args.start, args.end)), indent=2))
        return
    if args.command == "file":
        if not args.path:
            ap.error("`file` needs a slate JSON path")
        lg, entries = load_file(args.path)
    else:
        from .statsapi import matchups
        lg, entries = matchups(args.date)
        odds = {}
        if args.odds:
            with open(args.odds) as f:
                odds = json.load(f)
        elif os.environ.get("ODDS_API_KEY"):
            from .oddsapi import odds_by_game
            odds = odds_by_game(os.environ["ODDS_API_KEY"])
        for e in entries:
            e["odds"], e["props"] = odds.get(e["label"], {}), []
        if not entries:
            print(f"No MLB games on {args.date}.")
            return
    report(lg, entries, args.target, args.bankroll)


if __name__ == "__main__":
    main()
