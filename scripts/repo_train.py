#!/usr/bin/env python3
"""
REPO EXPRESS -- your most recently pushed public repos as a train. One
carriage per repo, painted in the repo's language colour (GitHub's own
colours), with the name, language, stars and how long ago it was pushed. A
steam locomotive pulls it, puffing smoke, headlight on; wheels turn at the
right speed for the distance travelled.

This is a library: render_skyline_svg.py calls train_layer() to run the train
along a viaduct in front of the contribution city. Data comes from
data/repos.json (fetch_repos.py, public repos only), refreshed daily.
"""
import datetime
import html
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "repos.json")

# ===========================================================================
#  EDIT THIS
# ===========================================================================
MAX_CARS = 8
EXCLUDE = set()              # repo names to keep off the train, e.g. {"some-repo"}
REQUIRE_DESCRIPTION = True   # only repos with a description (they make better carriages)
SKIP_FORKS = True
# ===========================================================================

SPEED = 70.0                 # px per second
CAR_H = 46
GAP = 10                     # coupler gap between carriages

MUTED = "#7d8590"
INK = "#e6edf3"

LANG_COLORS = {
    "Python": "#3572A5", "Rust": "#dea584", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "HTML": "#e34c26", "CSS": "#663399", "Kotlin": "#A97BFF", "Jupyter Notebook": "#DA5B0B",
    "Go": "#00ADD8", "Java": "#b07219", "C++": "#f34b7d", "C": "#555555", "Shell": "#89e051",
    "Swift": "#F05138", "Dart": "#00B4AB", "Ruby": "#701516", "C#": "#178600", "Vue": "#41b883",
}
DEFAULT_COLOR = "#8b949e"


def esc(s):
    return html.escape(s or "")


def ago(iso, now):
    if not iso:
        return ""
    then = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = (now - then).days
    if days < 1:
        return "today"
    if days < 14:
        return f"{days}d ago"
    if days < 60:
        return f"{days // 7}w ago"
    if days < 730:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def pick(data):
    user = data.get("username", "")
    out = []
    for r in data.get("repos", []):
        if r["name"].lower() == user.lower() or r["name"] in EXCLUDE:
            continue
        if SKIP_FORKS and r.get("fork"):
            continue
        if r.get("archived") or r.get("private"):   # public repos only, even if the data says otherwise
            continue
        if REQUIRE_DESCRIPTION and not (r.get("description") or "").strip():
            continue
        out.append(r)
        if len(out) == MAX_CARS:
            break
    return out


def wheel(cx, cy, r, spin_dur, static):
    spokes = "".join(f'<line x1="0" y1="0" x2="{r * 0.82:.1f}" y2="0" transform="rotate({a})"/>'
                     for a in range(0, 360, 60 if r > 8 else 90))
    spin = "" if static else (f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" '
                              f'dur="{spin_dur:.2f}s" repeatCount="indefinite"/>')
    return (f'<g transform="translate({cx:.1f},{cy:.1f})"><circle r="{r}" fill="#21262d" stroke="#8b949e" stroke-width="1.4"/>'
            f'<g stroke="#8b949e" stroke-width="1">{spokes}{spin}</g>'
            f'<circle r="{r * 0.22:.1f}" fill="#c9d1d9"/></g>')


