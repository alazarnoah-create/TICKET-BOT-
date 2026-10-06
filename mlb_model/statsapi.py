"""Pulls what the model needs from MLB's free Stats API (statsapi.mlb.com, no key needed):
the day's schedule with probable pitchers, league averages, team and pitcher season stats."""
from __future__ import annotations

import json
import ssl
import urllib.parse
import urllib.request

from .model import League, Matchup, Pitcher, Team

BASE = "https://statsapi.mlb.com/api/v1"
POSTSEASON_TYPES = {"F", "D", "L", "W"}  # wild card, division series, LCS, World Series


def http_json(url: str):
    try:
        import certifi  # macOS Python often lacks root certificates
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = None
    req = urllib.request.Request(url, headers={"User-Agent": "mlb-model/1.0"})
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        return json.load(resp)


def get(path: str, **params) -> dict:
    return http_json(f"{BASE}/{path}?{urllib.parse.urlencode(params)}")


def innings(ip) -> float:
    """'180.1' means 180 and one third."""
    whole, _, outs = str(ip or "0").partition(".")
    return int(whole) + int(outs or 0) / 3


def _splits(data: dict) -> list[dict]:
    stats = data.get("stats") or []
    return stats[0].get("splits", []) if stats else []


def _combined(splits: list[dict]) -> dict:
    """One stat line; a traded player gets a split per team, so add those up."""
    if not splits:
        return {}
    if len(splits) == 1 or any("team" not in s for s in splits):
        return next((s["stat"] for s in splits if "team" not in s), splits[0]["stat"])
    total: dict = {}
    for s in splits:
        for key, val in s["stat"].items():
            if key == "inningsPitched":
                total["_ip"] = total.get("_ip", 0) + innings(val)
            elif isinstance(val, int):
                total[key] = total.get(key, 0) + val
    total["inningsPitched"] = total.pop("_ip", 0)
    total["era"] = 9 * total.get("earnedRuns", 0) / total["inningsPitched"] if total["inningsPitched"] else None
    return total


def league(season: int) -> League:
    hit = [s["stat"] for s in _splits(get("teams/stats", stats="season", group="hitting",
                                          season=season, sportIds=1))]
    pit = [s["stat"] for s in _splits(get("teams/stats", stats="season", group="pitching",
                                          season=season, sportIds=1))]
    if not hit or not pit:
        return League()
    ip = sum(innings(s["inningsPitched"]) for s in pit)
    tot = {k: sum(s.get(k, 0) for s in pit)
           for k in ("earnedRuns", "homeRuns", "baseOnBalls", "hitByPitch", "strikeOuts")}
    era = 9 * tot["earnedRuns"] / ip
    raw_fip = (13 * tot["homeRuns"] + 3 * (tot["baseOnBalls"] + tot["hitByPitch"])
               - 2 * tot["strikeOuts"]) / ip
    return League(rpg=sum(s["runs"] for s in hit) / sum(s["gamesPlayed"] for s in hit),
                  era=era, fip_const=era - raw_fip, hr9=9 * tot["homeRuns"] / ip)


def team(team_id: int, name: str, season: int, lg: League) -> Team:
    path = f"teams/{team_id}/stats"
    h = _combined(_splits(get(path, stats="season", group="hitting", season=season)))
    p = _combined(_splits(get(path, stats="season", group="pitching", season=season)))
    t = Team(name, games=h.get("gamesPlayed") or 1, runs_scored=h.get("runs", 0),
             runs_allowed=p.get("runs", 0), ops=float(h["ops"]) if h.get("ops") else None)
    try:  # platoon splits and bullpen line are nice-to-haves
        for s in _splits(get(path, stats="statSplits", group="hitting", season=season, sitCodes="vl,vr")):
            code = s.get("split", {}).get("code")
            if code in ("vl", "vr") and s["stat"].get("ops"):
                t.ops_vs["L" if code == "vl" else "R"] = float(s["stat"]["ops"])
        rp = _splits(get(path, stats="statSplits", group="pitching", season=season, sitCodes="rp"))
        if rp:
            st = rp[0]["stat"]
            ip = innings(st.get("inningsPitched"))
            if ip > 50:
                t.bullpen_era = 9 * st.get("earnedRuns", 0) / ip
                t.bullpen_fip = (13 * st.get("homeRuns", 0) + 3 * (st.get("baseOnBalls", 0)
                                 + st.get("hitByPitch", 0)) - 2 * st.get("strikeOuts", 0)) / ip + lg.fip_const
    except Exception:  # noqa: BLE001 - the model works without them
        pass
    return t


def pitcher(pid: int | None, name: str, season: int) -> Pitcher:
    if not pid:
        return Pitcher(name or "TBD")
    person = get(f"people/{pid}", hydrate=f"stats(group=[pitching],type=[season],season={season})")["people"][0]
    st = _combined(_splits(person))
    era = st.get("era")
    return Pitcher(
        name=person.get("fullName", name), hand=person.get("pitchHand", {}).get("code", "R"),
        ip=innings(st.get("inningsPitched")), era=float(era) if era not in (None, "-.--") else None,
        k=st.get("strikeOuts"), bb=st.get("baseOnBalls"), hbp=st.get("hitByPitch", 0),
        hr=st.get("homeRuns"), gs=st.get("gamesStarted"), bf=st.get("battersFaced"),
        whip=float(st["whip"]) if st.get("whip") not in (None, "-.--") else None)


def matchups(day: str) -> tuple[League, list[dict]]:
    """Every game on `day` (YYYY-MM-DD) as {"label", "info", "matchup"}."""
    season = int(day[:4])
    lg = league(season)
    out = []
    data = get("schedule", sportId=1, date=day, hydrate="probablePitcher,team,venue,seriesStatus")
    for d in data.get("dates", []):
        for g in d.get("games", []):
            a, h = g["teams"]["away"], g["teams"]["home"]
            asp, hsp = a.get("probablePitcher") or {}, h.get("probablePitcher") or {}
            m = Matchup(
                away=team(a["team"]["id"], a["team"]["name"], season, lg),
                home=team(h["team"]["id"], h["team"]["name"], season, lg),
                away_sp=pitcher(asp.get("id"), asp.get("fullName", "TBD"), season),
                home_sp=pitcher(hsp.get("id"), hsp.get("fullName", "TBD"), season),
                postseason=g.get("gameType") in POSTSEASON_TYPES)
            series = (g.get("seriesStatus") or {}).get("description") or g.get("seriesDescription", "")
            out.append({"label": f"{m.away.name} @ {m.home.name}", "matchup": m,
                        "info": f"{series} | {g.get('gameDate', '')} | {g['status']['detailedState']}"})
    return lg, out
