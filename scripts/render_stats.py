#!/usr/bin/env python3
"""Gera stats.svg (840x880): cards de streak/números + barras de contribuições por mês."""
import datetime as dt
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = json.load(open(os.path.join(ROOT, "data", "contributions.json")))
PROMPT = os.environ.get("PROMPT_NAME") or DATA["user"].lower()
W, H = 840, 880
MES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_date(s):
    if not s:
        return "—"
    d = dt.date.fromisoformat(s)
    return f"{MES[d.month - 1]} {d.day}"


def num(n):
    return f"{n:,}".replace(",", ",")


def frame(title):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
        "<style>.t{opacity:0;animation:in .45s ease-out both}"
        "@keyframes in{0%{opacity:0;transform:translateY(14px)}100%{opacity:1;transform:translateY(0)}}"
        ".b{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .6s ease-out both}"
        "@keyframes grow{to{transform:scaleY(1)}}"
        "@media (prefers-reduced-motion:reduce){.t,.b{opacity:1!important;transform:none!important;animation:none!important}}</style>",
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111722"/>'
        '<stop offset="1" stop-color="#0d1117"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="#30363d"/>',
        f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="#30363d"/>',
        '<circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/>'
        '<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
        f'<text x="{W / 2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">{title}</text>',
    ]


def card(x, y, w, h, label, value, unit, sub, delay):
    return (f'<g class="t" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#161b22" stroke="#30363d"/>'
            f'<text x="{x + 24}" y="{y + 40}" fill="#7d8590" font-size="22">$ {label}</text>'
            f'<text x="{x + 24}" y="{y + 100}" font-size="54" font-weight="700" fill="#39d353">{value}'
            f'<tspan font-size="24" fill="#7d8590"> {unit}</tspan></text>'
            f'<text x="{x + 24}" y="{y + 132}" fill="#7d8590" font-size="18">{sub}</text></g>')


def main():
    d = DATA
    out = frame(f"{PROMPT}@github: ~$ ./stats.sh")
    cs, ls, bd = d["current_streak"], d["longest_streak"], d["best_day"]
    cards = [
        ("current streak", cs["days"], "days", f"{fmt_date(cs['start'])} → {fmt_date(cs['end'])}"),
        ("longest streak", ls["days"], "days", f"{fmt_date(ls['start'])} → {fmt_date(ls['end'])}"),
        ("contributions", num(d["total"]), "", "in the last year"),
        ("active days", d["active_days"], "", f"{d['active_pct']}% of the year"),
        ("best day", bd["count"], "", fmt_date(bd["date"])),
        ("avg / active day", d["avg_active"], "", "contributions"),
    ]
    cw, ch, gx, y0 = 392, 150, 16, 54
    for i, (lab, val, unit, sub) in enumerate(cards):
        r, c = divmod(i, 2)
        out.append(card(20 + c * (cw + gx), y0 + r * (ch + 16), cw, ch, lab, val, unit, sub, 0.12 * i))

    # gráfico mensal
    cy = y0 + 3 * (ch + 16)
    chh = H - cy - 20
    out.append(f'<g class="t" style="animation-delay:.8s"><rect x="20" y="{cy}" width="{W - 40}" height="{chh}" '
               f'rx="10" fill="#161b22" stroke="#30363d"/>'
               f'<text x="44" y="{cy + 40}" fill="#7d8590" font-size="22">$ contributions / month</text></g>')
    months = d["months"][-13:]
    mx = max((m["count"] for m in months), default=1) or 1
    area_top, area_bot = cy + 80, cy + chh - 40
    n = len(months)
    slot = (W - 80) / n
    bw = slot * 0.62
    peak = max(range(n), key=lambda i: months[i]["count"]) if n else -1
    for i, m in enumerate(months):
        bh = max(2, (area_bot - area_top) * m["count"] / mx)
        x = 40 + i * slot + (slot - bw) / 2
        color = "#39d353" if i == peak else "#26a641"
        out.append(f'<rect class="b" x="{x:.1f}" y="{area_bot - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" '
                   f'fill="{color}" style="animation-delay:{1 + 0.06 * i:.2f}s"/>')
        mo = int(m["month"][5:7])
        out.append(f'<text x="{x + bw / 2:.1f}" y="{area_bot + 26}" fill="#7d8590" font-size="15" '
                   f'text-anchor="middle">{MES[mo - 1].lower()}</text>')
        if i == peak:
            out.append(f'<text class="t" x="{x + bw / 2:.1f}" y="{area_bot - bh - 10:.1f}" fill="#e6edf3" '
                       f'font-size="16" font-weight="700" text-anchor="middle" '
                       f'style="animation-delay:1.8s">{num(m["count"])}</text>')
    out.append("</svg>")
    open(os.path.join(ROOT, "stats.svg"), "w").write("\n".join(out))
    print("stats.svg ok")


if __name__ == "__main__":
    main()