def car(x, repo, now, rail_y, static):
    name = repo["name"]
    lang = repo.get("language") or "—"
    col = LANG_COLORS.get(repo.get("language"), DEFAULT_COLOR)
    stars = repo.get("stargazers_count") or 0
    meta = f"{lang}  ★ {stars}  · {ago(repo.get('pushed_at'), now)}"
    w = max(118, len(name) * 7.2 + 28, len(meta) * 6.2 + 28)
    top = rail_y - 8 - CAR_H
    r_w = 6.5
    p = [f'<g><title>{esc(name)}: {esc(repo.get("description"))}</title>']
    # roof + body + corrugation
    p.append(f'<rect x="{x - 2:.1f}" y="{top - 4}" width="{w + 4:.1f}" height="6" rx="2" fill="#30363d"/>')
    p.append(f'<rect x="{x:.1f}" y="{top}" width="{w:.1f}" height="{CAR_H}" rx="4" fill="{col}"/>')
    ribs = "".join(f'<line x1="{x + i:.1f}" y1="{top + 3}" x2="{x + i:.1f}" y2="{top + CAR_H - 3}"/>'
                   for i in range(7, int(w) - 3, 8))
    p.append(f'<g stroke="#000" stroke-opacity=".18" stroke-width="1.2">{ribs}</g>')
    p.append(f'<rect x="{x:.1f}" y="{top}" width="{w:.1f}" height="{CAR_H}" rx="4" fill="none" '
             f'stroke="#000" stroke-opacity=".35"/>')
    # label plate
    p.append(f'<rect x="{x + 7:.1f}" y="{top + 7}" width="{w - 14:.1f}" height="{CAR_H - 14}" rx="3" '
             f'fill="#0d1117" fill-opacity=".86"/>')
    p.append(f'<text x="{x + 14:.1f}" y="{top + 21}" fill="{INK}" font-size="11.5" font-weight="700">{esc(name)}</text>')
    p.append(f'<circle cx="{x + 17:.1f}" cy="{top + 31.5}" r="3" fill="{col}"/>'
             f'<text x="{x + 24:.1f}" y="{top + 35}" fill="{MUTED}" font-size="10">{esc(meta)}</text>')
    # chassis + bogies
    p.append(f'<rect x="{x + 4:.1f}" y="{top + CAR_H}" width="{w - 8:.1f}" height="4" fill="#161b22"/>')
    spin = 2 * math.pi * r_w / SPEED
    for wx in (x + 16, x + 30, x + w - 30, x + w - 16):
        p.append(wheel(wx, rail_y - r_w, r_w, spin, static))
    p.append("</g>")
    return "".join(p), w


def locomotive(x, rail_y, static):
    """steam engine facing right; returns svg, width, chimney top (for smoke)."""
    w = 150
    base = rail_y - 12
    p = []
    # cab (rear, left)
    p.append(f'<rect x="{x}" y="{base - 62}" width="44" height="62" rx="3" fill="#1b2a40" stroke="#0b111b"/>')
    p.append(f'<rect x="{x - 3}" y="{base - 68}" width="50" height="8" rx="2" fill="#30363d"/>')
    p.append(f'<rect x="{x + 9}" y="{base - 52}" width="26" height="18" rx="2" fill="#f2cc60" fill-opacity=".85"/>')
    # boiler
    p.append(f'<rect x="{x + 40}" y="{base - 44}" width="88" height="34" rx="12" fill="#22324a" stroke="#0b111b"/>')
    for bx in (x + 62, x + 86, x + 108):
        p.append(f'<rect x="{bx}" y="{base - 44}" width="3" height="34" fill="#f2cc60" fill-opacity=".55"/>')
    p.append(f'<text x="{x + 84}" y="{base - 22}" fill="#f2cc60" font-size="7.5" font-weight="700" '
             f'text-anchor="middle" letter-spacing="1">REPO EXPRESS</text>')
    # smokebox front + chimney + dome
    p.append(f'<rect x="{x + 124}" y="{base - 46}" width="14" height="38" rx="5" fill="#161b22" stroke="#0b111b"/>')
    p.append(f'<path d="M{x + 110},{base - 44} l3,-18 h12 l3,18 Z" fill="#161b22"/>')
    p.append(f'<rect x="{x + 108}" y="{base - 66}" width="20" height="5" rx="2" fill="#30363d"/>')
    p.append(f'<ellipse cx="{x + 82}" cy="{base - 45}" rx="9" ry="6" fill="#30363d"/>')
    # headlight + beam
    p.append(f'<path d="M{x + 140},{base - 34} L{x + 300},{base - 64} L{x + 300},{base - 4} Z" fill="url(#lamp)"/>')
    p.append(f'<circle cx="{x + 139}" cy="{base - 34}" r="4.5" fill="#fff3b0" stroke="#30363d"/>')
    # cowcatcher + chassis
    p.append(f'<path d="M{x + 136},{base - 8} L{x + 152},{base + 6} L{x + 128},{base + 6} Z" fill="#da3633"/>')
    p.append(f'<rect x="{x}" y="{base - 10}" width="{w - 14}" height="6" fill="#0b111b"/>')
    # wheels: two big drivers + small leading wheel, joined by a coupling rod
    big, small = 13, 7
    spin_b = 2 * math.pi * big / SPEED
    spin_s = 2 * math.pi * small / SPEED
    for wx in (x + 58, x + 92):
        p.append(wheel(wx, rail_y - big, big, spin_b, static))
    p.append(wheel(x + 124, rail_y - small, small, spin_s, static))
    p.append(wheel(x + 20, rail_y - small, small, spin_s, static))
    rod_y = rail_y - big
    rod = (f'<line x1="{x + 58}" y1="{rod_y}" x2="{x + 92}" y2="{rod_y}" stroke="#c9d1d9" stroke-width="2.4" '
           f'stroke-linecap="round"/>')
    if not static:
        r = big * 0.55
        circle = ";".join(f"{r * math.cos(a / 8 * 6.2832):.1f} {r * math.sin(a / 8 * 6.2832):.1f}"
                          for a in range(9))
        rod = (f'<g>{rod}<animateTransform attributeName="transform" type="translate" values="{circle}" '
               f'dur="{spin_b:.2f}s" repeatCount="indefinite"/></g>')
    p.append(rod)
    return "".join(p), w, (x + 118, base - 66)


