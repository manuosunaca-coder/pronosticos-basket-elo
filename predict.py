#!/usr/bin/env python3
"""
Pronósticos Basket Elo — genera data.json para el widget de pronosticosbasketelo.blogspot.com

Fuentes (gratis, sin clave):
  · Euroliga: API oficial api-live.euroleague.net (calendario y resultados)
  · Liga Endesa (ACB): TheSportsDB, jornada a jornada
Modelo: rating Elo con ventaja de campo y peso por diferencia de puntos (sin empates).
Solo usa la librería estándar de Python.
"""
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from elo_core import (CARRY, HOME_ADV, START, arrow, backtest_accuracy, confidence, predict, run)

MAD = ZoneInfo("Europe/Madrid")
OUT = os.environ.get("OUT_DIR", os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(OUT, "cache")
UA = {"User-Agent": "Mozilla/5.0 (compatible; pronosticos-basket-elo/1.0)", "Accept": "application/json"}
LEAGUES = {"ACB": ("Liga Endesa", "es"), "EL": ("Euroliga", "eu")}
ACB_ROUNDS = 34
SEASONS_BACK = 3
STRONG = 7          # confianza a partir de la que se considera "pronóstico fuerte"
DAYS_AHEAD = 10
HISTORY_KEEP = 3000


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def get_json(url, tries=3, pause=0.0):
    for i in range(tries):
        try:
            if pause:
                time.sleep(pause)
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            log(f"  ! {url} ({e}) intento {i + 1}")
            time.sleep(3 + 5 * i)
    return None


def madrid(dt_utc):
    return dt_utc.astimezone(MAD)


def season_start(today):
    return today.year if today.month >= 8 else today.year - 1


def cached(name, loader, final):
    """Temporadas ya terminadas se guardan en cache/ para no descargarlas cada día."""
    os.makedirs(CACHE, exist_ok=True)
    fp = os.path.join(CACHE, name + ".json")
    if final and os.path.exists(fp):
        with open(fp, encoding="utf-8") as f:
            return json.load(f)
    games = loader()
    if games and final:
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(games, f, ensure_ascii=False)
    return games


# ------------------------------------------------------------------ Euroliga
def load_el(y):
    d = get_json(f"https://api-live.euroleague.net/v2/competitions/E/seasons/E{y}/games")
    out = []
    for g in (d or {}).get("data", []):
        try:
            dt = datetime.fromisoformat(g["utcDate"].replace("Z", "+00:00"))
        except Exception:  # noqa
            continue
        loc = madrid(dt)
        played = bool(g.get("played"))
        out.append({
            "lg": "EL", "season": y, "date": loc.date().isoformat(), "time": loc.strftime("%H:%M"),
            "home": g["local"]["club"]["name"], "away": g["road"]["club"]["name"],
            "hs": g["local"].get("score") if played else None,
            "as": g["road"].get("score") if played else None,
            "round": f'J{g.get("round")}' if (g.get("phaseType") or {}).get("code") == "RS" else (g.get("phaseType") or {}).get("name", ""),
            "confirmed": bool(g.get("confirmedDate")) and bool(g.get("confirmedHour")),
        })
    log(f"  Euroliga {y}: {len(out)} partidos")
    return out


# ------------------------------------------------------------------ ACB
def load_acb(y):
    s = f"{y}-{y + 1}"
    out = []
    empty = 0
    for r in range(1, ACB_ROUNDS + 1):
        d = get_json(f"https://www.thesportsdb.com/api/v1/json/123/eventsround.php?id=4408&r={r}&s={s}", pause=2.2)
        ev = (d or {}).get("events") or []
        if not ev:
            empty += 1
            if empty >= 3 and r > 3:
                break
            continue
        empty = 0
        for e in ev:
            ts = e.get("strTimestamp") or ""
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "")).replace(tzinfo=timezone.utc)
            except Exception:  # noqa
                try:
                    dt = datetime.fromisoformat(e["dateEvent"] + "T18:00:00").replace(tzinfo=timezone.utc)
                except Exception:  # noqa
                    continue
            loc = madrid(dt)
            hs, as_ = e.get("intHomeScore"), e.get("intAwayScore")
            played = (e.get("strStatus") in ("FT", "AOT", "Match Finished")) or (hs not in (None, "") and as_ not in (None, "") and dt < datetime.now(timezone.utc) - timedelta(hours=3))
            out.append({
                "lg": "ACB", "season": y, "date": loc.date().isoformat(), "time": loc.strftime("%H:%M"),
                "home": e["strHomeTeam"], "away": e["strAwayTeam"],
                "hs": int(hs) if played and hs not in (None, "") else None,
                "as": int(as_) if played and as_ not in (None, "") else None,
                "round": f"J{r}", "confirmed": True, "venue": e.get("strVenue") or "",
            })
    log(f"  ACB {s}: {len(out)} partidos")
    return out


