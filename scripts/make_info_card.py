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
#  space under Highlights, back up the left edge), eating food as it goes.
#  Pure SMIL (animateMotion with discrete steps) so it runs inside <img>.
# ---------------------------------------------------------------------------
CELL = 8          # grid step in px (path corners sit on multiples of this)
SEG = 6.5         # drawn segment size
STEP_T = 0.075    # seconds per step
SNAKE_LEN = 11
# the snake always animates unless SNAKE_STATIC=1 (STATIC=1 only freezes the text rows)
SNAKE_STATIC = bool(os.environ.get("SNAKE_STATIC"))
SNAKE_HEAD = "#56d364"
SNAKE_BODY = "#2ea043"
FOOD = "#ff7b72"

# corners of the route; every leg must be a multiple of CELL
ROUTE = [(8, 40), (472, 40), (472, 368), (400, 368), (400, 336), (336, 336), (336, 368),
         (240, 368), (240, 336), (176, 336), (176, 368), (8, 368), (8, 40)]


def route_cells(route):
    cells = []
    for (x1, y1), (x2, y2) in zip(route, route[1:]):
        n = (abs(x2 - x1) + abs(y2 - y1)) // CELL
        dx, dy = (x2 - x1) // n, (y2 - y1) // n
        cells += [(x1 + dx * i, y1 + dy * i) for i in range(n)]
    return cells


def snake_layer(cells):
    n = len(cells)
    period = n * STEP_T
    sq = SEG / 2
    out = ['<g>']
    # food: sits on the route, vanishes when the head arrives, respawns half a lap later
    food_idx = [int(n * f) for f in (0.12, 0.31, 0.47, 0.63, 0.86)]
    eat_t = []
    for fi in food_idx:
        fx, fy = cells[fi]
        t_eat = fi / n
        eat_t.append(t_eat)
        if SNAKE_STATIC:
            out.append(f'<rect x="{fx-2.5}" y="{fy-2.5}" width="5" height="5" rx="1" fill="{FOOD}"/>')
            continue
        back = t_eat + 0.5
        if back < 1:
            kt, vals = f"0;{t_eat:.4f};{back:.4f};1", "1;0;1;1"
        else:
            kt, vals = f"0;{back - 1:.4f};{t_eat:.4f};1", "0;1;0;0"
        out.append(f'<rect x="{fx-2.5}" y="{fy-2.5}" width="5" height="5" rx="1" fill="{FOOD}">'
                   f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" calcMode="discrete" '
                   f'dur="{period:.2f}s" repeatCount="indefinite"/></rect>')
    # body (tail first so the head draws on top); segment k trails the head by k cells:
    # a negative begin of (n-k) steps puts it k cells behind on the looping route
    values = ";".join(f"{x},{y}" for x, y in cells)
    for k in reversed(range(SNAKE_LEN)):
        head = k == 0
        col = SNAKE_HEAD if head else SNAKE_BODY
        op = 1 - (k / SNAKE_LEN) * 0.55
        shape = (f'<rect x="{-sq}" y="{-sq}" width="{SEG}" height="{SEG}" rx="{2.2 if head else 1.4}" '
                 f'fill="{col}" opacity="{op:.2f}"/>')
        if head:
            shape += '<circle cx="1.4" cy="-1.3" r="0.9" fill="#0d1117"/>'
        if SNAKE_STATIC:
            x, y = cells[(40 - k) % n]
            out.append(f'<g transform="translate({x},{y})">{shape}</g>')
            continue
        out.append(f'<g>{shape}<animateMotion values="{values}" calcMode="discrete" dur="{period:.2f}s" '
                   f'begin="{-((n - k) % n) * STEP_T:.3f}s" repeatCount="indefinite"/></g>')
    # score in the title bar: one counter per food eaten this lap
    if not SNAKE_STATIC:
        bounds = [0.0] + eat_t + [1.0]
        for i in range(len(bounds) - 1):
            a, b = bounds[i], bounds[i + 1]
            out.append(f'<text x="{W - PAD}" y="{TITLEBAR_H/2 + 4}" fill="{SNAKE_HEAD}" font-size="11" '
                       f'text-anchor="end" opacity="0">&#9632; score {i * 10:03d}'
                       f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{a:.4f};{b:.4f}" '
                       f'calcMode="discrete" dur="{period:.2f}s" repeatCount="indefinite"/></text>')
    out.append("</g>")
    return "".join(out)


parts.append(snake_layer(route_cells(ROUTE)))
parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", W, "x", H, "content_bottom", round(y))
