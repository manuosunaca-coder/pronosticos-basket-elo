#!/usr/bin/env python3
"""Prueba 2: fuentes para la ACB. Guarda respuestas en probe/ para inspeccionarlas."""
import urllib.request, os, re, sys

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
      "Accept": "text/html,application/json,*/*", "Accept-Language": "es-ES,es;q=0.9"}
os.makedirs("probe", exist_ok=True)
CANDS = [
    ("acb_home", "https://www.acb.com/"),
    ("acb_cal_es", "https://www.acb.com/es/calendario"),
    ("acb_res_es", "https://www.acb.com/es/resultados-clasificacion"),
    ("acb_calendario", "https://www.acb.com/calendario"),
    ("acb_resultados", "https://www.acb.com/resultados-clasificacion"),
    ("tsdb_acb_2627", "https://www.thesportsdb.com/api/v1/json/123/eventsseason.php?id=4408&s=2026-2027"),
    ("tsdb_acb_r1", "https://www.thesportsdb.com/api/v1/json/123/eventsround.php?id=4408&r=1&s=2026-2027"),
    ("tsdb_acb_next", "https://www.thesportsdb.com/api/v1/json/123/eventsnextleague.php?id=4408"),
    ("tsdb_acb_past", "https://www.thesportsdb.com/api/v1/json/123/eventspastleague.php?id=4408"),
    ("bbref_acb", "https://www.basketball-reference.com/international/spain-liga-acb/2027-schedule.html"),
    ("realgm_acb", "https://basketball.realgm.com/international/league/4/Spanish-ACB/schedule"),
    ("proballers", "https://www.proballers.com/basketball/league/4/spain-liga-endesa/schedule"),
    ("eurobasket", "https://basketball.eurobasket.com/Spain/ACB/Schedule.aspx"),
    ("el_2026", "https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/games"),
]
for name, url in CANDS:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            b = r.read()
            open(f"probe/{name}.txt", "wb").write(b[:3_000_000])
            print(f"=== {name}: HTTP {r.status} {len(b)} bytes final={r.geturl()}")
    except Exception as e:
        print(f"=== {name}: ERROR {e}")
    sys.stdout.flush()
