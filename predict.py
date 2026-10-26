#!/usr/bin/env python3
"""
Pronósticos Basket Elo — genera data.json para el widget de pronosticosbasketelo.blogspot.com

Fuentes (gratis, sin clave):
  · Liga Endesa (ACB), temporada actual: calendario oficial de acb.com (resultados, horarios y TV)
  · ACB, temporadas anteriores: TheSportsDB (se descargan una vez y se guardan en cache/)
  · Euroliga: API oficial api-live.euroleague.net
Modelo: rating Elo con ventaja de campo y peso por diferencia de puntos (sin empates).
Solo usa la librería estándar de Python.
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from elo_core import CARRY, HOME_ADV, START, arrow, backtest_accuracy, confidence, predict, run

MAD = ZoneInfo("Europe/Madrid")
OUT = os.environ.get("OUT_DIR", os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(OUT, "cache")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
      "Accept": "text/html,application/json,*/*", "Accept-Language": "es-ES,es;q=0.9"}
LEAGUES = {"ACB": ("Liga Endesa", "es"), "EL": ("Euroliga", "eu")}
SEASONS_BACK = 3
STRONG = 7
DAYS_AHEAD = 10
HISTORY_KEEP = 3000
TSDB_BUDGET = 40   # máximo de peticiones a TheSportsDB por ejecución (límite de la API gratis)

# Equivalencias de nombres ACB (TheSportsDB usa nombres distintos a acb.com)
ACB_KEYS = [
    ("tenerife", ["canarias", "tenerife", "1939", "laguna"]), ("barca", ["barcelona", "barca"]),
    ("unicaja", ["unicaja", "malaga"]), ("grancanaria", ["gran canaria", "dreamland", "herbalife"]),
    ("baskonia", ["baskonia", "vitoria"]), ("joventut", ["joventut", "badalona"]), ("manresa", ["manresa"]),
    ("girona", ["girona"]), ("zaragoza", ["zaragoza"]), ("granada", ["granada"]), ("lleida", ["lleida"]),
    ("andorra", ["andorra"]), ("realmadrid", ["real madrid"]), ("burgos", ["burgos", "san pablo"]),
    ("breogan", ["breogan"]), ("bilbao", ["bilbao"]), ("murcia", ["murcia"]), ("valencia", ["valencia"]),
    ("obradoiro", ["obradoiro"]), ("palencia", ["palencia"]), ("fuenlabrada", ["fuenlabrada"]),
    ("estudiantes", ["estudiantes"]), ("betis", ["betis", "sevilla"]),
]


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s)


def acb_key(name):
    n = norm(name)
    for k, words in ACB_KEYS:
        if any(w in n for w in words):
            return k
    return re.sub(r"[^a-z0-9]", "", n)


def http(url, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def get_json(url, tries=3):
    for i in range(tries):
        try:
            return json.loads(http(url).decode("utf-8"))
        except urllib.error.HTTPError as e:
            log(f"  ! HTTP {e.code} {url[:90]}")
            time.sleep(70 if e.code == 429 else 4 + 6 * i)
        except Exception as e:  # noqa
            log(f"  ! {e} {url[:90]}")
            time.sleep(4 + 6 * i)
    return None


def season_start(today):
    return today.year if today.month >= 8 else today.year - 1


def save_cache(name, games):
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(games, f, ensure_ascii=False)


def read_cache(name, min_games=0):
    fp = os.path.join(CACHE, name + ".json")
    if os.path.exists(fp):
        with open(fp, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, list) and (len(d) < min_games or (d and "hid" not in d[0])):
            return None   # caché antigua o incompleta: se vuelve a descargar
        return d
    return None


def loc(dt):
    return dt.astimezone(MAD)


# ------------------------------------------------------------------ Euroliga
def load_el(y):
    d = get_json(f"https://api-live.euroleague.net/v2/competitions/E/seasons/E{y}/games")
    out = []
    for g in (d or {}).get("data", []):
        try:
            t = loc(datetime.fromisoformat(g["utcDate"].replace("Z", "+00:00")))
        except Exception:  # noqa
            continue
        played = bool(g.get("played"))
        ph = (g.get("phaseType") or {}).get("code")
        out.append({
            "lg": "EL", "season": y, "date": t.date().isoformat(), "time": t.strftime("%H:%M"),
            "home": g["local"]["club"]["name"], "away": g["road"]["club"]["name"],
            "hid": g["local"]["club"]["code"], "aid": g["road"]["club"]["code"],
            "hs": g["local"].get("score") if played else None, "as": g["road"].get("score") if played else None,
            "round": f'J{g.get("round")}' if ph == "RS" else (g.get("phaseType") or {}).get("name", ""),
            "tv": "",
        })
    log(f"  Euroliga {y}: {len(out)} partidos, {sum(1 for x in out if x['hs'] is not None)} jugados")
    return out


# ------------------------------------------------------------------ ACB (acb.com)
def load_acb_official():
    try:
        h = http("https://acb.com/es/liga/calendario", timeout=60).decode("utf-8", "ignore")
    except Exception as e:  # noqa
        log("  ! acb.com:", e)
        return [], None
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', h)
    s = "".join(json.loads('"' + c + '"') for c in chunks)
    j = s.find('"rounds":[')
    k = s.rfind('"teams":[', 0, j)
    if j < 0 or k < 0:
        log("  ! acb.com: no se encuentra el calendario en la página")
        return [], None
    dec = json.JSONDecoder()
    teams, _ = dec.raw_decode(s[k + 8:])
    rounds, _ = dec.raw_decode(s[j + 9:])

    def team(ref):
        try:
            return teams[int(str(ref).rsplit(":", 1)[1])]
        except Exception:  # noqa
            return {"fullName": str(ref)}
    out, year = [], None
    for r in rounds:
        for m in r.get("matches", []):
            if m.get("matchStatus") == "UNSCHEDULED" or not m.get("startDateTime"):
                continue
            year = m.get("seasonStartYear") or year
            t = loc(datetime.fromisoformat(m["startDateTime"].replace("Z", "+00:00")))
            ht, at = team(m["homeTeam"]), team(m["awayTeam"])
            fin = m.get("matchStatus") == "FINALIZED"
            tv = ", ".join(c["name"] for c in ((m.get("broadcastChannels") or {}).get("primary") or [])[:3])
            out.append({
                "lg": "ACB", "season": m.get("seasonStartYear"), "date": t.date().isoformat(), "time": t.strftime("%H:%M"),
                "home": ht.get("fullName"), "away": at.get("fullName"),
                "hid": acb_key(ht.get("fullName", "")), "aid": acb_key(at.get("fullName", "")),
                "hs": m.get("homeTeamScore") if fin else None, "as": m.get("awayTeamScore") if fin else None,
                "round": f'J{r.get("roundNumber")}', "tv": tv,
            })
    log(f"  ACB oficial {year}: {len(out)} partidos, {sum(1 for x in out if x['hs'] is not None)} jugados")
    return out, year


# ------------------------------------------------------------------ ACB (TheSportsDB, temporadas pasadas)
def load_acb_tsdb(y, budget):
    """Descarga jornada a jornada. Guarda el progreso parcial para continuar en la siguiente ejecución."""
    name = f"ACB_{y}"
    part = read_cache(name + "_partial") or {"rounds": {}, "done": False}
    used = 0
    for r in range(1, 35):
        if str(r) in part["rounds"]:
            continue
        if used >= budget:
            break
        d = get_json(f"https://www.thesportsdb.com/api/v1/json/123/eventsround.php?id=4408&r={r}&s={y}-{y + 1}")
        used += 1
        time.sleep(2.5)
        if d is None:
            break
        part["rounds"][str(r)] = (d or {}).get("events") or []
    complete = all(str(r) in part["rounds"] for r in range(1, 35))
    out = []
    for r, evs in part["rounds"].items():
        for e in evs:
            try:
                t = loc(datetime.fromisoformat((e.get("strTimestamp") or "").replace("Z", "")).replace(tzinfo=timezone.utc))
                hs, as_ = int(e["intHomeScore"]), int(e["intAwayScore"])
            except Exception:  # noqa
                continue
            out.append({"lg": "ACB", "season": y, "date": t.date().isoformat(), "time": t.strftime("%H:%M"),
                        "home": e["strHomeTeam"], "away": e["strAwayTeam"],
                        "hid": acb_key(e["strHomeTeam"]), "aid": acb_key(e["strAwayTeam"]),
                        "hs": hs, "as": as_, "round": f"J{r}", "tv": ""})
    if complete:
        save_cache(name, out)
        fp = os.path.join(CACHE, name + "_partial.json")
        if os.path.exists(fp):
            os.remove(fp)
    else:
        save_cache(name + "_partial", part)
    log(f"  ACB {y} (TheSportsDB): {len(out)} partidos, {len(part['rounds'])}/34 jornadas, {used} peticiones")
    return out, used


# ------------------------------------------------------------------ historial
def key_of(g):
    return f'{g["lg"]}|{g["date"]}|{g["home"]}|{g["away"]}'


def settle(history, games):
    res = {key_of(g): g for g in games if g["hs"] is not None}
    by_ids = {(g["lg"], g.get("hid"), g.get("aid"), g["season"]): g for g in games if g["hs"] is not None}
    for p in history:
        if p.get("result"):
            continue
        g = res.get(p["key"]) or by_ids.get((p["lg"], p.get("hid"), p.get("aid"), p.get("season")))
        if not g:
            continue
        home_won = g["hs"] > g["as"]
        p["score"] = f'{g["hs"]}-{g["as"]}'
        p["result"] = "1" if home_won else "2"
        p["win"] = p["result"] == p["pick"]


def stats(ps):
    if not ps:
        return {"n": 0, "hits": 0, "hit_rate": 0}
    h = sum(1 for p in ps if p["win"])
    return {"n": len(ps), "hits": h, "hit_rate": round(100 * h / len(ps), 1)}


# ------------------------------------------------------------------ principal
def main():
    now = datetime.now(timezone.utc)
    today = loc(now).date()
    cur = season_start(today)
    seasons = list(range(cur - SEASONS_BACK + 1, cur + 1))
    games = []

    log("Euroliga…")
    for y in seasons:
        g = read_cache(f"EL_{y}", 250) if y < cur else None
        if g is None:
            g = load_el(y)
            if y < cur and len(g) > 250:
                save_cache(f"EL_{y}", g)
        games += g

    log("ACB…")
    acb_cur, acb_year = load_acb_official()
    if acb_year and acb_year != cur:
        log(f"  aviso: acb.com muestra la temporada {acb_year}")
    games += acb_cur
    budget = TSDB_BUDGET
    for y in seasons[:-1]:
        g = read_cache(f"ACB_{y}", 280)
        if g is None:
            g, used = load_acb_tsdb(y, budget)
            budget -= used
        games += g

    played = [g for g in games if g["hs"] is not None]
    if len(played) < 300 or not acb_cur:
        log(f"Datos insuficientes (jugados={len(played)}, acb={len(acb_cur)}); no se actualiza data.json.")
        sys.exit(0 if os.path.exists(os.path.join(OUT, "data.json")) else 1)
    log(f"Partidos jugados: {len(played)}")
    st = run(games)
    order = sorted(played, key=lambda g: (g["date"], g.get("time", "")))

    # nombre más reciente de cada equipo
    disp = {}
    for g in sorted(games, key=lambda g: (g["season"], g["date"])):
        disp[(g["lg"], g["hid"])] = g["home"]
        disp[(g["lg"], g["aid"])] = g["away"]

    hist_path = os.path.join(OUT, "history.json")
    history = json.load(open(hist_path, encoding="utf-8")) if os.path.exists(hist_path) else []
    settle(history, games)

    upcoming, seen = [], set()
    limit = today + timedelta(days=DAYS_AHEAD)
    for g in games:
        if g["hs"] is not None or g["season"] != cur:
            continue
        d = datetime.fromisoformat(g["date"]).date()
        if d < today or d > limit or key_of(g) in seen:
            continue
        seen.add(key_of(g))
        rh, ra, p, margin = predict(st, g)
        pick = "1" if p >= 0.5 else "2"
        pf = p if pick == "1" else 1 - p
        lname, flag = LEAGUES[g["lg"]]
        upcoming.append({
            "key": key_of(g), "lg": g["lg"], "league": lname, "flag": flag, "season": g["season"],
            "date": g["date"], "time": g["time"], "round": g.get("round", ""), "tv": g.get("tv", ""),
            "home": g["home"], "away": g["away"], "hid": g["hid"], "aid": g["aid"],
            "elo_h": round(rh), "elo_a": round(ra),
            "tr_h": arrow(st, g["lg"], g["hid"]), "tr_a": arrow(st, g["lg"], g["aid"]),
            "rec_h": st["rec"].get((g["lg"], g["hid"], cur), [0, 0]),
            "rec_a": st["rec"].get((g["lg"], g["aid"], cur), [0, 0]),
            "p_home": round(100 * p, 1), "p_away": round(100 * (1 - p), 1),
            "pick": pick, "pick_prob": round(100 * pf, 1), "margin": round(abs(margin), 1), "conf": confidence(pf),
        })
    upcoming.sort(key=lambda u: (u["date"], u["time"], -u["conf"]))
    log(f"Pronósticos: {len(upcoming)}")

    known = {p["key"]: p for p in history}
    for u in upcoming:
        p = known.get(u["key"])
        if p:
            if not p.get("result"):
                p.update({k: u[k] for k in ("pick", "pick_prob", "margin", "conf", "time")})
            continue
        history.append({k: u[k] for k in ("key", "lg", "league", "flag", "season", "date", "time", "round",
                                          "home", "away", "hid", "aid", "pick", "pick_prob", "margin", "conf")}
                       | {"created": now.isoformat(timespec="minutes")})
    history.sort(key=lambda p: (p["date"], p.get("time", "")))
    history = history[-HISTORY_KEEP:]
    settled = [p for p in history if p.get("result")]
    strong = [p for p in settled if p["conf"] >= STRONG]
    month = today.strftime("%Y-%m")

    leagues = []
    for lg, (lname, flag) in LEAGUES.items():
        ids = {g["hid"] for g in games if g["lg"] == lg and g["season"] == cur} | \
              {g["aid"] for g in games if g["lg"] == lg and g["season"] == cur}
        rows = []
        for t in ids:
            k = (lg, t)
            e = st["elo"].get(k, START)
            if st["season_of"].get(k) not in (None, cur):
                e = START + CARRY * (e - START)
            w, l = st["rec"].get((lg, t, cur), [0, 0])
            rows.append({"team": disp.get(k, t), "elo": round(e), "tr": arrow(st, lg, t), "w": w, "l": l})
        rows.sort(key=lambda r: -r["elo"])
        leagues.append({"lg": lg, "league": lname, "flag": flag, "teams": rows})

    by_lg = defaultdict(list)
    for c, g in zip(st["calib"], order):
        if g["season"] == cur:
            by_lg[g["lg"]].append(c)
    cur_all = by_lg["ACB"] + by_lg["EL"]
    recent_games = sorted([g for g in played if g["season"] == cur and (today - datetime.fromisoformat(g["date"]).date()).days <= 14],
                          key=lambda g: (g["date"], g["time"]), reverse=True)

    data = {
        "generated": now.isoformat(timespec="minutes"),
        "season": f"{cur}-{(cur + 1) % 100:02d}",
        "upcoming": upcoming,
        "recent": list(reversed(settled[-200:])),
        "last_games": [{k: g[k] for k in ("lg", "date", "time", "round", "home", "away", "hs", "as")} for g in recent_games[:80]],
        "stats": {
            "all": stats(settled[-300:]), "strong": stats(strong[-300:]),
            "month": stats([p for p in settled if p["date"].startswith(month)]),
            "strong_month": stats([p for p in strong if p["date"].startswith(month)]),
            "season_model": {"n": len(cur_all), "hit_rate": backtest_accuracy(cur_all)},
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
