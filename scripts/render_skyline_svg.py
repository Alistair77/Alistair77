#!/usr/bin/env python3
"""
Render data/contributions.json (produced by fetch_contributions.py) as an
animated CONTRIBUTION SKYLINE.

The idea:
  * every unbroken run of days with commits is one BUILDING
  * every day in that run is one FLOOR stacked on top (oldest day at street level)
  * a day with zero contributions ends the building -- the next active day
    breaks ground on a brand-new building next door
  * a floor's colour follows that day's commit count (same green ramp as GitHub),
    and its windows light up in proportion -- busy days glow brighter
  * if the streak is still alive (today or yesterday had commits) the last
    building is "under construction": it gets a crane and a blinking beacon,
    and tomorrow's run of this workflow adds the next floor

On load the city builds itself: floors drop in one at a time, building after
building in chronological order, then roofs and labels pop on. It plays once
and freezes on the finished skyline (only stars + beacon keep twinkling).

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.
Set STATIC=1 to emit the finished frame with no animation (handy for previews).
"""
import datetime
import json
import math
import os
import random

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-skyline.svg")
USER = os.environ.get("GH_PROFILE_USER", "Alistair77")

# floor colours: level 1 (quiet day) -> level 5 (busiest day). index 0 unused.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
SIDE = ["#0b0f15", "#082a19", "#04431f", "#176a29", "#238a35", "#3fa86a"]  # darker 3D faces
WIN_ON = "#fff3b0"
WIN_OFF = "#0a1410"

W = 869
PAD = 22
TITLEBAR_H = 30
SKY_H = 230          # sky + buildings area (above the street)
STREET_H = 34
STATS_H = 78
H = TITLEBAR_H + SKY_H + STREET_H + STATS_H

MAX_FLOOR_H = 24
MIN_FLOOR_H = 3
DEPTH = 5            # 3D side-face depth in px
ROOF_ROOM = 34       # headroom kept above the tallest building for roof/crane/label

BG_TOP = "#060a12"
BG_BOT = "#0d1a2b"
FRAME = "#1f6feb"
MUTED = "#7d8590"
ACCENT = "#22d3ee"
GREEN = "#39d353"
GOLD = "#f2cc60"
RED = "#ff5f56"

# animation timing (one-shot)
START = 0.35         # pause before the first floor drops
FLOOR_T = 0.08       # stagger between floors
BUILDING_GAP_T = 0.08  # extra beat between buildings
DROP_DUR = 0.45


def level_for(count, mx):
    """Colour a day relative to the account's own busiest day."""
    if count <= 0:
        return 0
    if mx <= 0:
        return 1
    return min(5, max(1, math.ceil(count / mx * 5)))


def find_buildings(days):
    """Split the day list into runs of consecutive active days."""
    buildings, cur = [], []
    for d in days:
        if d["count"] > 0:
            cur.append(d)
        elif cur:
            buildings.append(cur)
            cur = []
    if cur:
        buildings.append(cur)
    return buildings


def is_under_construction(days, buildings):
    """The last building is still going up if its streak hasn't been broken yet:
    its top floor is today, or yesterday (today isn't over)."""
    if not buildings or not days:
        return False
    last_active = buildings[-1][-1]["date"]
    tail = [d["date"] for d in days[-2:]]
    return last_active in tail


def fmt(date_s):
    return datetime.date.fromisoformat(date_s).strftime("%b %-d")


