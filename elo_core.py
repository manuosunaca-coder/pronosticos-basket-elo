"""Motor Elo de baloncesto (sin empates). Entrada: lista de partidos normalizados.

Partido: {"lg": "ACB"|"EL", "season": 2025, "date": "YYYY-MM-DD", "time": "HH:MM" (hora de Madrid),
          "home": str, "away": str, "hs": int|None, "as": int|None, "round": str}
"""
import math
from collections import defaultdict

K = 20.0
HOME_ADV = {"ACB": 75.0, "EL": 85.0}   # ventaja de jugar en casa en puntos Elo
START = 1500.0
CARRY = 0.70                           # entre temporadas se conserva el 70 % de la distancia a 1500
ELO_PER_POINT = 28.0                   # 28 puntos Elo ≈ 1 punto en el marcador


def mov_mult(margin, elo_diff_winner):
    return ((abs(margin) + 3) ** 0.8) / (7.5 + 0.006 * elo_diff_winner)


def win_prob(dr):
    return 1.0 / (1.0 + 10 ** (-dr / 400.0))


def run(games):
    """Recorre los partidos jugados en orden. Devuelve estado del modelo."""
    elo = {}           # (lg, team) -> rating  (cada competición tiene su propia escala)
    season_of = {}
    trend = defaultdict(list)
    rec = defaultdict(lambda: [0, 0])  # (lg, team, season) -> [victorias, derrotas]
    played = [g for g in games if g["hs"] is not None and g["as"] is not None]
    played.sort(key=lambda g: (g["date"], g.get("time", "")))
    calib = []         # (prob local del modelo, ganó local) para medir el acierto histórico
    for g in played:
        lg, s = g["lg"], g["season"]
        for t in (g["home"], g["away"]):
            k = (lg, t)
            if k in elo and season_of[k] != s:
                elo[k] = START + CARRY * (elo[k] - START)
            elo.setdefault(k, START)
            season_of[k] = s
        kh, ka = (lg, g["home"]), (lg, g["away"])
        rh, ra = elo[kh], elo[ka]
        dr = rh + HOME_ADV.get(lg, 80.0) - ra
        p = win_prob(dr)
        hw = g["hs"] > g["as"]
        calib.append((p, hw))
        margin = g["hs"] - g["as"]
        diff_w = dr if hw else -dr
        delta = K * mov_mult(margin, diff_w) * ((1.0 if hw else 0.0) - p)
        elo[kh], elo[ka] = rh + delta, ra - delta
        trend[kh] = (trend[kh] + [delta])[-5:]
        trend[ka] = (trend[ka] + [-delta])[-5:]
        rec[(lg, g["home"], s)][0 if hw else 1] += 1
        rec[(lg, g["away"], s)][1 if hw else 0] += 1
    return {"elo": elo, "trend": trend, "rec": rec, "season_of": season_of, "calib": calib, "n": len(played)}


def predict(state, g):
    lg = g["lg"]
    kh, ka = (lg, g["home"]), (lg, g["away"])
    rh = state["elo"].get(kh, START)
    ra = state["elo"].get(ka, START)
    # equipo nuevo en temporada nueva: aplica el arrastre
    for k in (kh, ka):
        if k in state["season_of"] and state["season_of"][k] != g["season"]:
            if k == kh:
                rh = START + CARRY * (rh - START)
            else:
                ra = START + CARRY * (ra - START)
    dr = rh + HOME_ADV.get(lg, 80.0) - ra
    p = win_prob(dr)
    return rh, ra, p, dr / ELO_PER_POINT


def arrow(state, lg, team):
    s = sum(state["trend"].get((lg, team), []))
    return 1 if s > 12 else (-1 if s < -12 else 0)


def confidence(p_fav):
    """1-10 según la probabilidad del favorito: 50 % -> 1, 90 % o más -> 10."""
    return max(1, min(10, int(round(1 + (p_fav - 0.50) / 0.40 * 9))))


def backtest_accuracy(calib, last=None):
    c = calib[-last:] if last else calib
    if not c:
        return 0.0
    ok = sum(1 for p, hw in c if (p >= 0.5) == hw)
    return round(100.0 * ok / len(c), 1)