def smoke(cx, cy, static):
    if static:
        return "".join(f'<circle cx="{cx - i * 16}" cy="{cy - 8 - i * 7}" r="{5 + i * 2.5}" fill="#8b949e" '
                       f'fill-opacity="{0.5 - i * 0.1:.2f}"/>' for i in range(4))
    out = []
    period = 1.6
    for i in range(6):
        b = -i * period / 6
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="4" fill="#9aa4ae" opacity="0">'
            f'<animate attributeName="cy" values="{cy};{cy - 46}" dur="{period}s" begin="{b:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cx" values="{cx};{cx - 70}" dur="{period}s" begin="{b:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="4;15" dur="{period}s" begin="{b:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values=".7;0" dur="{period}s" begin="{b:.2f}s" repeatCount="indefinite"/>'
            f'</circle>')
    return "".join(out)


def load():
    if not os.path.exists(IN_PATH):
        return {"username": "", "repos": []}
    with open(IN_PATH) as f:
        return json.load(f)


def train_layer(data, rail_y, width, static=False, start_frac=0.7):
    """the whole train as one <g>, looping left -> right across `width`.
    Returns (svg, n_cars). The locomotive starts start_frac of the way across."""
    now = datetime.datetime.now(datetime.timezone.utc)
    repos = pick(data)
    widths = [car(0, r, now, rail_y, static)[1] for r in repos]
    cars_svg, x = [], 0.0
    # the oldest pick rides at the back, the newest right behind the engine
    for r, w in zip(reversed(repos), reversed(widths)):
        cars_svg.append(car(x, r, now, rail_y, static)[0])
        cars_svg.append(f'<rect x="{x + w:.1f}" y="{rail_y - 20}" width="{GAP}" height="3" fill="#30363d"/>')
        x += w + GAP
    loco_svg, loco_w, chimney = locomotive(x, rail_y, static)
    train_len = x + loco_w
    inner = ("<defs><linearGradient id=\"lamp\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"0\">"
             "<stop offset=\"0\" stop-color=\"#fff3b0\" stop-opacity=\".4\"/>"
             "<stop offset=\"1\" stop-color=\"#fff3b0\" stop-opacity=\"0\"/></linearGradient></defs>"
             + "".join(cars_svg) + loco_svg + smoke(*chimney, static))
    if static:
        return f'<g transform="translate({width * start_frac - train_len:.0f},0)">{inner}</g>', len(repos)
    dur = (width + train_len + 40) / SPEED
    begin = width * start_frac / SPEED
    return (f'<g>{inner}<animateTransform attributeName="transform" type="translate" '
            f'from="{-train_len:.0f} 0" to="{width + 40} 0" dur="{dur:.1f}s" begin="{-begin:.1f}s" '
            f'repeatCount="indefinite"/></g>'), len(repos)
