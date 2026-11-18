#!/usr/bin/env python3
"""
The "shirt-rip reveal": two hands grab a buttoned dress shirt and pull it open,
the buttons pop off, a comic RIIIP! bursts out, and a glowing personal crest
(an original shield with a circuit-style "A") lights up on the suit underneath,
while the hero card -- name, title, powers -- slams in beside it. It holds,
then the shirt buttons itself back up and the whole thing loops.

Static artwork, so it is NOT re-rendered by the daily workflow; run it by hand
after editing the EDIT THIS block. Pure SMIL so it animates inside <img> on
GitHub. STATIC=1 emits the open (revealed) frame for previews.
"""
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "reveal.svg")
STATIC = bool(os.environ.get("STATIC"))

# ===========================================================================
#  EDIT THIS
# ===========================================================================
HOST = "Alistair77"
HERO_NAME = "ALISTAIR"
HERO_TITLE = "AI ENGINEER"
HERO_SUB = "Builder · Lifelong Learner"
POWERS = ["LLMs", "RAG", "Agents", "Full-Stack"]
CREST_LETTER_PATH = "M-21,30 L0,-28 L21,30 M-12,9 L12,9"   # the "A" on the crest
# ===========================================================================

W, H = 860, 340
TITLEBAR_H = 30
CX = 300                 # torso centre line
D = 9.0                  # loop length, seconds

BG, BG2 = "#0a0e14", "#0d1420"
FRAME = "#1f6feb"
MUTED = "#7d8590"
INK = "#e6edf3"
NEON = "#39d353"
CYAN = "#22d3ee"
GOLD = "#f2cc60"
SKIN, SKIN_DK = "#c98e64", "#a8714c"
SHIRT, SHIRT_DK, SHIRT_EDGE = "#eef2f6", "#c3ccd6", "#8b96a3"
SUIT, SUIT2 = "#0f2a4a", "#091a30"

# timeline (seconds) -> keyTimes are these / D
T_TUG, T_TUG_PEAK, T_TUG_BACK = 0.9, 1.15, 1.4
T_RIP, T_OPEN = 1.75, 2.25
T_HOLD_END, T_CLOSED = 7.9, 8.6


def kt(*secs):
    return ";".join(f"{s / D:.4f}" for s in secs)


def anim(attr, values, times, extra=""):
    if STATIC:
        return ""
    return (f'<animate attributeName="{attr}" values="{values}" keyTimes="{times}" '
            f'dur="{D}s" repeatCount="indefinite" {extra}/>')


def anim_t(kind, values, times, extra=""):
    if STATIC:
        return ""
    return (f'<animateTransform attributeName="transform" type="{kind}" values="{values}" '
            f'keyTimes="{times}" dur="{D}s" repeatCount="indefinite" {extra}/>')


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ---- shirt geometry (left half; right half is the mirror around CX) -------
SHOULDER_A = (158, 340)
SHOULDER_B = (163, 118)
SHOULDER_Q = (168, 76)
SHOULDER_T = (214, 66)
COLLAR = (268, 50)
CLOSED = {"D": (300, 92), "E": (303, 200), "F": (306, 340)}
OPEN = {"D": (256, 82), "E": (222, 200), "F": (236, 340)}
TUG = {k: lerp(CLOSED[k], OPEN[k], 0.09) for k in CLOSED}


def mirror(pt):
    return (2 * CX - pt[0], pt[1])


def half_path(st, right=False):
    f = mirror if right else (lambda p: p)
    A, B, Q, T, C = (f(p) for p in (SHOULDER_A, SHOULDER_B, SHOULDER_Q, SHOULDER_T, COLLAR))
    Dp, E, F = f(st["D"]), f(st["E"]), f(st["F"])
    # open edge bows outward around the hands, so use a curve through E
    c1 = lerp(Dp, E, 0.5)
    c2 = lerp(E, F, 0.5)
    pts = lambda p: f"{p[0]:.1f},{p[1]:.1f}"
    return (f"M{pts(A)} L{pts(B)} Q{pts(Q)} {pts(T)} L{pts(C)} L{pts(Dp)} "
            f"Q{pts(c1)} {pts(E)} Q{pts(c2)} {pts(F)} Z")


def collar_path(st, right=False):
    f = mirror if right else (lambda p: p)
    C, Dp = COLLAR, st["D"]
    pts = [C, Dp, (Dp[0] - 18, Dp[1] + 6), (C[0] - 20, C[1] + 16)]
    return "M" + " L".join(f"{f(p)[0]:.1f},{f(p)[1]:.1f}" for p in pts) + " Z"


