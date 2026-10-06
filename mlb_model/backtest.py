"""Checks the team half of the model on a past season, with no peeking: each game is predicted
from only the games played before it. Reports how well the win probabilities were calibrated
(Brier score, log loss) against the naive "home team wins 54%" guess."""
from __future__ import annotations

from math import log

from .model import League, Matchup, Pitcher, Team, project
from .statsapi import get

MIN_GAMES = 15  # skip each team's first few games: nothing to go on yet


def season_games(season: int, start: str | None = None, end: str | None = None) -> list[dict]:
    data = get("schedule", sportId=1, gameType="R", startDate=start or f"{season}-03-01",
               endDate=end or f"{season}-11-30")
    games = []
    for d in data.get("dates", []):
        for g in d.get("games", []):
            a, h = g["teams"]["away"], g["teams"]["home"]
            if g["status"].get("abstractGameState") == "Final" and "score" in a and "score" in h:
                games.append({"date": g["gameDate"], "away": a["team"]["name"], "home": h["team"]["name"],
                              "away_runs": a["score"], "home_runs": h["score"]})
    return sorted(games, key=lambda g: g["date"])


def run(games: list[dict]) -> dict:
    seen: dict[str, list[int]] = {}  # team -> [games, runs scored, runs allowed]
    lg_runs = lg_games = 0
    preds = []
    for g in games:
        a, h = seen.setdefault(g["away"], [0, 0, 0]), seen.setdefault(g["home"], [0, 0, 0])
        if a[0] >= MIN_GAMES and h[0] >= MIN_GAMES:
            lg = League(rpg=lg_runs / lg_games)
            no_sp = Pitcher("team", expected_ip=0)  # team-only: all innings rated by team runs allowed
            m = Matchup(Team(g["away"], *a), Team(g["home"], *h), no_sp, no_sp)
            game = project(m, lg)
            preds.append((game.home_win, g["home_runs"] > g["away_runs"],
                          game.away_mean + game.home_mean, g["home_runs"] + g["away_runs"]))
        a[0] += 1; a[1] += g["away_runs"]; a[2] += g["home_runs"]  # noqa: E702
        h[0] += 1; h[1] += g["home_runs"]; h[2] += g["away_runs"]  # noqa: E702
        lg_runs += g["away_runs"] + g["home_runs"]
        lg_games += 2
    return summarize(preds)


def summarize(preds: list[tuple]) -> dict:
    if not preds:
        return {"games": 0}
    n = len(preds)
    home_rate = sum(won for _, won, _, _ in preds) / n

    def brier(ps):
        return sum((p - won) ** 2 for p, (_, won, _, _) in zip(ps, preds)) / n

    def logloss(ps):
        return -sum(log(p if won else 1 - p) for p, (_, won, _, _) in zip(ps, preds)) / n

    model = [p for p, _, _, _ in preds]
    naive = [0.54] * n
    buckets = {}
    for p, won, _, _ in preds:
        b = min(int(p * 10), 9) / 10
        buckets.setdefault(b, []).append((p, won))
    return {
        "games": n,
        "home_win_rate": home_rate,
        "accuracy": sum((p > 0.5) == won for p, won, _, _ in preds) / n,
        "brier": brier(model), "brier_naive": brier(naive),
        "logloss": logloss(model), "logloss_naive": logloss(naive),
        "avg_pred_total": sum(t for _, _, t, _ in preds) / n,
        "avg_actual_total": sum(t for _, _, _, t in preds) / n,
        "calibration": {f"{b:.0%}-{b + 0.1:.0%}": (len(v), sum(p for p, _ in v) / len(v),
                                                   sum(w for _, w in v) / len(v))
                        for b, v in sorted(buckets.items())},
    }
