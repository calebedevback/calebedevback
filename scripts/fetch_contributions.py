#!/usr/bin/env python3
"""Baixa as contribuições públicas do GitHub (sem token) e salva data/contributions.json."""
import datetime as dt
import json
import os
import re
import sys
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_USER") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not USER:
    sys.exit("defina GH_USER ou passe o usuário como argumento")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "contributions.json")


def fetch():
    r = requests.get(f"https://github.com/users/{USER}/contributions",
                     headers={"User-Agent": "profile-readme/1.0"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        txt = tips.get(td.get("id"), "")
        m = re.match(r"(\d[\d,]*)", txt)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": date, "count": count, "level": int(td.get("data-level") or 0)})
    if not days:
        sys.exit("nenhum dia encontrado — o HTML do GitHub pode ter mudado")
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    best = (0, None, None)
    run, start = 0, None
    for d in days:
        if d["count"] > 0:
            run += 1
            start = start or d["date"]
            if run > best[0]:
                best = (run, start, d["date"])
        else:
            run, start = 0, None
    i = len(days) - 1
    if days[i]["count"] == 0:
        i -= 1  # hoje ainda não acabou
    end, cur = i, 0
    while i >= 0 and days[i]["count"] > 0:
        cur += 1
        i -= 1
    current = (cur, days[i + 1]["date"] if cur else None, days[end]["date"] if cur else None)
    return current, best


def main():
    days = fetch()
    total = sum(d["count"] for d in days)
    active = [d for d in days if d["count"] > 0]
    best_day = max(days, key=lambda d: d["count"])
    months = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    cur, longest = streaks(days)
    data = {
        "user": USER,
        "generated": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": total,
        "active_days": len(active),
        "active_pct": round(100 * len(active) / len(days)),
        "avg_active": round(total / len(active), 1) if active else 0,
        "best_day": best_day,
        "current_streak": {"days": cur[0], "start": cur[1], "end": cur[2]},
        "longest_streak": {"days": longest[0], "start": longest[1], "end": longest[2]},
        "months": [{"month": k, "count": v} for k, v in months.items()],
        "days": days,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print(f"{USER}: {total} contribuições, streak atual {cur[0]}, maior {longest[0]}")


if __name__ == "__main__":
    main()