def render(data, static=False):
    days = data["days"]
    mx = max((d["count"] for d in days), default=0)
    buildings = find_buildings(days)
    building_now = is_under_construction(days, buildings)
    n = len(buildings)
    tallest = max((len(b) for b in buildings), default=0)

    ground_y = TITLEBAR_H + SKY_H
    left, right = PAD + 6, W - PAD - 6
    if building_now:
        right -= 26  # leave room for the crane beside the last building
    street_w = right - left

    # building footprint: as wide as fits, clamped so 1 or 100 buildings both look ok
    slot = street_w / max(n, 1)
    bw = max(8.0, min(34.0, slot * 0.74))
    gap = slot - bw
    # centre the row when there are only a few buildings
    row_w = n * bw + max(n - 1, 0) * gap
    x0 = left + (street_w - row_w) / 2 if n else left

    avail = SKY_H - ROOF_ROOM - 8
    floor_h = max(MIN_FLOOR_H, min(MAX_FLOOR_H, avail / max(tallest, 1)))

    rnd = random.Random(77)  # deterministic stars / windows: SVG only changes when data does

    anim = "" if static else "anim"
    css = f"""
@keyframes drop {{
  0%   {{ opacity: 0; transform: translateY(-70px); }}
  55%  {{ opacity: 1; transform: translateY(2px); }}
  75%  {{ transform: translateY(-2px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes pop {{
  0%   {{ opacity: 0; transform: translateY(6px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes dust {{
  0%   {{ opacity: .55; transform: scaleX(.4); }}
  100% {{ opacity: 0;   transform: scaleX(1.6); }}
}}
@keyframes twinkle {{ 0%,100% {{ opacity: .9; }} 50% {{ opacity: .2; }} }}
@keyframes blink   {{ 0%,49% {{ opacity: 1; }} 50%,100% {{ opacity: .15; }} }}
@keyframes swing   {{ 0%,100% {{ transform: rotate(-4deg); }} 50% {{ transform: rotate(4deg); }} }}
.anim .f   {{ opacity: 0; animation: drop {DROP_DUR}s cubic-bezier(.3,.7,.3,1) both; }}
.anim .p   {{ opacity: 0; animation: pop .4s ease-out both; }}
.anim .d   {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: dust .5s ease-out forwards; }}
.d {{ opacity: 0; }}
.s  {{ animation: twinkle 3s ease-in-out infinite; }}
.bk {{ animation: blink 1.1s steps(1) infinite; }}
.hk {{ transform-box: view-box; animation: swing 4s ease-in-out infinite; }}
""".strip()

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f"<style>{css}</style>",
        "<defs>"
        f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOT}"/></linearGradient>'
        '<radialGradient id="moon" cx=".5" cy=".5" r=".5">'
        '<stop offset="0" stop-color="#fdf6d8"/><stop offset=".7" stop-color="#f2e7b8"/>'
        '<stop offset="1" stop-color="#f2e7b8" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="glow" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{GREEN}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{GREEN}" stop-opacity=".12"/></linearGradient>'
        "</defs>",
        f'<g class="{anim}">',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#sky)"/>',
    ]

    # ---- sky: stars, moon, faint distant skyline ----
    for _ in range(46):
        sx = rnd.uniform(PAD, W - PAD)
        sy = rnd.uniform(TITLEBAR_H + 6, ground_y - 70)
        r = rnd.choice([0.6, 0.8, 1.0, 1.2])
        dl = rnd.uniform(0, 3)
        p.append(f'<circle class="s" cx="{sx:.1f}" cy="{sy:.1f}" r="{r}" fill="#cfe3ff" '
                 f'style="animation-delay:{dl:.2f}s"/>')
    mx_, my_ = PAD + 120, TITLEBAR_H + 40
    p.append(f'<circle cx="{mx_}" cy="{my_}" r="26" fill="url(#moon)" opacity=".35"/>')
    p.append(f'<circle cx="{mx_}" cy="{my_}" r="13" fill="#f6edc6"/>')

    # distant silhouette so empty stretches still feel like a city
    sil = [f"M{PAD},{ground_y}"]
    x = PAD
    while x < W - PAD:
        w = rnd.uniform(14, 34)
        h = rnd.uniform(12, 46)
        sil.append(f"L{x:.1f},{ground_y - h:.1f} L{min(x + w, W - PAD):.1f},{ground_y - h:.1f}")
        x += w
    sil.append(f"L{W - PAD},{ground_y} Z")
    p.append(f'<path d="{" ".join(sil)}" fill="#13233a" opacity=".55"/>')
    p.append(f'<rect x="0" y="{ground_y - 60}" width="{W}" height="60" fill="url(#glow)"/>')

    # ---- title bar ----
    p.append(f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity=".35"/>')
    p.append(f'<rect x="0" y="0" width="{W}" height="{TITLEBAR_H}" rx="12" fill="#0b111b" opacity=".9"/>')
    p.append(f'<rect x="0" y="{TITLEBAR_H - 12}" width="{W}" height="12" fill="#0b111b" opacity=".9"/>')
    for i, c in enumerate([RED, "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{c}"/>')
    p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
             f'{USER}@github: ~/contributions --skyline</text>')

    # ---- buildings ----
    t = START
    longest_idx = max(range(n), key=lambda i: (len(buildings[i]), i)) if n else -1
    month_marks = []
    for bi, b in enumerate(buildings):
        bx = x0 + bi * (bw + gap)
        floors = len(b)
        total = sum(d["count"] for d in b)
        under = building_now and bi == n - 1
        top_y = ground_y - floors * floor_h
        p.append(f'<g><title>{fmt(b[0]["date"])} &#8594; {fmt(b[-1]["date"])}: '
                 f'{floors}-day streak, {total} contributions</title>')

        # dust puff as the foundation lands
        p.append(f'<ellipse class="d" cx="{bx + bw / 2:.1f}" cy="{ground_y}" rx="{bw * 0.8:.1f}" ry="3" '
                 f'fill="#9fb3c8" style="animation-delay:{t + DROP_DUR * 0.5:.2f}s"/>')

        for fi, d in enumerate(b):
            lvl = level_for(d["count"], mx)
            fy = ground_y - (fi + 1) * floor_h
            fh = floor_h - (0.8 if floor_h > 6 else 0.3)
            g = [f'<g class="f" style="animation-delay:{t:.2f}s">']
            # 3D side face + top lip
            g.append(f'<path d="M{bx + bw:.1f},{fy:.1f} l{DEPTH},-{DEPTH * 0.6:.1f} v{fh:.1f} '
                     f'l-{DEPTH},{DEPTH * 0.6:.1f} Z" fill="{SIDE[lvl]}"/>')
            if fi == floors - 1:
                g.append(f'<path d="M{bx:.1f},{fy:.1f} l{DEPTH},-{DEPTH * 0.6:.1f} h{bw:.1f} '
                         f'l-{DEPTH},{DEPTH * 0.6:.1f} Z" fill="{SIDE[lvl]}" opacity=".85"/>')
            g.append(f'<rect x="{bx:.1f}" y="{fy:.1f}" width="{bw:.1f}" height="{fh:.1f}" '
                     f'fill="{PALETTE[lvl]}"/>')
            # windows: lit share grows with the day's intensity
            if floor_h >= 7 and bw >= 12:
                cols = max(1, int((bw - 4) // 7))
                ww, wh = 3.6, min(5.0, fh - 4)
                step = (bw - 4 - ww) / max(cols - 1, 1) if cols > 1 else 0
                for wi in range(cols):
                    wx = bx + 2 + wi * step + (0 if cols > 1 else (bw - 4 - ww) / 2)
                    wy = fy + (fh - wh) / 2
                    lit = rnd.random() < 0.25 + lvl * 0.15
                    g.append(f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww}" height="{wh:.1f}" rx=".6" '
                             f'fill="{WIN_ON if lit else WIN_OFF}" opacity="{0.95 if lit else 0.7}"/>')
            g.append(f"<title>{d['date']}: {d['count']} contribution{'s' if d['count'] != 1 else ''}</title>")
            g.append("</g>")
            p.append("".join(g))
            t += FLOOR_T

        done = t + DROP_DUR * 0.6
        cx = bx + bw / 2 + DEPTH / 2
        roof_y = top_y - DEPTH * 0.6
        if under:
            # crane: mast beside the building, jib over the top, swinging hook + beacon
            mast_x = bx + bw + DEPTH + 6
            mast_top = roof_y - 26
            p.append(f'<g class="p" style="animation-delay:{done:.2f}s">')
            p.append(f'<rect x="{mast_x:.1f}" y="{mast_top:.1f}" width="3" height="{ground_y - mast_top:.1f}" fill="{GOLD}"/>')
            for ly in range(int(mast_top) + 6, int(ground_y), 8):
                p.append(f'<line x1="{mast_x:.1f}" y1="{ly}" x2="{mast_x + 3:.1f}" y2="{ly + 6}" stroke="#7a5d10" stroke-width=".8"/>')
            jib_l = bx - 6
            p.append(f'<rect x="{jib_l:.1f}" y="{mast_top:.1f}" width="{mast_x + 14 - jib_l:.1f}" height="2.5" fill="{GOLD}"/>')
            p.append(f'<rect x="{mast_x + 6:.1f}" y="{mast_top + 2.5:.1f}" width="8" height="5" fill="#6e7681"/>')
            hook_x = bx + bw / 2
            p.append(f'<g class="hk" style="transform-origin:{hook_x:.1f}px {mast_top + 2:.1f}px">'
                     f'<line x1="{hook_x:.1f}" y1="{mast_top + 2:.1f}" x2="{hook_x:.1f}" y2="{roof_y - 10:.1f}" '
                     f'stroke="#c9d1d9" stroke-width=".8"/>'
                     f'<rect x="{hook_x - 5:.1f}" y="{roof_y - 10:.1f}" width="10" height="5" rx="1" '
                     f'fill="{PALETTE[2]}" stroke="{GREEN}" stroke-width=".6" stroke-dasharray="2 1.5"/></g>')
            p.append(f'<circle class="bk" cx="{mast_x + 1.5:.1f}" cy="{mast_top - 3:.1f}" r="2.4" fill="{RED}"/>')
            p.append(f'<text x="{cx:.1f}" y="{mast_top - 10:.1f}" fill="{GOLD}" font-size="9" '
                     f'text-anchor="middle" font-weight="700">BUILDING&#8230;</text>')
            p.append("</g>")
            label_y = roof_y - 4
        else:
            # finished: roof cap + antenna (gold spire on the tallest)
            spire = bi == longest_idx
            ant_h = 14 if spire else (6 if floors >= 3 else 0)
            p.append(f'<g class="p" style="animation-delay:{done:.2f}s">')
            if ant_h:
                p.append(f'<line x1="{cx:.1f}" y1="{roof_y:.1f}" x2="{cx:.1f}" y2="{roof_y - ant_h:.1f}" '
                         f'stroke="{GOLD if spire else "#6e7681"}" stroke-width="{1.4 if spire else 1}"/>')
                bk = 'class="bk" ' if spire else ""
                p.append(f'<circle {bk}cx="{cx:.1f}" cy="{roof_y - ant_h:.1f}" '
                         f'r="{2 if spire else 1.3}" fill="{GOLD if spire else RED}"/>')
            p.append("</g>")
            label_y = roof_y - ant_h - 6
        # floor-count label above the roof
        if bw >= 14:
            colour = GOLD if bi == longest_idx else (ACCENT if under else MUTED)
            if not under:
                p.append(f'<text class="p" x="{cx:.1f}" y="{label_y:.1f}" fill="{colour}" font-size="9.5" '
                         f'text-anchor="middle" font-weight="700" style="animation-delay:{done + 0.1:.2f}s">'
                         f'{floors}</text>')
        p.append("</g>")

        month = b[0]["date"][:7]
        if not month_marks or month_marks[-1][1] != month:
            month_marks.append((bx + bw / 2, month))
        t += BUILDING_GAP_T

    if not n:
        p.append(f'<text x="{W / 2}" y="{ground_y - 60}" fill="{MUTED}" font-size="13" text-anchor="middle">'
                 f'empty lot &#183; first commit breaks ground</text>')

    # ---- street ----
    p.append(f'<rect x="0" y="{ground_y}" width="{W}" height="{STREET_H}" fill="#0b1018"/>')
    p.append(f'<line x1="{PAD}" y1="{ground_y + 0.5}" x2="{W - PAD}" y2="{ground_y + 0.5}" stroke="#30363d" stroke-width="1.5"/>')
    p.append(f'<line x1="{PAD}" y1="{ground_y + 22}" x2="{W - PAD}" y2="{ground_y + 22}" stroke="#30363d" '
             f'stroke-width="1.2" stroke-dasharray="10 8"/>')
    last_x = -99
    for mx_x, month in month_marks:
        if mx_x - last_x < 30:
            continue
        last_x = mx_x
        label = datetime.date.fromisoformat(month + "-01").strftime("%b")
        p.append(f'<text x="{mx_x:.1f}" y="{ground_y + 14}" fill="{MUTED}" font-size="9.5" text-anchor="middle">{label}</text>')

    # ---- stats footer ----
    sep_y = ground_y + STREET_H
    p.append(f'<rect x="0" y="{sep_y}" width="{W}" height="{STATS_H}" fill="#0a0e14"/>')
    p.append(f'<rect x="0" y="{H - 14}" width="{W}" height="14" rx="12" fill="#0a0e14"/>')
    p.append(f'<line x1="0" y1="{sep_y}" x2="{W}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity=".25"/>')

    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    total = data["total_contributions"]
    best = data["best_day"]
    rng = data["range"]
    floors_total = sum(len(b) for b in buildings)

    ly = sep_y + 26
    p.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{GREEN}"><tspan font-weight="700">{total:,}</tspan>'
             f'<tspan fill="{MUTED}"> contributions  &#183;  </tspan>'
             f'<tspan font-weight="700">{n}</tspan><tspan fill="{MUTED}"> buildings  &#183;  </tspan>'
             f'<tspan font-weight="700">{floors_total}</tspan><tspan fill="{MUTED}"> floors</tspan></text>')
    p.append(f'<text x="{W - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
             f'{rng["start"]} &#8594; {rng["end"]}</text>')
    ly += 24
    status = (f'<tspan fill="{GOLD}" font-weight="700">{cs} floors &amp; rising</tspan>' if cs
              else f'<tspan fill="{MUTED}">idle &#8212; next commit breaks ground</tspan>')
    p.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}">current build {status}'
             f'<tspan fill="{MUTED}">   &#183;   tallest </tspan>'
             f'<tspan fill="{GOLD}" font-weight="700">{ls} floors</tspan></text>')

    # legend: floor colours
    lx = W - PAD - 6 * 11 - 34
    p.append(f'<text x="{lx - 6}" y="{ly}" fill="{MUTED}" font-size="10" text-anchor="end">'
             f'best day <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan>   less</text>')
    for i, c in enumerate(PALETTE[1:]):
        p.append(f'<rect x="{lx + i * 11}" y="{ly - 9}" width="10" height="10" rx="1.5" fill="{c}"/>')
    p.append(f'<text x="{lx + 5 * 11 + 4}" y="{ly}" fill="{MUTED}" font-size="10">more</text>')

    p.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" '
             f'stroke="{FRAME}" stroke-opacity=".55"/>')
    p.append("</g></svg>")
    return "".join(p)


