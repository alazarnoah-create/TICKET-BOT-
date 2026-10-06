"""The prediction model: team and starter numbers -> expected runs for each side -> a full
final-score distribution, from which every market (moneyline, run line, totals, and same-game
combos of them) is read off exactly.

How expected runs are built (a multiplicative "log5"-style model, everything relative to league):

    runs = league R/G * offense index * opposing pitching index * park * home/away edge

  offense index   team runs scored per game / league, with its home park taken out, pulled
                  toward average (~13% over a full season); optionally adjusted for the
                  starter's hand (platoon OPS split)
  pitching index  starter for the innings he's expected to throw, bullpen for the rest.
                  Starter = blend of ERA and FIP (or an xFIP-style estimate when HR are unknown),
                  regressed toward league by innings pitched. Bullpen = bullpen ERA if given,
                  else team runs allowed per game.
  park            run park factor of the stadium (1.00 = neutral)

Each team's runs are a negative binomial with that mean (MLB scoring is over-dispersed: a team
averaging 4.5 runs has an SD near 3.1, more than Poisson's 2.1). Ties after nine go to extras.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, lgamma, log

DISPERSION = 4.0  # negative binomial size parameter; fits real MLB run spreads
MAX_RUNS = 30
HOME_EDGE = 0.035  # home scores 3.5% more, away 3.5% less: ~53% for evenly matched teams, as in MLB

# Rough multi-year run park factors (1.00 = neutral). Edit freely; the Stats API names teams
# as below. (id, abbreviation, park factor)
TEAMS = {
    "Arizona Diamondbacks": (109, "ARI", 1.02), "Atlanta Braves": (144, "ATL", 1.01),
    "Baltimore Orioles": (110, "BAL", 0.99), "Boston Red Sox": (111, "BOS", 1.04),
    "Chicago Cubs": (112, "CHC", 0.98), "Chicago White Sox": (145, "CWS", 0.99),
    "Cincinnati Reds": (113, "CIN", 1.05), "Cleveland Guardians": (114, "CLE", 0.97),
    "Colorado Rockies": (115, "COL", 1.12), "Detroit Tigers": (116, "DET", 0.98),
    "Houston Astros": (117, "HOU", 1.00), "Kansas City Royals": (118, "KC", 1.02),
    "Los Angeles Angels": (108, "LAA", 1.01), "Los Angeles Dodgers": (119, "LAD", 1.00),
    "Miami Marlins": (146, "MIA", 0.97), "Milwaukee Brewers": (158, "MIL", 0.98),
    "Minnesota Twins": (142, "MIN", 1.00), "New York Mets": (121, "NYM", 0.96),
    "New York Yankees": (147, "NYY", 1.00), "Athletics": (133, "ATH", 1.04),
    "Philadelphia Phillies": (143, "PHI", 1.02), "Pittsburgh Pirates": (134, "PIT", 0.98),
    "San Diego Padres": (135, "SD", 0.95), "San Francisco Giants": (137, "SF", 0.96),
    "Seattle Mariners": (136, "SEA", 0.92), "St. Louis Cardinals": (138, "STL", 0.98),
    "Tampa Bay Rays": (139, "TB", 0.98), "Texas Rangers": (140, "TEX", 0.98),
    "Toronto Blue Jays": (141, "TOR", 1.00), "Washington Nationals": (120, "WSH", 1.00),
}


def park_factor(team_name: str) -> float:
    if team_name in TEAMS:
        return TEAMS[team_name][2]
    for name, (_, abbr, pf) in TEAMS.items():  # "LAD", "Dodgers", "Oakland Athletics"...
        if team_name.upper() == abbr or name.split()[-1] == team_name.split()[-1]:
            return pf
    return 1.0


@dataclass
class League:
    rpg: float = 4.45  # runs per team per game
    era: float = 4.10
    fip_const: float = 3.10
    hr9: float = 1.15


@dataclass
class Pitcher:
    name: str
    hand: str = "R"
    ip: float = 0.0
    era: float | None = None
    fip: float | None = None
    k: int | None = None
    bb: int | None = None
    hbp: int = 0
    hr: int | None = None
    gs: int | None = None
    whip: float | None = None
    bf: int | None = None  # batters faced
    expected_ip: float | None = None  # override: how deep you expect him to go today


@dataclass
class Team:
    name: str
    games: int
    runs_scored: int
    runs_allowed: int
    park: float | None = None  # home park factor; looked up from the name if missing
    ops: float | None = None
    ops_vs: dict = field(default_factory=dict)  # {"L": .780, "R": .720}
    bullpen_era: float | None = None
    bullpen_fip: float | None = None

    @property
    def home_park(self) -> float:
        return self.park if self.park is not None else park_factor(self.name)


def regress(value: float, mean: float, n: float, k: float) -> float:
    """Shrink a noisy stat toward the mean: weight n / (n + k) on the observed value."""
    w = n / (n + k)
    return w * value + (1 - w) * mean


def effective_fip(p: Pitcher, lg: League) -> float | None:
    """FIP as given, else worked out from K, BB, HBP and HR (unknown HR: league rate, like xFIP)."""
    if p.fip is not None or p.k is None or p.bb is None or not p.ip:
        return p.fip
    hr = p.hr if p.hr is not None else lg.hr9 * p.ip / 9
    return (13 * hr + 3 * (p.bb + p.hbp) - 2 * p.k) / p.ip + lg.fip_const


def pitcher_era(p: Pitcher, lg: League) -> float:
    """Best guess at a starter's true-talent run rate on the ERA scale."""
    fip = effective_fip(p, lg)
    if p.era is None and fip is None:
        return lg.era
    if fip is None:  # ERA alone is noisy: regress harder
        return regress(p.era, lg.era, p.ip, 120)
    raw = fip if p.era is None else 0.35 * p.era + 0.65 * fip
    return regress(raw, lg.era, p.ip, 50)