# ------------------------------------------------------------------ historial
def key_of(g):
    return f'{g["lg"]}|{g["date"]}|{g["home"]}|{g["away"]}'


def settle(history, games):
    res = {key_of(g): g for g in games if g["hs"] is not None}
    # el mismo partido puede cambiar de fecha: buscar también por equipos y temporada
    by_teams = {(g["lg"], g["home"], g["away"], g["season"]): g for g in games if g["hs"] is not None}
    for p in history:
        if p.get("result"):
            continue
        g = res.get(p["key"]) or by_teams.get((p["lg"], p["home"], p["away"], p.get("season")))
        if not g:
            continue
        home_won = g["hs"] > g["as"]
        p["score"] = f'{g["hs"]}-{g["as"]}'
        p["result"] = "1" if home_won else "2"
        p["win"] = p["result"] == p["pick"]
        fav_margin = (g["hs"] - g["as"]) if p["pick"] == "1" else (g["as"] - g["hs"])
        p["margin_err"] = round(fav_margin - p["margin"], 1)


def stats(ps):
    if not ps:
        return {"n": 0, "hits": 0, "hit_rate": 0}
    h = sum(1 for p in ps if p["win"])
    return {"n": len(ps), "hits": h, "hit_rate": round(100 * h / len(ps), 1)}