def _selfcheck():
    days = [{"date": f"2026-01-{i:02d}", "count": c} for i, c in
            enumerate([0, 2, 3, 0, 0, 1, 0, 5, 5, 5], start=1)]
    b = find_buildings(days)
    assert [len(x) for x in b] == [2, 1, 3], b          # zero day = new building
    assert is_under_construction(days, b)               # ends today -> crane up
    days2 = days + [{"date": "2026-01-11", "count": 0}]
    assert is_under_construction(days2, b)              # today empty, yesterday active -> still alive
    days3 = days2 + [{"date": "2026-01-12", "count": 0}]
    assert not is_under_construction(days3, b)          # two empty days -> finished
    assert level_for(0, 13) == 0 and level_for(13, 13) == 5 and level_for(1, 13) == 1
    render({"days": days, "current_streak": {"length": 3}, "longest_streak": {"length": 3},
            "total_contributions": 21, "best_day": {"date": "2026-01-08", "count": 5},
            "range": {"start": "2026-01-01", "end": "2026-01-10"}})
    render({"days": [{"date": "2026-01-01", "count": 0}], "current_streak": {"length": 0},
            "longest_streak": {"length": 0}, "total_contributions": 0,
            "best_day": {"date": "2026-01-01", "count": 0},
            "range": {"start": "2026-01-01", "end": "2026-01-01"}})
    print("selfcheck ok")


if __name__ == "__main__":
    if os.environ.get("SELFCHECK"):
        _selfcheck()
        raise SystemExit
    data = json.load(open(IN_PATH))
    svg = render(data, static=bool(os.environ.get("STATIC")))
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