def morph(fn, right=False):
    """d-values across the timeline: closed, tug, closed, (rip) open, hold, close."""
    seq = [CLOSED, CLOSED, TUG, CLOSED, CLOSED, OPEN, OPEN, CLOSED, CLOSED]
    times = kt(0, T_TUG, T_TUG_PEAK, T_TUG_BACK, T_RIP, T_OPEN, T_HOLD_END, T_CLOSED, D)
    vals = ";".join(fn(s, right) for s in seq)
    return vals, times


def hand(right=False):
    """a fist gripping the shirt edge, fingers curled toward the centre line, arm in a cuffed sleeve."""
    s = -1 if right else 1
    g = [f'<g transform="scale({s},1)">']
    # forearm in a white sleeve, coming up from below-outside
    g.append(f'<path d="M-30,10 L-78,120 L-44,132 L-6,22 Z" fill="{SHIRT}" stroke="{SHIRT_EDGE}" stroke-width="1"/>')
    g.append(f'<path d="M-36,4 L-6,16 L-10,30 L-40,18 Z" fill="{SHIRT_DK}" stroke="{SHIRT_EDGE}" stroke-width="1"/>')  # cuff
    # back of the hand
    g.append(f'<rect x="-34" y="-20" width="34" height="38" rx="11" fill="{SKIN}" stroke="{SKIN_DK}" stroke-width="1.2"/>')
    # curled fingers over the fabric edge
    for i, fy in enumerate((-19, -9.5, 0, 9.5)):
        g.append(f'<rect x="-8" y="{fy}" width="15" height="9.5" rx="4.7" fill="{SKIN}" '
                 f'stroke="{SKIN_DK}" stroke-width="1.1"/>')
    # thumb across the top
    g.append(f'<path d="M-30,-18 Q-22,-30 -6,-24 Q-2,-21 -6,-17 Q-18,-17 -26,-12 Z" fill="{SKIN}" '
             f'stroke="{SKIN_DK}" stroke-width="1.1"/>')
    g.append(f'<path d="M-26,-4 Q-18,-6 -12,-2" stroke="{SKIN_DK}" stroke-width="1" fill="none"/>')
    g.append("</g>")
    return "".join(g)


def crest():
    """original personal crest: a shield with a circuit-trace 'A'."""
    shield = "M0,-52 L46,-30 L46,10 Q46,40 0,60 Q-46,40 -46,10 L-46,-30 Z"
    inner = "M0,-43 L38,-25 L38,9 Q38,33 0,50 Q-38,33 -38,9 L-38,-25 Z"
    out = [
        f'<path d="{shield}" fill="#07131f" stroke="url(#crestEdge)" stroke-width="4" stroke-linejoin="round"/>',
        f'<path d="{inner}" fill="url(#crestFill)" stroke="{NEON}" stroke-opacity=".35" stroke-width="1"/>',
        # circuit traces behind the letter
        f'<g stroke="{CYAN}" stroke-opacity=".35" stroke-width="1.2" fill="none">'
        '<path d="M-30,-6 h10 l6,6 h8"/><path d="M30,-6 h-10 l-6,6 h-8"/>'
        '<path d="M-26,24 h12 l5,-5"/><path d="M26,24 h-12 l-5,-5"/></g>'
        f'<g fill="{CYAN}" fill-opacity=".7"><circle cx="-30" cy="-6" r="1.8"/><circle cx="30" cy="-6" r="1.8"/>'
        '<circle cx="-26" cy="24" r="1.8"/><circle cx="26" cy="24" r="1.8"/></g>',
        f'<path d="{CREST_LETTER_PATH}" stroke="url(#crestA)" stroke-width="8.5" stroke-linecap="round" '
        f'stroke-linejoin="round" fill="none"/>',
        f'<circle cx="0" cy="-28" r="3.2" fill="#eafff0"/>',
    ]
    return "".join(out)


