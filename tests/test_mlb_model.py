"""Offline tests for the MLB model. Run: python3 -m unittest tests.test_mlb_model"""
import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mlb_model import backtest, oddsapi, statsapi  # noqa: E402
from mlb_model.__main__ import load_file, report  # noqa: E402
from mlb_model.model import Game, League, Matchup, Pitcher, Team, pitcher_era, project, runs_pmf  # noqa: E402
from mlb_model.odds import ev, kelly, no_vig, to_american, to_decimal  # noqa: E402
from mlb_model.parlay import game_legs, price, search  # noqa: E402
from mlb_model.props import homer_prob, strikeout_over  # noqa: E402

SLATE = Path(__file__).resolve().parent.parent / "mlb_model" / "games" / "2026-10-06.json"


def avg_team(name, rs=720, ra=720):
    return Team(name, 162, rs, ra, park=1.0)


class Odds(unittest.TestCase):
    def test_conversions(self):
        self.assertAlmostEqual(to_decimal(-150), 1 + 100 / 150)
        self.assertEqual(to_decimal(200), 3.0)
        self.assertEqual(to_american(2.5), 150)
        self.assertEqual(to_american(1.5), -200)

    def test_no_vig_and_sizing(self):
        self.assertEqual(no_vig(-110, -110), [0.5, 0.5])
        self.assertAlmostEqual(ev(0.5, 100), 0.0)
        self.assertEqual(kelly(0.4, 100), 0.0)  # negative EV: no bet
        self.assertLessEqual(kelly(0.9, 100), 0.05)  # capped


class Model(unittest.TestCase):
    def test_runs_distribution_matches_mlb_spread(self):
        pmf = runs_pmf(4.5)
        mean = sum(k * p for k, p in enumerate(pmf))
        sd = sum((k - mean) ** 2 * p for k, p in enumerate(pmf)) ** 0.5
        self.assertAlmostEqual(sum(pmf), 1.0)
        self.assertAlmostEqual(mean, 4.5, places=2)
        self.assertTrue(2.9 < sd < 3.3, sd)

    def test_even_teams_give_home_field_edge(self):
        g = project(Matchup(avg_team("A"), avg_team("B"), Pitcher("x"), Pitcher("y")), League(rpg=4.45))
        self.assertAlmostEqual(sum(g.scores.values()), 1.0)
        self.assertTrue(0.52 < g.home_win < 0.56, g.home_win)
        over, under, push = g.total_probs(8.5)
        self.assertAlmostEqual(over + under, 1.0)
        self.assertEqual(push, 0.0 if push < 1e-12 else push)

    def test_better_team_and_better_starter_win_more(self):
        lg = League()
        base = project(Matchup(avg_team("A"), avg_team("B"), Pitcher("x"), Pitcher("y")), lg)
        strong = project(Matchup(avg_team("A", 850, 600), avg_team("B"), Pitcher("x"), Pitcher("y")), lg)
        ace = Pitcher("ace", ip=200, era=2.0, fip=2.2, gs=32)
        aced = project(Matchup(avg_team("A"), avg_team("B"), ace, Pitcher("y")), lg)
        self.assertGreater(strong.away_win, base.away_win + 0.1)
        self.assertGreater(aced.away_win, base.away_win + 0.03)
        self.assertLess(aced.home_mean, base.home_mean)

    def test_pitcher_regression(self):
        lg = League(era=4.0)
        self.assertEqual(pitcher_era(Pitcher("new"), lg), 4.0)
        small = pitcher_era(Pitcher("hot start", ip=20, era=1.0), lg)
        big = pitcher_era(Pitcher("ace", ip=200, era=1.0), lg)
        self.assertTrue(1.0 < big < small < 4.0)
        # no HR count: an xFIP-style estimate from K and BB still counts
        self.assertLess(pitcher_era(Pitcher("k", ip=180, k=230, bb=30), lg), 4.0)


