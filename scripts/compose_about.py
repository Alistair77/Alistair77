#!/usr/bin/env python3
"""
Combine the ASCII portrait (avi-ascii.svg) and the agent info card
(info-card.svg) into ONE 860px-wide panel, about.svg, so the README doesn't
need a <table> (GitHub draws borders + padding around tables, which squeezed
both images and threw the widths off).

  * the portrait is cropped to the face (PORTRAIT_CROP) and gets its own
    window frame, so it fills its half instead of floating in empty space
  * both windows are exactly the same height; the gap between them is GAP
  * both source SVGs are inlined (ids prefixed so they can't collide), so
    their animations -- typing portrait, agent trace, snake -- all still run

Run after make_ascii_svg.py / make_info_card.py:  python scripts/compose_about.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PORTRAIT = os.path.join(ROOT, "avi-ascii.svg")
CARD = os.path.join(ROOT, "info-card.svg")
OUT = os.path.join(ROOT, "about.svg")

W = 860
GAP = 12
TITLEBAR_H = 30
PORTRAIT_CROP = (136, 232, 520, 594)   # x, y, w, h inside avi-ascii.svg: the face, minus empty margins
HOST = "Alistair77"

FRAME = "#30363d"
MUTED = "#7d8590"


def inner(svg_text, prefix):
    """root <svg> attributes (w, h) + its children with every id namespaced."""
    m = re.match(r'\s*<svg\b([^>]*)>(.*)</svg>\s*$', svg_text, re.S)
    attrs, body = m.group(1), m.group(2)
    w = float(re.search(r'\bwidth="([\d.]+)"', attrs).group(1))
    h = float(re.search(r'\bheight="([\d.]+)"', attrs).group(1))
    body = re.sub(r'\bid="([^"]+)"', lambda k: f'id="{prefix}{k.group(1)}"', body)
    body = re.sub(r'url\(#([^)]+)\)', lambda k: f'url(#{prefix}{k.group(1)})', body)
    body = re.sub(r'href="#([^"]+)"', lambda k: f'href="#{prefix}{k.group(1)}"', body)
    return w, h, body


def main():
    cw, ch, card = inner(open(CARD).read(), "c_")
    _, _, portrait = inner(open(PORTRAIT).read(), "p_")

    cx, cy, cwid, chei = PORTRAIT_CROP
    # same height for both windows: portrait window = titlebar + cropped art at the card's scale
    # solve: left_w + GAP + right_w = W, where right_w = ch_scaled * cw/ch, left content aspect = crop aspect
    aspect = cwid / chei
    # the card's own title bar is TITLEBAR_H in its units; scale ours to match so the bars line up
    hh = (W - GAP) / (cw / ch + aspect * (1 - TITLEBAR_H / ch))
    s = hh / ch
    tb = TITLEBAR_H * s
    right_w = hh * cw / ch
    left_w = W - GAP - right_w

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{hh:.0f}" viewBox="0 0 {W} {hh:.1f}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        "<defs>"
        '<linearGradient id="abg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient>'
        f'<clipPath id="pwin"><rect x="0" y="0" width="{left_w:.1f}" height="{hh:.1f}" rx="12"/></clipPath>'
        "</defs>",
        # ---- left window: the portrait, cropped to the face ----
        '<g clip-path="url(#pwin)">',
        f'<rect width="{left_w:.1f}" height="{hh:.1f}" fill="url(#abg)"/>',
        f'<svg x="0" y="{tb:.1f}" width="{left_w:.1f}" height="{hh - tb:.1f}" '
        f'viewBox="{cx} {cy} {cwid} {chei}" preserveAspectRatio="xMidYMid meet">{portrait}</svg>',
        f'<rect width="{left_w:.1f}" height="{tb:.1f}" fill="#0d1117"/>',
        "</g>",
        f'<line x1="0" y1="{tb:.1f}" x2="{left_w:.1f}" y2="{tb:.1f}" stroke="{FRAME}"/>',
    ]
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{(20 + i * 16) * s:.1f}" cy="{tb / 2:.1f}" r="{5 * s:.1f}" fill="{c}"/>')
    p.append(f'<text x="{left_w / 2 + 24:.1f}" y="{tb / 2 + 4 * s:.1f}" fill="{MUTED}" font-size="{12 * s:.1f}" '
             f'text-anchor="middle">~/whoami</text>')
    p.append(f'<rect x=".5" y=".5" width="{left_w - 1:.1f}" height="{hh - 1:.1f}" rx="12" fill="none" stroke="{FRAME}"/>')
    # ---- right window: the agent card, scaled to the same height ----
    p.append(f'<svg x="{left_w + GAP:.1f}" y="0" width="{right_w:.1f}" height="{hh:.1f}" '
             f'viewBox="0 0 {cw:.0f} {ch:.0f}">{card}</svg>')
    p.append("</svg>")
    svg = "".join(p)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes): {W} x {hh:.0f}, portrait {left_w:.0f} + card {right_w:.0f}")


if __name__ == "__main__":
    main()
