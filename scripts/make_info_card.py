"""
Build a neofetch-style info card SVG (Andrew6rant style) to sit to the RIGHT of
the ASCII portrait: colored key/value rows for work experience, tech stack, and
highlights -- NOT GitHub stats (the contribution graph covers those).

Static content, hand-authored below. Lines fade/slide in on a short stagger so
it feels like the panel is printing alongside the portrait. STATIC=1 emits the
frozen state for Quick Look previews.
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

W, H = 480, 376
PAD = 20
TITLEBAR_H = 30
KEY_X = PAD
VAL_X = PAD + 92
LINE_H = 20.5

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
KEY = "#ffa657"      # orange keys (matches Andrew)
SECTION = "#58a6ff"  # blue section headers
GREEN = "#3fb950"
ACCENT = "#22d3ee"

# ===========================================================================
#  EDIT THIS  -- your info panel. It re-lays-out automatically; if it gets too
#  tall for the card, bump H above (and the width= in your profile README).
#  The username in the header is HOST below.
#
#  row types:
#    ("host",)              -> "you@github" header + rule
#    ("kv", key, value)     -> orange key + light value
#    ("sec", title)         -> blue "— title —" section rule
#    ("bul", text)          -> green dot + light bullet
#    ("gap",)               -> a little vertical space
# ===========================================================================
HOST = "Alistair77"   # shown as  Alistair77@github  in the header

ROWS = [
    ("host",),
    ("kv", "Now", "AI Engineer @ Personal Projects"),
    ("kv", "Focus", "LLMs, RAG, Agents"),
    ("kv", "Also", "Full-Stack Developer"),
    ("gap",),
    ("sec", "Stack"),
    ("kv", "AI / ML", "LangChain, LoRA, RAG"),
    ("kv", "Backend", "Python, FastAPI, Postgres"),
    ("kv", "Frontend", "React, Next.js, TypeScript"),
    ("kv", "Cloud", "Docker, AWS, Vercel"),
    ("gap",),
    ("sec", "Highlights"),
    ("bul", "AI engineer exploring LLMs & agent systems"),
    ("bul", "Building end-to-end intelligent applications"),
]


def esc(s):
    return html.escape(s)


def rise(inner, i):
    """fade + slight upward slide, staggered by row index; freezes visible."""
    if STATIC:
        return f"<g>{inner}</g>"
    delay = 0.15 + i * 0.06
    return (f'<g opacity="0" transform="translate(0,5)">{inner}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.4s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" '
            f'begin="{delay:.2f}s" dur="0.4s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/></g>')


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<defs>'
    f'<linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#ibg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">{esc(HOST)}@github: ~$ neofetch</text>')

y = TITLEBAR_H + 30
for i, row in enumerate(ROWS):
    kind = row[0]
    if kind == "gap":
        y += LINE_H * 0.5
        continue
    if kind == "host":
        host = esc(HOST)
        rule_x = KEY_X + (len(HOST) + 7) * 8 + 8
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" font-size="14" font-weight="700">'
                 f'<tspan fill="{GREEN}">{host}</tspan><tspan fill="{MUTED}">@</tspan>'
                 f'<tspan fill="{ACCENT}">github</tspan></text>'
                 f'<line x1="{rule_x}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "sec":
        title = esc(row[1])
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{SECTION}" font-size="12.5" font-weight="700">'
                 f'&#8212; {title}</text>'
                 f'<line x1="{KEY_X + 12 + len(row[1])*8}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "kv":
        key, val = esc(row[1]), esc(row[2])
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{KEY}" font-size="12.5" font-weight="700">{key}</text>'
                 f'<text x="{VAL_X}" y="{y:.1f}" fill="{INK}" font-size="12.5">{val}</text>')
    elif kind == "bul":
        txt = esc(row[1])
        inner = (f'<circle cx="{KEY_X+3}" cy="{y-4:.1f}" r="2.5" fill="{GREEN}"/>'
                 f'<text x="{KEY_X+14}" y="{y:.1f}" fill="{INK}" font-size="12.5">{txt}</text>')
    else:
        continue
    parts.append(rise(inner, i))
    y += LINE_H

# ---------------------------------------------------------------------------
#  SNAKE -- a snake-game snake that steps cell by cell around the panel (top
#  lane under the title bar, down the right edge, a zig-zag through the free
#  space under Highlights, back up the left edge). Like the real game it eats
#  food, GROWS two segments per bite, and the score ticks up; each lap the
#  board resets. The head faces where it's going, eyes + flicking tongue.
#  Pure SMIL (discrete animateMotion steps) so it runs inside <img> on GitHub.
# ---------------------------------------------------------------------------
CELL = 10         # grid step in px (every route leg is a multiple of this)
SEG = 9           # drawn segment size (CELL - SEG = the gap between scales)
STEP_T = 0.045    # seconds per step
BASE_LEN = 14     # length at the start of each lap
GROW = 2          # segments gained per food
# the snake always animates unless SNAKE_STATIC=1 (STATIC=1 only freezes the text rows)
SNAKE_STATIC = bool(os.environ.get("SNAKE_STATIC"))
SNAKE_HEAD = "#56d364"
SNAKE_BODY = ("#2ea043", "#238636")   # alternating scales
SNAKE_EDGE = "#0f5323"
FOOD = "#ff7b72"
FOOD_AT = (0.12, 0.31, 0.47, 0.63, 0.86)  # where on the lap the food sits

# corners of the route; every leg must be a multiple of CELL
ROUTE = [(10, 40), (470, 40), (470, 360), (400, 360), (400, 330), (340, 330), (340, 360),
         (240, 360), (240, 330), (180, 330), (180, 360), (10, 360), (10, 40)]


def route_cells(route):
    cells = []
    for (x1, y1), (x2, y2) in zip(route, route[1:]):
        n = (abs(x2 - x1) + abs(y2 - y1)) // CELL
        dx, dy = (x2 - x1) // n, (y2 - y1) // n
        cells += [(x1 + dx * i, y1 + dy * i) for i in range(n)]
    return cells


def heading(cells, i):
    """degrees the head faces at cell i (0 = right, 90 = down)."""
    (x1, y1), (x2, y2) = cells[i], cells[(i + 1) % len(cells)]
    return {(1, 0): 0, (0, 1): 90, (-1, 0): 180, (0, -1): 270}[
        ((x2 > x1) - (x2 < x1), (y2 > y1) - (y2 < y1))]


def snake_layer(cells):
    n = len(cells)
    period = n * STEP_T
    dur = f'dur="{period:.2f}s" repeatCount="indefinite"'
    sq = SEG / 2
    max_len = BASE_LEN + GROW * len(FOOD_AT)
    out = ['<g>']

    # ---- food: pulsing pellet + glow; vanishes as the head arrives, back half a lap later.
    #      on the bite: a burst ring and a floating "+10".
    food_idx = [int(n * f) for f in FOOD_AT]
    eat_t = [fi / n for fi in food_idx]
    for fi, t in zip(food_idx, eat_t):
        fx, fy = cells[fi]
        pellet = (f'<circle cx="{fx}" cy="{fy}" r="6" fill="{FOOD}" opacity=".18"/>'
                  f'<circle cx="{fx}" cy="{fy}" r="3.4" fill="{FOOD}">'
                  + ("" if SNAKE_STATIC else
                     '<animate attributeName="r" values="3;4;3" dur="0.9s" repeatCount="indefinite"/>')
                  + '</circle>')
        if SNAKE_STATIC:
            out.append(pellet)
            continue
        back = t + 0.5
        if back < 1:
            kt, vals = f"0;{t:.4f};{back:.4f};1", "1;0;1;1"
        else:
            kt, vals = f"0;{back - 1:.4f};{t:.4f};1", "0;1;0;0"
        out.append(f'<g>{pellet}<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" '
                   f'calcMode="discrete" {dur}/></g>')
        t2, t3 = t + 0.002, t + 0.045
        ktb = f"0;{t:.4f};{t2:.4f};{t3:.4f};1"
        out.append(f'<circle cx="{fx}" cy="{fy}" r="3" fill="none" stroke="{FOOD}" stroke-width="1.5" opacity="0">'
                   f'<animate attributeName="r" values="3;3;3;14;14" keyTimes="{ktb}" {dur}/>'
                   f'<animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="{ktb}" {dur}/></circle>')
        t4 = t + 0.07
        ktp = f"0;{t:.4f};{t2:.4f};{t4:.4f};1"
        # pop text floats up, except in the top lane where it would hit the title bar
        ty, rise_px = (fy + 18, -6) if fy < 60 else (fy - 8, -16)
        tx, anchor = (fx - 9, "end") if fx > W - 40 else ((fx + 9, "start") if fx < 40 else (fx, "middle"))
        out.append(f'<text x="{tx}" y="{ty}" fill="#ffa198" font-size="10" font-weight="700" '
                   f'text-anchor="{anchor}" opacity="0">+10'
                   f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{ktp}" {dur}/>'
                   f'<animateTransform attributeName="transform" type="translate" '
                   f'values="0 0;0 0;0 0;0 {rise_px};0 {rise_px}" keyTimes="{ktp}" {dur}/></text>')

    # ---- body, tail first so the head draws on top. segment k trails the head by k
    #      cells (a negative begin of (n-k) steps). segments past BASE_LEN only
    #      appear once enough food has been eaten this lap -> the snake grows.
    values = ";".join(f"{x},{y}" for x, y in cells)
    head_i = 46  # where the frozen SNAKE_STATIC frame puts the head
    for k in reversed(range(max_len)):
        if k == 0:
            # head: rounded front, two eyes and a tongue, rotated to face the direction of travel
            shape = (f'<rect x="{-sq - 0.5}" y="{-sq - 0.5}" width="{SEG + 1}" height="{SEG + 1}" rx="3.6" '
                     f'fill="{SNAKE_HEAD}" stroke="{SNAKE_EDGE}" stroke-width=".8"/>'
                     f'<circle cx="1.6" cy="-2.3" r="1.5" fill="#fff"/><circle cx="2.1" cy="-2.3" r=".8" fill="#0d1117"/>'
                     f'<circle cx="1.6" cy="2.3" r="1.5" fill="#fff"/><circle cx="2.1" cy="2.3" r=".8" fill="#0d1117"/>'
                     f'<path d="M{sq + 0.5},0 h3.2 m0,0 l1.6,-1.4 m-1.6,1.4 l1.6,1.4" stroke="#ff5f56" '
                     f'stroke-width=".9" stroke-linecap="round" fill="none">'
                     + ("" if SNAKE_STATIC else
                        '<animate attributeName="opacity" values="1;0;0;1" keyTimes="0;.3;.8;1" '
                        'calcMode="discrete" dur="0.7s" repeatCount="indefinite"/>')
                     + '</path>')
            if SNAKE_STATIC:
                shape = f'<g transform="rotate({heading(cells, head_i)})">{shape}</g>'
            else:
                rots = ";".join(str(heading(cells, i)) for i in range(n))
                shape = (f'<g>{shape}<animateTransform attributeName="transform" type="rotate" '
                         f'values="{rots}" calcMode="discrete" {dur}/></g>')
        else:
            fade = 1 - (k / max_len) * 0.45
            shape = (f'<rect x="{-sq}" y="{-sq}" width="{SEG}" height="{SEG}" rx="2.4" '
                     f'fill="{SNAKE_BODY[k % 2]}" stroke="{SNAKE_EDGE}" stroke-width=".6" opacity="{fade:.2f}"/>'
                     f'<rect x="{-sq + 2}" y="{-sq + 1.6}" width="{SEG - 4}" height="1.6" rx=".8" '
                     f'fill="#7ee787" opacity=".35"/>')
        if SNAKE_STATIC:
            if k >= BASE_LEN:
                continue
            x, y = cells[(head_i - k) % n]
            out.append(f'<g transform="translate({x},{y})">{shape}</g>')
            continue
        grow = ""
        if k >= BASE_LEN:
            t = eat_t[(k - BASE_LEN) // GROW]
            grow = (f'<animate attributeName="opacity" values="0;1" keyTimes="0;{t:.4f}" '
                    f'calcMode="discrete" {dur}/>')
        out.append(f'<g opacity="{0 if grow else 1}">{shape}{grow}<animateMotion values="{values}" '
                   f'calcMode="discrete" dur="{period:.2f}s" '
                   f'begin="{-((n - k) % n) * STEP_T:.3f}s" repeatCount="indefinite"/></g>')

    # ---- score + length in the title bar, one label per stretch between bites
    if not SNAKE_STATIC:
        bounds = [0.0] + eat_t + [1.0]
        for i in range(len(bounds) - 1):
            a, b = bounds[i], bounds[i + 1]
            out.append(f'<text x="{W - PAD}" y="{TITLEBAR_H/2 + 4}" fill="{SNAKE_HEAD}" font-size="10.5" '
                       f'text-anchor="end" opacity="0">&#9632; {i * 10:03d}'
                       f'<tspan fill="{MUTED}"> len {BASE_LEN + GROW * i}</tspan>'
                       f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{a:.4f};{b:.4f}" '
                       f'calcMode="discrete" {dur}/></text>')
    out.append("</g>")
    return "".join(out)


parts.append(snake_layer(route_cells(ROUTE)))
parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", W, "x", H, "content_bottom", round(y))