class Parlays(unittest.TestCase):
    def setUp(self):
        self.games = {"g1": Game(4.0, 4.5), "g2": Game(5.0, 3.5)}
        self.odds = {"ml": {"away": 120, "home": -140}, "run_line": {"away": [1.5, -170], "home": [-1.5, 150]},
                     "total": {"line": 8, "over": -110, "under": -110}}

    def test_legs_and_pushes(self):
        legs = {leg.name: leg for leg in game_legs("g1", "AW", "HM", self.odds)}
        self.assertEqual(set(legs), {"AW ML", "HM ML", "AW +1.5", "HM -1.5", "Over 8", "Under 8"})
        g = self.games["g1"]
        self.assertAlmostEqual(legs["AW ML"].model_prob(self.games) + legs["HM ML"].model_prob(self.games), 1)
        self.assertAlmostEqual(legs["AW +1.5"].model_prob(self.games) + legs["HM -1.5"].model_prob(self.games), 1)
        self.assertAlmostEqual(legs["Over 8"].push_prob(self.games), g.total_probs(8)[2])

    def test_cross_game_parlay_is_product_and_same_game_is_joint(self):
        l1 = game_legs("g1", "A", "H", {"ml": {"home": -140}})[0]
        l2 = game_legs("g2", "A", "H", {"ml": {"away": -150}})[0]
        p = price([l1, l2], self.games)
        self.assertAlmostEqual(p.hit, l1.model_prob(self.games) * l2.model_prob(self.games))
        self.assertAlmostEqual(p.payout, to_decimal(-140) * to_decimal(-150))
        legs = game_legs("g1", "A", "H", {"ml": {"home": -140}, "total": {"line": 8.5, "over": -110}})
        joint = price(legs, self.games).hit
        self.assertAlmostEqual(joint, self.games["g1"].prob(legs[0].win, legs[1].win))

    def test_search_skips_conflicting_bets(self):
        legs = game_legs("g1", "A", "H", self.odds) + game_legs("g2", "A2", "H2", self.odds)
        for par in search(legs, self.games, min_legs=2, max_legs=4, top=50):
            keys = [(x.game, "side" if x.market in ("ml", "rl") else x.market) for x in par.legs]
            self.assertEqual(len(keys), len(set(keys)))
        for par in search(legs, self.games, target=10, top=50):
            self.assertTrue(7.5 <= par.payout <= 15)


class Props(unittest.TestCase):
    def test_props(self):
        self.assertGreater(strikeout_over(5.5, 7.0), strikeout_over(5.5, 5.0))
        self.assertTrue(0 < strikeout_over(7.5, 6.5) < 0.5)
        star = homer_prob(45, 650, slot=2)
        self.assertTrue(0.15 < star < 0.35, star)
        self.assertLess(homer_prob(5, 500, slot=9), star)


class StatsApi(unittest.TestCase):
    def test_innings_and_traded_pitcher(self):
        self.assertAlmostEqual(statsapi.innings("180.1"), 180 + 1 / 3)
        line = statsapi._combined([
            {"team": {"id": 1}, "stat": {"inningsPitched": "100.2", "earnedRuns": 40, "strikeOuts": 90}},
            {"team": {"id": 2}, "stat": {"inningsPitched": "50.1", "earnedRuns": 30, "strikeOuts": 40}}])
        self.assertAlmostEqual(line["inningsPitched"], 151)
        self.assertEqual(line["strikeOuts"], 130)
        self.assertAlmostEqual(line["era"], 9 * 70 / 151)

    def test_matchups_parses_api_shapes(self):
        def stat(**kw):
            return {"stats": [{"splits": [{"stat": kw}]}]}

        def fake_get(path, **params):
            if path == "schedule":
                return {"dates": [{"games": [{
                    "gameType": "D", "gameDate": "2026-10-06T22:08:00Z", "status": {"detailedState": "Scheduled"},
                    "seriesStatus": {"description": "NLDS Game 3"},
                    "teams": {"away": {"team": {"id": 119, "name": "Los Angeles Dodgers"},
                                       "probablePitcher": {"id": 1, "fullName": "Starter One"}},
                              "home": {"team": {"id": 144, "name": "Atlanta Braves"}}}}]}]}
            if path == "teams/stats":
                if params["group"] == "hitting":
                    return {"stats": [{"splits": [{"stat": {"runs": 720, "gamesPlayed": 162}}] * 30}]}
                return {"stats": [{"splits": [{"stat": {"inningsPitched": "1450.0", "earnedRuns": 660,
                                                        "homeRuns": 180, "baseOnBalls": 500, "hitByPitch": 60,
                                                        "strikeOuts": 1400}}] * 30}]}
            if path.startswith("teams/") and params.get("stats") == "statSplits":
                if params["group"] == "hitting":
                    return {"stats": [{"splits": [{"split": {"code": "vl"}, "stat": {"ops": ".790"}},
                                                  {"split": {"code": "vr"}, "stat": {"ops": ".740"}}]}]}
                return stat(inningsPitched="560.0", earnedRuns=220, homeRuns=60, baseOnBalls=200, strikeOuts=600)
            if path.startswith("teams/"):
                if params["group"] == "hitting":
                    return stat(runs=801, gamesPlayed=162, ops=".752")
                return stat(runs=600)
            if path == "people/1":
                return {"people": [{"fullName": "Starter One", "pitchHand": {"code": "R"},
                                    "stats": [{"splits": [{"stat": {"inningsPitched": "185.0", "era": "2.53",
                                                                    "strikeOuts": 182, "baseOnBalls": 40,
                                                                    "homeRuns": 20, "gamesStarted": 30,
                                                                    "whip": "0.87"}}]}]}]}
            raise AssertionError(path)

        real, statsapi.get = statsapi.get, fake_get
        try:
            lg, entries = statsapi.matchups("2026-10-06")
        finally:
            statsapi.get = real
        self.assertAlmostEqual(lg.rpg, 720 / 162)
        self.assertAlmostEqual(lg.era, 9 * 660 / 1450)
        m = entries[0]["matchup"]
        self.assertTrue(m.postseason)
        self.assertEqual((m.away.runs_scored, m.away.runs_allowed, m.away.ops_vs), (801, 600, {"L": 0.79, "R": 0.74}))
        self.assertAlmostEqual(m.away.bullpen_era, 9 * 220 / 560)
        self.assertEqual((m.away_sp.era, m.away_sp.gs, m.away_sp.hand), (2.53, 30, "R"))
        self.assertEqual(m.home_sp.name, "TBD")
        self.assertIn("NLDS Game 3", entries[0]["info"])


