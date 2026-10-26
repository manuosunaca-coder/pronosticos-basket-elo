#!/usr/bin/env python3
"""Prueba qué fuentes de datos de ACB y Euroliga responden desde GitHub Actions."""
import urllib.request, json, sys

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
      "Accept": "application/json, text/plain, */*"}
CANDS = [
    ("EL v2 games", "https://api-live.euroleague.net/v2/competitions/E/seasons/E2025/games", {}),
    ("EL v1 schedules", "https://api-live.euroleague.net/v1/schedules?seasonCode=E2025", {}),
    ("EL v1 results r1", "https://api-live.euroleague.net/v1/results?seasonCode=E2025&gameNumber=1", {}),
    ("EL incrowd", "https://feeds.incrowdsports.com/provider/euroleague-feeds/v2/competitions/E/seasons/E2025/games", {}),
    ("ACB web calendario", "https://www.acb.com/calendario/index/temporada_id/2025/edicion_id/0", {}),
    ("ACB web resultados", "https://www.acb.com/resultados-clasificacion/ver/temporada_id/2025/competicion_id/1/jornada_numero/1", {}),
    ("ACB api2", "https://api2.acb.com/api/v1/openapilive/Matches/matchesbycompetitionandseason?idCompetition=1&idSeason=2025", {}),
    ("TSDB ACB 2025-2026", "https://www.thesportsdb.com/api/v1/json/123/eventsseason.php?id=4408&s=2025-2026", {}),
    ("TSDB EL 2025-2026", "https://www.thesportsdb.com/api/v1/json/123/eventsseason.php?id=4546&s=2025-2026", {}),
    ("TSDB lookup 4408", "https://www.thesportsdb.com/api/v1/json/123/lookupleague.php?id=4408", {}),
    ("ESPN acb", "https://site.api.espn.com/apis/site/v2/sports/basketball/spanish-liga-acb/scoreboard", {}),
    ("Sofascore ACB", "https://api.sofascore.com/api/v1/unique-tournament/264/seasons", {}),
]
for name, url, h in CANDS:
    try:
        req = urllib.request.Request(url, headers={**UA, **h})
        with urllib.request.urlopen(req, timeout=30) as r:
            b = r.read()
            print(f"=== {name}: HTTP {r.status} {len(b)} bytes ct={r.headers.get('Content-Type')}")
            t = b.decode("utf-8", "replace")
            print(t[:1500].replace("\n", " "))
    except Exception as e:
        print(f"=== {name}: ERROR {e}")
    sys.stdout.flush()