def build():
    rnd = random.Random(7)
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        "<defs>"
        f'<linearGradient id="rbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
        f'<stop offset="1" stop-color="{BG}"/></linearGradient>'
        f'<pattern id="dots" width="9" height="9" patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1.1" fill="{FRAME}" fill-opacity=".14"/></pattern>'
        f'<radialGradient id="burst" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{NEON}" stop-opacity=".55"/>'
        f'<stop offset=".5" stop-color="{CYAN}" stop-opacity=".18"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="suit" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{SUIT}"/>'
        f'<stop offset="1" stop-color="{SUIT2}"/></linearGradient>'
        f'<linearGradient id="crestEdge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{NEON}"/>'
        f'<stop offset="1" stop-color="{CYAN}"/></linearGradient>'
        f'<linearGradient id="crestFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d2b1c"/>'
        f'<stop offset="1" stop-color="#06131c"/></linearGradient>'
        f'<linearGradient id="crestA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b8ffcf"/>'
        f'<stop offset=".55" stop-color="{NEON}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>'
        f'<linearGradient id="shirtL" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{SHIRT_DK}"/>'
        f'<stop offset=".35" stop-color="{SHIRT}"/><stop offset="1" stop-color="{SHIRT}"/></linearGradient>'
        f'<linearGradient id="shirtR" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="{SHIRT_DK}"/>'
        f'<stop offset=".35" stop-color="{SHIRT}"/><stop offset="1" stop-color="{SHIRT}"/></linearGradient>'
        f'<clipPath id="scene"><rect x="1" y="{TITLEBAR_H}" width="{W - 2}" height="{H - TITLEBAR_H - 1}" rx="0"/></clipPath>'
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#rbg)"/>',
        f'<rect x="0" y="{TITLEBAR_H}" width="{W}" height="{H - TITLEBAR_H - 12}" fill="url(#dots)"/>',
        '<g clip-path="url(#scene)">',
    ]

    open_on = kt(0, T_RIP, T_OPEN, T_HOLD_END, T_CLOSED, D)
    # ---- light rays behind the torso, spinning, only while open ----
    rays = []
    for i in range(18):
        a = i * 20
        rays.append(f'<path d="M0,0 L{math.cos(math.radians(a - 3.5)) * 520:.0f},{math.sin(math.radians(a - 3.5)) * 520:.0f} '
                    f'L{math.cos(math.radians(a + 3.5)) * 520:.0f},{math.sin(math.radians(a + 3.5)) * 520:.0f} Z"/>')
    spin = "" if STATIC else (f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" '
                              f'dur="40s" repeatCount="indefinite" additive="sum"/>')
    p.append(f'<g opacity="{1 if STATIC else 0}">'
             + anim("opacity", "0;0;1;1;0;0", open_on)
             + f'<g transform="translate({CX},185)"><g fill="{NEON}" fill-opacity=".07">{"".join(rays)}{spin}</g>'
             f'<circle r="190" fill="url(#burst)"/></g></g>')

    # ---- neck + torso (suit underneath) ----
    p.append(f'<path d="M272,{TITLEBAR_H} L272,62 Q300,74 328,62 L328,{TITLEBAR_H} Z" fill="{SKIN}"/>')
    p.append(f'<path d="M272,52 Q300,66 328,52 L328,62 Q300,74 272,62 Z" fill="{SKIN_DK}" opacity=".6"/>')
    torso = (f"M158,340 L163,118 Q168,76 214,66 L268,50 Q300,64 332,50 L386,66 Q432,76 437,118 L442,340 Z")
    p.append(f'<path d="{torso}" fill="url(#suit)"/>')
    # faint circuit lines on the suit
    p.append(f'<g stroke="{CYAN}" stroke-opacity=".12" stroke-width="1.2" fill="none">'
             f'<path d="M190,300 v-40 l20,-20 h24"/><path d="M410,300 v-40 l-20,-20 h-24"/>'
             f'<path d="M230,330 v-30 h20"/><path d="M370,330 v-30 h-20"/>'
             f'<path d="M300,250 v80"/><path d="M200,140 h30 l12,12"/><path d="M400,140 h-30 l-12,12"/></g>')

    # ---- crest + its pulsing glow ----
    glow_pulse = "" if STATIC else (
        '<animate attributeName="r" values="70;84;70" dur="1.6s" repeatCount="indefinite"/>')
    p.append(f'<g opacity="{1 if STATIC else 0}">' + anim("opacity", "0;0;1;1;0;0", open_on)
             + f'<circle cx="{CX}" cy="185" r="70" fill="url(#burst)">{glow_pulse}</circle></g>')
    pop = anim_t("scale", "1;1;1.12;1;1;1", kt(0, T_RIP, T_OPEN, T_OPEN + 0.25, T_HOLD_END, D), 'additive="sum"')
    p.append(f'<g transform="translate({CX},185)"><g>{crest()}{pop}</g></g>')

    # ---- the shirt halves + collars, morphing open/closed ----
    for right in (False, True):
        grad = "shirtR" if right else "shirtL"
        if STATIC:
            p.append(f'<path d="{half_path(OPEN, right)}" fill="url(#{grad})" stroke="{SHIRT_EDGE}" stroke-width="1.2"/>')
            p.append(f'<path d="{collar_path(OPEN, right)}" fill="{SHIRT}" stroke="{SHIRT_EDGE}" stroke-width="1.2"/>')
            continue
        vals, times = morph(half_path, right)
        p.append(f'<path d="{half_path(CLOSED, right)}" fill="url(#{grad})" stroke="{SHIRT_EDGE}" stroke-width="1.2">'
                 f'<animate attributeName="d" values="{vals}" keyTimes="{times}" dur="{D}s" repeatCount="indefinite"/></path>')
        vals, times = morph(collar_path, right)
        p.append(f'<path d="{collar_path(CLOSED, right)}" fill="{SHIRT}" stroke="{SHIRT_EDGE}" stroke-width="1.2">'
                 f'<animate attributeName="d" values="{vals}" keyTimes="{times}" dur="{D}s" repeatCount="indefinite"/></path>')
    # placket line + pocket on the closed shirt (fades as it opens)
    p.append(f'<g opacity="{0 if STATIC else 1}">' + anim("opacity", "1;1;0;0;1;1", open_on)
             + f'<line x1="{CX + 3}" y1="96" x2="{CX + 6}" y2="340" stroke="{SHIRT_EDGE}" stroke-width="1"/>'
             f'<path d="M345,128 h34 v34 q-17,6 -34,0 Z" fill="none" stroke="{SHIRT_EDGE}" stroke-width="1"/></g>')

    # ---- buttons: sit on the placket, pop off on the rip, come back when it closes ----
    for i, by in enumerate((112, 152, 192, 232, 272, 312)):
        bx = CX + 3 + (by - 96) / 244 * 3
        dx = rnd.choice([-1, 1]) * rnd.uniform(60, 170)
        dy = -rnd.uniform(40, 120)
        spin = rnd.choice([-1, 1]) * rnd.uniform(200, 540)
        if STATIC:
            continue
        p.append(f'<g transform="translate({bx:.1f},{by})"><g>'
                 f'<circle r="4.2" fill="#f7f9fb" stroke="{SHIRT_EDGE}" stroke-width="1"/>'
                 f'<circle cx="-1.3" cy="-1.3" r=".7" fill="{SHIRT_EDGE}"/><circle cx="1.3" cy="1.3" r=".7" fill="{SHIRT_EDGE}"/>'
                 + anim_t("translate", f"0 0;0 0;{dx:.0f} {dy:.0f};{dx * 1.3:.0f} {dy + 160:.0f};0 0;0 0",
                          kt(0, T_RIP, T_RIP + 0.35, T_RIP + 1.1, T_RIP + 1.11, D), 'additive="sum"')
                 + anim_t("rotate", f"0;0;{spin:.0f};{spin:.0f};0;0",
                          kt(0, T_RIP, T_RIP + 0.6, T_RIP + 1.1, T_RIP + 1.11, D), 'additive="sum"')
                 + anim("opacity", "1;1;1;0;0;1;1",
                        kt(0, T_RIP, T_RIP + 0.7, T_RIP + 1.1, T_CLOSED - 0.05, T_CLOSED, D), 'calcMode="discrete"')
                 + "</g></g>")

    # ---- hands, riding the shirt edge at chest height ----
    for right in (False, True):
        pts = [CLOSED["E"], CLOSED["E"], TUG["E"], CLOSED["E"], CLOSED["E"], OPEN["E"], OPEN["E"],
               CLOSED["E"], CLOSED["E"]]
        if right:
            pts = [mirror(q) for q in pts]
        # hands sit just outside the fabric edge
        off = 12 if right else -12
        vals = ";".join(f"{x + off:.1f} {y:.1f}" for x, y in pts)
        times = kt(0, T_TUG, T_TUG_PEAK, T_TUG_BACK, T_RIP, T_OPEN, T_HOLD_END, T_CLOSED, D)
        e = mirror(OPEN["E"]) if right else OPEN["E"]
        start = e if STATIC else (mirror(CLOSED["E"]) if right else CLOSED["E"])
        p.append(f'<g transform="translate({start[0] + off:.1f},{start[1]})">{hand(right)}'
                 + anim_t("translate", vals, times) + "</g>")

    # ---- comic RIIIP! burst at the moment of the rip ----
    star = []
    for i in range(24):
        r = 46 if i % 2 == 0 else 30
        a = math.radians(i * 15)
        star.append(f"{math.cos(a) * r * 1.25:.1f},{math.sin(a) * r:.1f}")
    burst_t = kt(0, T_RIP - 0.05, T_RIP + 0.1, T_RIP + 0.8, T_RIP + 1.1, D)
    p.append(f'<g transform="translate(478,92) rotate(-10)">'
             f'<g opacity="{0}">'
             + anim("opacity", "0;0;1;1;0;0", burst_t)
             + anim_t("scale", "0.2;0.2;1.15;1;0.9;0.2", burst_t)
             + f'<polygon points="{" ".join(star)}" fill="{GOLD}" stroke="#0b111b" stroke-width="2.5"/>'
             f'<text x="0" y="7" text-anchor="middle" font-family="Impact, \'Arial Black\', sans-serif" '
             f'font-size="22" font-weight="900" fill="#da3633" stroke="#0b111b" stroke-width="1" '
             f'letter-spacing="1">RIIIP!</text></g></g>')

    # ---- hero card, slams in on the right once the shirt is open ----
    tx = 520
    lines = [
        (f'<text x="{tx}" y="138" fill="{INK}" font-family="Impact, \'Arial Black\', sans-serif" '
         f'font-size="50" letter-spacing="3">{HERO_NAME}</text>', 0.0),
        (f'<rect x="{tx}" y="150" width="292" height="3" fill="url(#crestEdge)"/>', 0.15),
        (f'<text x="{tx}" y="182" fill="{NEON}" font-size="20" font-weight="700" letter-spacing="4">{HERO_TITLE}</text>', 0.25),
        (f'<text x="{tx}" y="206" fill="{MUTED}" font-size="13">{HERO_SUB}</text>', 0.35),
    ]
    px = tx
    chips = []
    for pw in POWERS:
        wdt = len(pw) * 8 + 18
        chips.append(f'<rect x="{px}" y="234" width="{wdt}" height="22" rx="11" fill="#0d2b1c" stroke="{NEON}" stroke-opacity=".6"/>'
                     f'<text x="{px + wdt / 2}" y="249" fill="#b8ffcf" font-size="12" text-anchor="middle">{pw}</text>')
        px += wdt + 8
    lines.append((f'<text x="{tx}" y="228" fill="{GOLD}" font-size="10.5" letter-spacing="2">POWERS</text>'
                  + "".join(chips), 0.5))
    for inner, d in lines:
        a = T_OPEN + d
        if STATIC:
            p.append(inner)
            continue
        p.append(f'<g opacity="0">{inner}'
                 + anim("opacity", "0;0;1;1;0;0", kt(0, a, a + 0.3, T_HOLD_END - 0.2, T_HOLD_END + 0.2, D))
                 + anim_t("translate", "40 0;40 0;0 0;0 0;0 0", kt(0, a, a + 0.3, T_HOLD_END, D))
                 + "</g>")
    # idle tagline while the shirt is still buttoned
    if not STATIC:
        p.append(f'<g opacity="1"><text x="{tx}" y="182" fill="{MUTED}" font-size="14">just a regular dev&#8230;</text>'
                 f'<text x="{tx}" y="206" fill="{MUTED}" font-size="12" opacity=".7">( plot twist incoming )</text>'
                 + anim("opacity", "1;1;0;0;1;1", kt(0, T_TUG, T_TUG + 0.3, T_CLOSED + 0.1, T_CLOSED + 0.4, D))
                 + "</g>")

    p.append("</g>")
    # ---- title bar + frame ----
    p.append(f'<rect x="0" y="0" width="{W}" height="{TITLEBAR_H}" rx="12" fill="#0b111b"/>'
             f'<rect x="0" y="{TITLEBAR_H - 12}" width="{W}" height="12" fill="#0b111b"/>'
             f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity=".35"/>')
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{22 + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{c}"/>')
    p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
             f'{HOST}@github: ~$ ./reveal --true-identity</text>')
    p.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}" stroke-opacity=".55"/>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    svg = build()
    with open(OUT, "w") as f:
        f.write(svg)
    print("wrote", OUT, len(svg), "bytes")
