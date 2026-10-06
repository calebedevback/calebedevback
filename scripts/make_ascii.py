#!/usr/bin/env python3
"""Gera ascii.svg (840x880): retrato em ASCII a partir de uma foto, desenhado linha a linha.

Uso: python scripts/make_ascii.py foto.png     (sem foto, usa seu avatar do GitHub)
"""
import io
import os
import sys
from xml.sax.saxutils import escape

import numpy as np
import requests
from PIL import Image, ImageFilter, ImageOps

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
USER = os.environ.get("GH_USER", "")
PROMPT = os.environ.get("PROMPT_NAME") or USER.lower()
W, H, PAD, BAR = 840, 880, 20, 30
COLS, ROWS = 110, 100
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|/tjfrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


def load(path):
    if path:
        img = Image.open(path)
    else:
        r = requests.get(f"https://github.com/{USER}.png?size=460", timeout=30)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content))
    img = ImageOps.exif_transpose(img).convert("RGBA")
    bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
    return Image.alpha_composite(bg, img).convert("L")


def to_ascii(img):
    # recorte central proporcional à grade de caracteres
    cw, chh = (W - 2 * PAD) / COLS, (H - BAR - 2 * PAD) / ROWS
    target = (COLS * cw) / (ROWS * chh)
    w, h = img.size
    if w / h > target:
        nw = int(h * target); img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target); img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    img = ImageOps.autocontrast(img, cutoff=2).filter(ImageFilter.SHARPEN)
    a = np.asarray(img.resize((COLS, ROWS), Image.LANCZOS), dtype=float) / 255.0
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]).mean()
    if edge > 0.6:  # fundo claro: inverte para o fundo ficar vazio no card escuro
        a = 1.0 - a
    a = np.clip((a - 0.1) / 0.9, 0, 1) ** 0.9
    idx = (a * (len(RAMP) - 1)).round().astype(int)
    return ["".join(RAMP[i] for i in row) for row in idx], cw, chh


def main():
    lines, cw, chh = to_ascii(load(sys.argv[1] if len(sys.argv) > 1 else None))
    fs = chh * 0.86
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
           '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111722"/>'
           '<stop offset="1" stop-color="#0d1117"/></linearGradient></defs>',
           f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
           f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="#30363d"/>',
           f'<line x1="0" y1="{BAR}" x2="{W}" y2="{BAR}" stroke="#30363d"/>',
           '<circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/>'
           '<circle cx="52" cy="15" r="5" fill="#27c93f"/>',
           f'<text x="{W / 2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">{PROMPT}@github: ~$ ./portrait.sh</text>']
    tw = W - 2 * PAD
    step = 0.05
    for i, line in enumerate(lines):
        y = BAR + PAD + i * chh
        t = i * step
        out.append(f'<clipPath id="r{i}"><rect x="{PAD}" y="{y:.2f}" height="{chh + 1:.2f}" width="0">'
                   f'<animate attributeName="width" from="0" to="{tw}" begin="{t:.2f}s" dur="{step:.2f}s" fill="freeze"/>'
                   f'</rect></clipPath>')
        out.append(f'<text clip-path="url(#r{i})" xml:space="preserve" x="{PAD}" y="{y + fs:.2f}" fill="#c9d1d9" '
                   f'font-size="{fs:.2f}" textLength="{tw}" lengthAdjust="spacing">{escape(line)}</text>')
    end = len(lines) * step
    # cursor piscando no final
    out.append(f'<rect x="{PAD}" y="{H - PAD - chh:.2f}" width="{cw * 1.2:.2f}" height="{chh:.2f}" fill="#39d353" opacity="0">'
               f'<animate attributeName="opacity" values="0;1;0" dur="1s" begin="{end:.2f}s" repeatCount="indefinite"/></rect>')
    out.append("</svg>")
    open(os.path.join(ROOT, "ascii.svg"), "w").write("\n".join(out))
    print("ascii.svg ok")


if __name__ == "__main__":
    main()