class OddsApi(unittest.TestCase):
    def test_best_prices(self):
        event = {"away_team": "Los Angeles Dodgers", "home_team": "Atlanta Braves", "bookmakers": [
            {"markets": [{"key": "h2h", "outcomes": [{"name": "Los Angeles Dodgers", "price": -115},
                                                    {"name": "Atlanta Braves", "price": -105}]},
                         {"key": "totals", "outcomes": [{"name": "Over", "price": -115, "point": 6},
                                                       {"name": "Under", "price": -105, "point": 6}]}]},
            {"markets": [{"key": "h2h", "outcomes": [{"name": "Los Angeles Dodgers", "price": -110},
                                                    {"name": "Atlanta Braves", "price": -110}]},
                         {"key": "spreads", "outcomes": [{"name": "Los Angeles Dodgers", "price": 160, "point": -1.5},
                                                        {"name": "Atlanta Braves", "price": -190, "point": 1.5}]},
                         {"key": "totals", "outcomes": [{"name": "Over", "price": -110, "point": 6},
                                                       {"name": "Under", "price": -110, "point": 6}]}]}]}
        real, oddsapi._fetch = oddsapi._fetch, lambda key: [event]
        try:
            odds = oddsapi.odds_by_game("key")["Los Angeles Dodgers @ Atlanta Braves"]
        finally:
            oddsapi._fetch = real
        self.assertEqual(odds["ml"], {"away": -110, "home": -105})
        self.assertEqual(odds["run_line"], {"away": [-1.5, 160], "home": [1.5, -190]})
        self.assertEqual(odds["total"], {"line": 6, "over": -110, "under": -105})


class Backtest(unittest.TestCase):
    def test_no_peeking_and_strong_team_favored(self):
        games = []
        for i in range(60):  # "Good" scores 6 and allows 2; the others trade 4-4ish games
            day = f"2025-05-{1 + i // 3:02d}T{i % 3:02d}"
            games.append({"date": day, "away": "Good", "home": f"Other{i % 3}", "away_runs": 6, "home_runs": 2})
            games.append({"date": day, "away": f"Other{i % 3}", "home": f"Other{(i + 1) % 3}",
                          "away_runs": 4 + i % 2, "home_runs": 4 + (i + 1) % 2})
        out = backtest.run(games)
        self.assertGreater(out["games"], 0)
        self.assertGreater(out["accuracy"], 0.5)
        self.assertLess(out["brier"], out["brier_naive"])


class Slate(unittest.TestCase):
    def test_todays_slate_runs(self):
        lg, entries = load_file(str(SLATE))
        self.assertEqual(len(entries), 2)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            report(lg, entries, target=50, bankroll=100)
        out = buf.getvalue()
        self.assertIn("Los Angeles Dodgers @ Atlanta Braves", out)
        self.assertIn("Long shots paying ~50x", out)


if __name__ == "__main__":
    unittest.main()