def starter_innings(p: Pitcher, postseason: bool) -> float:
    if p.expected_ip is not None:
        return p.expected_ip
    ip = min(p.ip / p.gs, 6.2) if p.gs else 5.5
    return ip - 0.4 if postseason else ip  # quicker hooks in October


def offense_index(t: Team, lg: League, starter_hand: str) -> float:
    neutral = t.runs_scored / t.games / ((1 + t.home_park) / 2)  # half the games at home
    idx = regress(neutral / lg.rpg, 1.0, t.games, 25)
    if t.ops and t.ops_vs.get(starter_hand):  # platoon: runs scale roughly with OPS ^ 1.8
        idx *= 1 + 0.5 * ((t.ops_vs[starter_hand] / t.ops) ** 1.8 - 1)  # half: splits are noisy
    return idx


def bullpen_index(t: Team, lg: League, postseason: bool) -> float:
    if t.bullpen_era is not None:
        raw = t.bullpen_era if t.bullpen_fip is None else (t.bullpen_era + t.bullpen_fip) / 2
        # ~550 noisy relief innings: trust them 60%
        idx = 0.6 * raw / ((1 + t.home_park) / 2) / lg.era + 0.4
    else:
        idx = runs_allowed_index(t, lg)
    return idx * (0.90 if postseason else 1.0)  # October bullpens shrink to the best arms


def runs_allowed_index(t: Team, lg: League) -> float:
    neutral = t.runs_allowed / t.games / ((1 + t.home_park) / 2)
    return regress(neutral / lg.rpg, 1.0, t.games, 25)


def pitching_index(starter: Pitcher, team: Team, lg: League, postseason: bool) -> float:
    if starter.ip or starter.era is not None or starter.fip is not None:
        sp = pitcher_era(starter, lg) / ((1 + team.home_park) / 2) / lg.era
    else:  # unknown starter: rate his innings like the team's pitching overall
        sp = runs_allowed_index(team, lg)
    share = min(starter_innings(starter, postseason), 9) / 9
    return share * sp + (1 - share) * bullpen_index(team, lg, postseason)


@dataclass
class Matchup:
    away: Team
    home: Team
    away_sp: Pitcher
    home_sp: Pitcher
    park: float | None = None  # stadium; defaults to the home team's park
    postseason: bool = False
    weather: float = 1.0  # extra run multiplier: wind out 1.05, cold/wind in 0.95...

    def expected_runs(self, lg: League) -> tuple[float, float]:
        env = lg.rpg * (self.park or self.home.home_park) * self.weather
        env *= 0.95 if self.postseason else 1.0  # colder nights, every team's best arms
        away = env * offense_index(self.away, lg, self.home_sp.hand) * \
            pitching_index(self.home_sp, self.home, lg, self.postseason) * (1 - HOME_EDGE)
        home = env * offense_index(self.home, lg, self.away_sp.hand) * \
            pitching_index(self.away_sp, self.away, lg, self.postseason) * (1 + HOME_EDGE)
        return away, home


def runs_pmf(mean: float, size: float = DISPERSION) -> list[float]:
    """P(team scores k runs), k = 0..MAX_RUNS, negative binomial."""
    p = size / (size + mean)
    pmf = [exp(lgamma(k + size) - lgamma(size) - lgamma(k + 1) + size * log(p) + k * log(1 - p))
           for k in range(MAX_RUNS + 1)]
    total = sum(pmf)
    return [x / total for x in pmf]


class Game:
    """Final-score distribution for one game. scores[(away, home)] = probability."""

    def __init__(self, away_mean: float, home_mean: float, label: str = ""):
        self.label, self.away_mean, self.home_mean = label, away_mean, home_mean
        pa, ph = runs_pmf(away_mean), runs_pmf(home_mean)
        # extra innings: home bats last and keeps a small edge; the stronger side gets the rest
        home_x = min(0.7, max(0.3, 0.52 + 0.5 * (home_mean - away_mean) / (home_mean + away_mean)))
        self.scores: dict[tuple[int, int], float] = {}
        for a, p1 in enumerate(pa):
            for h, p2 in enumerate(ph):
                if a == h:  # tied after nine: one extra run decides it (margin 1)
                    self._add((a, h + 1), p1 * p2 * home_x)
                    self._add((a + 1, h), p1 * p2 * (1 - home_x))
                else:
                    self._add((a, h), p1 * p2)

    def _add(self, key, p):
        self.scores[key] = self.scores.get(key, 0.0) + p

    def prob(self, *conditions) -> float:
        """P(every condition holds). A condition is a function (away_runs, home_runs) -> bool."""
        return sum(p for (a, h), p in self.scores.items() if all(c(a, h) for c in conditions))

    @property
    def home_win(self) -> float:
        return self.prob(lambda a, h: h > a)

    @property
    def away_win(self) -> float:
        return 1 - self.home_win

    def total_probs(self, line: float) -> tuple[float, float, float]:
        """(over, under, push)"""
        over = self.prob(lambda a, h: a + h > line)
        under = self.prob(lambda a, h: a + h < line)
        return over, under, 1 - over - under

    def fair_total(self) -> float:
        """The total line where over and under are closest to 50/50."""
        return min((x / 2 for x in range(5, 30)),
                   key=lambda line: abs(self.total_probs(line)[0] - self.total_probs(line)[1]))


def project(m: Matchup, lg: League | None = None) -> Game:
    lg = lg or League()
    away, home = m.expected_runs(lg)
    return Game(away, home, f"{m.away.name} @ {m.home.name}")
