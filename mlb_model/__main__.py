"""MLB betting model. Run from the repo folder:

  python3 -m mlb_model today                      today's games, live from the MLB Stats API
  python3 -m mlb_model today --odds odds.json     ...priced against odds you typed in
  python3 -m mlb_model file mlb_model/games/2026-10-06.json   a hand-built slate (no internet)
  python3 -m mlb_model page mlb_model/games/2026-10-06.json   ...as the MLB Bet Lab web page
  python3 -m mlb_model backtest --season 2025     how well-calibrated the team model was

Set ODDS_API_KEY (free at the-odds-api.com) and `today` pulls live odds too.
Easiest: put the key in odds_api_key.txt and run `bash bets` (or double-click "MLB Bets.command").
Options: --target 50 (long-shot parlay size), --bankroll 100 (for stake sizes).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
from datetime import date

from .model import League, project
from .parlay import describe, game_legs, search
from .slate import abbr, bet_rows, load_file, prop_legs


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
        for r in bet_rows(legs, games, bankroll):
            leg, fair, stake = r["leg"], r["fair"], r["stake"]
            print(f"  {leg.name:<22}{leg.odds:>+7d}{f'{fair:.1%}' if fair else '':>8}{r['model']:>8.1%}"
                  f"{r['ev']:>+8.1%}{f'${stake:.2f}' if stake else '-':>8}")
        print("  Best 3-leg same-game parlays (model EV; the book's SGP price will be lower):")
        for par in search(legs, games, min_legs=3, max_legs=3, top=2):
            print("    " + describe(par))
    if not every_leg:
        print("\nNo odds loaded, so no bets yet. Put your free the-odds-api.com key in"
              " odds_api_key.txt in this folder (see README) and run again.")
        return
    if target:
        print(f"\n=== Long shots paying ~{target:g}x, best model EV first")
        for par in search(every_leg, games, target=target, min_legs=2, max_legs=6) or []:
            print("    " + describe(par))
    print("\nFair = book's no-vig probability. Model = this model. EV/$1 = model's expected profit."
          "\nStake = quarter-Kelly on the bankroll, capped at 5%. Every parlay leg multiplies the vig.")


def main() -> None:
    try:
        run(sys.argv[1:])
    except urllib.error.HTTPError as exc:
        if "the-odds-api" in exc.url and exc.code in (401, 403):
            sys.exit("The Odds API turned down the key in odds_api_key.txt. Check it, or your free"
                     " 500 monthly requests may be used up.")
        sys.exit(f"Server error {exc.code} from {exc.url.split('?')[0]}. Try again in a minute.")
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" in str(exc):
            sys.exit("Your Python can't check web certificates. Run this once, then try again:\n"
                     "  python3 -m pip install certifi")
        sys.exit(f"Couldn't reach the internet ({exc.reason}). Check your connection.")


def run(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="mlb_model", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["today", "file", "page", "backtest"])
    ap.add_argument("path", nargs="?", help="slate JSON for `file` and `page`")
    ap.add_argument("--out", help="where `page` writes the web page (default: next to the slate)")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--odds", help='JSON {"Away Team @ Home Team": {odds}} for `today`')
    ap.add_argument("--target", type=float, default=50)
    ap.add_argument("--bankroll", type=float, default=100)
    ap.add_argument("--season", type=int, default=date.today().year - 1)
    ap.add_argument("--start")
    ap.add_argument("--end")
    args = ap.parse_args(argv)

    if args.command == "backtest":
        from .backtest import run, season_games
        print(json.dumps(run(season_games(args.season, args.start, args.end)), indent=2))
        return
    if args.command in ("file", "page"):
        if not args.path:
            ap.error(f"`{args.command}` needs a slate JSON path")
        lg, entries, meta = load_file(args.path)
        if args.command == "page":
            from .page import write_page
            out = args.out or args.path.rsplit(".", 1)[0] + ".html"
            write_page(lg, entries, meta, out, args.target, args.bankroll)
            print(f"Wrote {out}")
            return
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