# ------------------------------------------------------------------ principal
def main():
    now = datetime.now(timezone.utc)
    today = madrid(now).date()
    cur = season_start(today)
    seasons = list(range(cur - SEASONS_BACK + 1, cur + 1))
    games = []
    log("Euroliga…")
    for y in seasons:
        games += cached(f"EL_{y}", lambda y=y: load_el(y), final=y < cur)
    log("ACB…")
    for y in seasons:
        games += cached(f"ACB_{y}", lambda y=y: load_acb(y), final=y < cur)
    played = [g for g in games if g["hs"] is not None]
    if len(played) < 300:
        log("Muy pocos partidos; no se actualiza nada.")
        sys.exit(1)
    log(f"Partidos jugados: {len(played)}")
    st = run(games)

    hist_path = os.path.join(OUT, "history.json")
    history = json.load(open(hist_path, encoding="utf-8")) if os.path.exists(hist_path) else []
    settle(history, games)

    upcoming = []
    limit = today + timedelta(days=DAYS_AHEAD)
    for g in games:
        if g["hs"] is not None:
            continue
        d = datetime.fromisoformat(g["date"]).date()
        if d < today or d > limit:
            continue
        rh, ra, p, margin = predict(st, g)
        pick = "1" if p >= 0.5 else "2"
        pf = p if pick == "1" else 1 - p
        lname, flag = LEAGUES[g["lg"]]
        rec_h = st["rec"].get((g["lg"], g["home"], g["season"]), [0, 0])
        rec_a = st["rec"].get((g["lg"], g["away"], g["season"]), [0, 0])
        upcoming.append({
            "key": key_of(g), "lg": g["lg"], "league": lname, "flag": flag, "season": g["season"],
            "date": g["date"], "time": g["time"], "round": g.get("round", ""),
            "home": g["home"], "away": g["away"],
            "elo_h": round(rh), "elo_a": round(ra),
            "tr_h": arrow(st, g["lg"], g["home"]), "tr_a": arrow(st, g["lg"], g["away"]),
            "rec_h": rec_h, "rec_a": rec_a,
            "p_home": round(100 * p, 1), "p_away": round(100 * (1 - p), 1),
            "pick": pick, "pick_prob": round(100 * pf, 1),
            "margin": round(abs(margin), 1), "conf": confidence(pf),
        })
    seen = set()
    upcoming = [u for u in upcoming if not (u["key"] in seen or seen.add(u["key"]))]
    upcoming.sort(key=lambda u: (u["date"], u["time"], -u["conf"]))
    log(f"Pronósticos: {len(upcoming)}")

    known = {p["key"]: p for p in history}
    for u in upcoming:
        if u["key"] in known:
            p = known[u["key"]]
            if not p.get("result"):
                p.update({k: u[k] for k in ("pick", "pick_prob", "margin", "conf", "time")})
            continue
        history.append({k: u[k] for k in ("key", "lg", "league", "flag", "season", "date", "time", "round",
                                          "home", "away", "pick", "pick_prob", "margin", "conf")}
                       | {"created": now.isoformat(timespec="minutes")})
    history.sort(key=lambda p: (p["date"], p.get("time", "")))
    history = history[-HISTORY_KEEP:]
    settled = [p for p in history if p.get("result")]
    strong = [p for p in settled if p["conf"] >= STRONG]
    month = today.strftime("%Y-%m")

    # ranking por competición (temporada actual)
    leagues = []
    for lg, (lname, flag) in LEAGUES.items():
        teams = {g["home"] for g in games if g["lg"] == lg and g["season"] == cur} | \
                {g["away"] for g in games if g["lg"] == lg and g["season"] == cur}
        rows = []
        for t in teams:
            k = (lg, t)
            e = st["elo"].get(k, START)
            if st["season_of"].get(k) not in (None, cur):
                e = START + CARRY * (e - START)
            w, l = st["rec"].get((lg, t, cur), [0, 0])
            rows.append({"team": t, "elo": round(e), "tr": arrow(st, lg, t), "w": w, "l": l})
        rows.sort(key=lambda r: -r["elo"])
        leagues.append({"lg": lg, "league": lname, "flag": flag, "teams": rows})

    # acierto del modelo en lo que va de temporada (Elo calculado antes de cada partido)
    calib_cur = [c for c, g in zip(st["calib"], sorted(played, key=lambda g: (g["date"], g.get("time", ""))))
                 if g["season"] == cur]
    by_lg = defaultdict(list)
    for c, g in zip(st["calib"], sorted(played, key=lambda g: (g["date"], g.get("time", "")))):
        if g["season"] == cur:
            by_lg[g["lg"]].append(c)

    recent_games = sorted([g for g in played if (today - datetime.fromisoformat(g["date"]).date()).days <= 10],
                          key=lambda g: (g["date"], g["time"]), reverse=True)

    data = {
        "generated": now.isoformat(timespec="minutes"),
        "season": f"{cur}-{(cur + 1) % 100:02d}",
        "upcoming": upcoming,
        "recent": list(reversed(settled[-200:])),
        "last_games": [{k: g[k] for k in ("lg", "date", "time", "round", "home", "away", "hs", "as")} for g in recent_games[:60]],
        "stats": {
            "all": stats(settled[-300:]), "strong": stats(strong[-300:]),
            "month": stats([p for p in settled if p["date"].startswith(month)]),
            "strong_month": stats([p for p in strong if p["date"].startswith(month)]),
            "season_model": {"n": len(calib_cur), "hit_rate": backtest_accuracy(calib_cur)},
            "season_by_lg": {lg: {"n": len(v), "hit_rate": backtest_accuracy(v)} for lg, v in by_lg.items()},
            "all_model": {"n": len(st["calib"]), "hit_rate": backtest_accuracy(st["calib"])},
        },
        "leagues": leagues,
        "model": {"games": len(played), "seasons": len(seasons), "home_adv": HOME_ADV, "strong": STRONG},
    }
    with open(os.path.join(OUT, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=0)
    log("OK")


if __name__ == "__main__":
    main()
