#!/usr/bin/env python3
"""Gera contrib-heatmap.svg: gráfico de contribuições animado (células aparecem uma a uma)."""
import datetime as dt
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = json.load(open(os.path.join(ROOT, "data", "contributions.json")))
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CELL, GAP, LEFT, TOP = 13, 3, 34, 24


def main():
    days = DATA["days"]
    first = dt.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # domingo = 0
    n_weeks = (offset + len(days) + 6) // 7
    width = LEFT + n_weeks * (CELL + GAP) + 6
    height = TOP + 7 * (CELL + GAP) + 26
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
           "<style>"
           "text.l{fill:#7d8590;font-size:13px;font-weight:600}"
           "text.t{fill:#e6edf3;font-size:15px;font-weight:700}"
           ".c{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .55s ease-out both}"
           "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.12)}100%{opacity:1;transform:scale(1)}}"
           "@media (prefers-reduced-motion:reduce){.c{opacity:1!important;animation:none!important}}"
           "</style>"]
    last_month = None
    for i, d in enumerate(days):
        date = dt.date.fromisoformat(d["date"])
        w, r = divmod(offset + i, 7)
        if r == 0 or i == 0:
            if date.month != last_month and (date.day <= 7 or i == 0) and w < n_weeks - 1:
                out.append(f'<text class="l" x="{LEFT + w * (CELL + GAP)}" y="16">{MONTHS[date.month - 1]}</text>')
                last_month = date.month
    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        out.append(f'<text class="l" x="2" y="{TOP + row * (CELL + GAP) + 11}">{label}</text>')
    total_cells = len(days)
    for i, d in enumerate(days):
        w, r = divmod(offset + i, 7)
        delay = 2.6 * w / max(n_weeks, 1) + 0.02 * r
        out.append(f'<rect class="c" x="{LEFT + w * (CELL + GAP)}" y="{TOP + r * (CELL + GAP)}" width="{CELL}" '
                   f'height="{CELL}" rx="2.5" fill="{COLORS[min(d["level"], 4)]}" style="animation-delay:{delay:.3f}s">'
                   f'<title>{d["date"]}: {d["count"]}</title></rect>')
    out.append(f'<text class="t" x="{LEFT}" y="{height - 6}">{DATA["total"]:,} contributions in the last year</text>')
    out.append("</svg>")
    open(os.path.join(ROOT, "contrib-heatmap.svg"), "w").write("\n".join(out))
    print("contrib-heatmap.svg ok", total_cells, "dias")


if __name__ == "__main__":
    main()
