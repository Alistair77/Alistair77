#!/usr/bin/env python3
"""
TROPHY CASE -- achievements earned from your public GitHub activity, shown in
a click-to-open <details> section of the README (so it adds no height until a
visitor opens it).

  * 10 trophies: streak tiers, contribution milestones, a power day, languages,
    public repos, stars, and months active
  * unlocked ones shine gold (a glint sweeps across now and then) and show the
    date they were earned; anything earned in the last 7 days gets a NEW tag
  * locked ones show a padlock and a progress bar toward the target
  * unlocks are PERMANENT: they're recorded in data/trophies.json, so a streak
    that ages out of the rolling 12-month window doesn't re-lock its trophy.
    Unlock dates are worked out from your daily history where possible (e.g.
    the day a 7-day streak completed); repo-based ones are dated when first seen.
  * the README's summary line ("6 of 10 unlocked") is rewritten between the
    <!-- trophies:summary --> markers so the count is visible without opening

Reads data/contributions.json + data/repos.json, writes trophies.svg,
data/trophies.json and README.md. Run daily by the workflow. SELFCHECK=1 tests.
"""
import datetime
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CONTRIB = os.path.join(ROOT, "data", "contributions.json")
REPOS = os.path.join(ROOT, "data", "repos.json")
STATE = os.path.join(ROOT, "data", "trophies.json")
README = os.path.join(ROOT, "README.md")
OUT = os.path.join(ROOT, "trophies.svg")
STATIC = bool(os.environ.get("STATIC"))
HOST = os.environ.get("GH_PROFILE_USER", "Alistair77")

NEW_DAYS = 7
W = 860
PAD = 22
TITLEBAR_H = 30
COLS, GAP = 5, 12
TILE_W = (W - 2 * PAD - (COLS - 1) * GAP) / COLS
TILE_H = 112
GRID_Y = 88
H = GRID_Y + 2 * TILE_H + GAP + 38

INK = "#e6edf3"
MUTED = "#7d8590"
GOLD = "#f2cc60"
GREEN = "#3fb950"
FRAME = "#1f6feb"
LOCKED = "#484f58"

# id, title, description, metric, target, unit, icon, icon colour
TROPHIES = [
    ("roll", "ON A ROLL", "3-day streak", "streak", 3, "days", "flame3", "#ffa657"),
    ("week", "WEEK WARRIOR", "7-day streak", "streak", 7, "days", "flame7", "#ffa657"),
    ("unstoppable", "UNSTOPPABLE", "30-day streak", "streak", 30, "days", "flame30", "#ff7b72"),
    ("century", "CENTURY", "100 contributions a year", "total", 100, "", "n100", "#7ee787"),
    ("club500", "500 CLUB", "500 contributions a year", "total", 500, "", "n500", "#7ee787"),
    ("power", "POWER DAY", "25 contributions in a day", "best_day", 25, "", "bolt", GOLD),
    ("polyglot", "POLYGLOT", "5 languages across repos", "languages", 5, "", "globe", "#56d4dd"),
    ("shipyard", "SHIPYARD", "25 public repos", "repos", 25, "", "box", "#d2a8ff"),
    ("stargazer", "STARGAZER", "25 stars across repos", "stars", 25, "", "star", GOLD),
    ("allyear", "YEAR-ROUNDER", "active in all 12 months", "months", 12, "months", "calendar", "#79c0ff"),
]


# ---------------------------------------------------------------- metrics ---
def metrics(contrib, repos):
    days = contrib.get("days", [])
    me = (repos.get("username") or HOST).lower()
    pub = [r for r in repos.get("repos", []) if not r.get("private") and not r.get("fork")]
    longest, run = 0, 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    return {
        "streak": max(longest, contrib.get("longest_streak", {}).get("length", 0)),
        "total": contrib.get("total_contributions", sum(d["count"] for d in days)),
        "best_day": max((d["count"] for d in days), default=0),
        "languages": len({r["language"] for r in pub if r.get("language")}),
        "repos": len(pub),
        "stars": sum(r.get("stargazers_count") or 0 for r in pub),
        "months": len({d["date"][:7] for d in days if d["count"] > 0}),
    }


def inferred_date(metric, target, days):
    """the day a contribution-based target was first reached, from the daily history."""
    run, total, months = 0, 0, set()
    for d in days:
        c = d["count"]
        run = run + 1 if c > 0 else 0
        total += c
        if c > 0:
            months.add(d["date"][:7])
        if ((metric == "streak" and run >= target) or (metric == "total" and total >= target)
                or (metric == "best_day" and c >= target) or (metric == "months" and len(months) >= target)):
            return d["date"]
    return None   # repo/language/star counts have no daily history


def evaluate(contrib, repos, state, today):
    """-> list of trophy dicts; unlocks are recorded in (and never removed from) state."""
    m = metrics(contrib, repos)
    unlocked = state.setdefault("unlocked", {})
    out = []
    for tid, title, desc, metric, target, unit, icon, colour in TROPHIES:
        value = m[metric]
        if tid not in unlocked and value >= target:
            day = inferred_date(metric, target, contrib.get("days", []))
            # first time a repo-based trophy is seen: no history to date it, so leave it undated
            unlocked[tid] = day if day else (None if state.get("seeded") is not True else today.isoformat())
        earned = tid in unlocked
        when = unlocked.get(tid)
        is_new = bool(earned and when and (today - datetime.date.fromisoformat(when)).days < NEW_DAYS)
        out.append({"id": tid, "title": title, "desc": desc, "value": value, "target": target, "unit": unit,
                    "icon": icon, "colour": colour, "earned": earned, "when": when, "new": is_new})
    state["seeded"] = True   # from now on, newly met repo-based trophies are dated the day they're seen
    return out


def summary_line(trophies):
    n = sum(t["earned"] for t in trophies)
    new = [t["title"].title() for t in trophies if t["new"]]
    extra = f" · new: {', '.join(new)}" if new else ""
    return f"<b>🏆 Trophy case</b> · {n} of {len(trophies)} unlocked{extra} · click to open"


def update_readme(path, line):
    if not os.path.exists(path):
        return False
    s = open(path).read()
    pat = re.compile(r"(<!-- trophies:summary -->)(.*?)(<!-- /trophies:summary -->)", re.S)
    if not pat.search(s):
        return False
    new = pat.sub(lambda k: k.group(1) + line + k.group(3), s)
    if new != s:
        with open(path, "w") as f:
            f.write(new)
    return new != s


# ------------------------------------------------------------------ icons ---
def star_path(r1, r2, n=5):
    import math
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.pi / n * i - math.pi / 2
        pts.append(f"{r * math.cos(a):.1f},{r * math.sin(a):.1f}")
    return "M" + " L".join(pts) + " Z"


def icon(kind, col):
    flame = ("M0,-12 C6,-5 9,-1 9,4 A9,8.5 0 0 1 -9,4 C-9,-1 -5,-3 -4,-8 "
             "C-2,-5 0,-5 0,-12 Z")
    if kind.startswith("flame"):
        n = kind[5:]
        return (f'<path d="{flame}" fill="{col}"/>'
                f'<text y="7" fill="#0b111b" font-size="{10 if len(n) < 2 else 8.5}" font-weight="800" '
                f'text-anchor="middle">{n}</text>')
    if kind in ("n100", "n500"):
        return (f'<text y="4.5" fill="{col}" font-size="12.5" font-weight="800" text-anchor="middle" '
                f'letter-spacing="-.5">{kind[1:]}</text>')
    if kind == "bolt":
        return f'<path d="M2.5,-12 L-7,1.5 L-0.5,1.5 L-2.5,12 L7,-2 L0.5,-2 Z" fill="{col}"/>'
    if kind == "globe":
        return (f'<g fill="none" stroke="{col}" stroke-width="1.6"><circle r="10"/><ellipse rx="4.5" ry="10"/>'
                f'<path d="M-10,0 H10 M-8.5,-5 H8.5 M-8.5,5 H8.5"/></g>')
    if kind == "box":
        return (f'<g fill="none" stroke="{col}" stroke-width="1.7" stroke-linejoin="round">'
                f'<path d="M-9,-4.5 L0,-10 L9,-4.5 L9,6 L0,11 L-9,6 Z"/><path d="M-9,-4.5 L0,1 L9,-4.5 M0,1 V11"/></g>')
    if kind == "star":
        return f'<path d="{star_path(11, 4.6)}" fill="{col}"/>'
    if kind == "calendar":
        dots = "".join(f'<circle cx="{-5 + (i % 4) * 3.4:.1f}" cy="{0 + (i // 4) * 3.6:.1f}" r="1" fill="{col}"/>'
                       for i in range(12))
        return (f'<g fill="none" stroke="{col}" stroke-width="1.6"><rect x="-9" y="-8" width="18" height="17" rx="2.5"/>'
                f'<path d="M-9,-3.5 H9 M-4.5,-11 V-6 M4.5,-11 V-6"/></g>{dots}')
    return ""


def padlock(x, y):
    return (f'<g transform="translate({x:.1f},{y:.1f})"><circle r="8" fill="#0d1117" stroke="{LOCKED}"/>'
            f'<rect x="-3.6" y="-1" width="7.2" height="5.6" rx="1.2" fill="{MUTED}"/>'
            f'<path d="M-2.2,-1 V-3 A2.2,2.2 0 0 1 2.2,-3 V-1" fill="none" stroke="{MUTED}" stroke-width="1.3"/></g>')


def trophy_cup(x, y, col):
    return (f'<g transform="translate({x},{y})" fill="none" stroke="{col}" stroke-width="1.8" stroke-linejoin="round">'
            f'<path d="M-6,-8 H6 V-3 A6,6 0 0 1 -6,-3 Z" fill="{col}" fill-opacity=".25"/>'
            f'<path d="M-6,-6 H-9.5 A3.5,3.5 0 0 0 -6,-0.5 M6,-6 H9.5 A3.5,3.5 0 0 1 6,-0.5"/>'
            f'<path d="M0,3 V6 M-4,8.5 H4"/></g>')


# ----------------------------------------------------------------- render ---
def fmt_progress(t):
    unit = f" {t['unit']}" if t["unit"] else ""
    return f"{min(t['value'], t['target']):,} / {t['target']:,}{unit}"


def tile(i, t):
    col_i, row_i = i % COLS, i // COLS
    x = PAD + col_i * (TILE_W + GAP)
    y = GRID_Y + row_i * (TILE_H + GAP)
    cx, cy = x + TILE_W / 2, y + 36
    earned = t["earned"]
    p = [f'<g><title>{html.escape(t["title"].title())}: {html.escape(t["desc"])} '
         f'({fmt_progress(t)})</title>']
    p.append(f'<rect x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" '
             f'fill="{"#161b22" if earned else "#0d1117"}" stroke="{GOLD if earned else "#30363d"}" '
             f'stroke-opacity="{.45 if earned else 1}"/>')
    # medallion
    if earned:
        p.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="27" fill="{GOLD}" opacity=".08"/>'
                 f'<circle cx="{cx:.1f}" cy="{cy}" r="22" fill="#0b111b" stroke="url(#gold)" stroke-width="4"/>')
    else:
        p.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="22" fill="#0b111b" stroke="#30363d" stroke-width="4"/>')
    p.append(f'<g transform="translate({cx:.1f},{cy})">{icon(t["icon"], t["colour"] if earned else LOCKED)}</g>')
    if earned and not STATIC:
        # a glint sweeps across the medallion every few seconds
        p.append(f'<g clip-path="url(#med{i})"><rect x="{cx - 44:.1f}" y="{cy - 30}" width="8" height="60" '
                 f'fill="#fff" opacity=".35" transform="rotate(25 {cx:.1f} {cy})">'
                 f'<animateTransform attributeName="transform" type="translate" additive="sum" '
                 f'values="0 0;80 0;80 0" keyTimes="0;.18;1" dur="5s" begin="{1.2 + i * 0.45:.2f}s" '
                 f'repeatCount="indefinite"/></rect></g>')
    if not earned:
        p.append(padlock(cx + 17, cy + 17))
    # text
    p.append(f'<text x="{cx:.1f}" y="{y + 74}" fill="{INK if earned else MUTED}" font-size="10.5" font-weight="700" '
             f'letter-spacing=".8" text-anchor="middle">{html.escape(t["title"])}</text>')
    p.append(f'<text x="{cx:.1f}" y="{y + 88}" fill="{MUTED}" font-size="9" text-anchor="middle">'
             f'{html.escape(t["desc"])}</text>')
    if earned:
        when = ""
        if t["when"]:
            when = " " + datetime.date.fromisoformat(t["when"]).strftime("%d %b %Y").upper().lstrip("0")
        p.append(f'<text x="{cx:.1f}" y="{y + 103}" fill="{GREEN}" font-size="9" font-weight="700" '
                 f'letter-spacing=".5" text-anchor="middle">&#10003; UNLOCKED{when}</text>')
    else:
        bw = TILE_W - 40
        frac = max(0.0, min(1.0, t["value"] / t["target"]))
        p.append(f'<rect x="{cx - bw / 2:.1f}" y="{y + 94}" width="{bw:.1f}" height="4" rx="2" fill="#21262d"/>'
                 f'<rect x="{cx - bw / 2:.1f}" y="{y + 94}" width="{bw * frac:.1f}" height="4" rx="2" fill="{t["colour"]}" '
                 f'opacity=".8"/>'
                 f'<text x="{cx:.1f}" y="{y + 108}" fill="{MUTED}" font-size="8.5" text-anchor="middle">'
                 f'{html.escape(fmt_progress(t))}</text>')
    if t["new"]:
        p.append(f'<g transform="translate({x + TILE_W - 8:.1f},{y + 8})"><rect x="-28" y="0" width="28" height="13" rx="3" '
                 f'fill="#da3633"/><text x="-14" y="9.5" fill="#fff" font-size="8.5" font-weight="800" '
                 f'text-anchor="middle">NEW</text></g>')
    p.append("</g>")
    inner = "".join(p)
    if STATIC:
        return inner
    return (f'<g opacity="0">{inner}<animate attributeName="opacity" from="0" to="1" '
            f'begin="{0.15 + i * 0.07:.2f}s" dur=".4s" fill="freeze"/></g>')


def render(trophies):
    n = sum(t["earned"] for t in trophies)
    clips = "".join(
        f'<clipPath id="med{i}"><circle cx="{PAD + (i % COLS) * (TILE_W + GAP) + TILE_W / 2:.1f}" '
        f'cy="{GRID_Y + (i // COLS) * (TILE_H + GAP) + 36}" r="20"/></clipPath>' for i in range(len(trophies)))
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f"<title>Trophy case: {n} of {len(trophies)} achievements unlocked from public GitHub activity</title>",
        "<defs>"
        '<linearGradient id="tbg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0a0e14"/></linearGradient>'
        '<linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#fff1b8"/><stop offset=".45" stop-color="{GOLD}"/>'
        '<stop offset="1" stop-color="#b8860b"/></linearGradient>' + clips + "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#tbg)"/>',
        f'<rect width="{W}" height="{TITLEBAR_H}" rx="12" fill="#0b111b"/>'
        f'<rect y="{TITLEBAR_H - 12}" width="{W}" height="12" fill="#0b111b"/>'
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity=".35"/>',
    ]
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{22 + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{c}"/>')
    p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
             f'{html.escape(HOST)}@github: ~$ ls ~/trophies</text>')
    # header: title + overall progress
    p.append(trophy_cup(PAD + 10, 60, GOLD))
    p.append(f'<text x="{PAD + 28}" y="65" fill="{GOLD}" font-size="15" font-weight="800" letter-spacing="3">TROPHY CASE</text>')
    bw = 150
    p.append(f'<text x="{W - PAD - bw - 12}" y="64" fill="{INK}" font-size="12" font-weight="700" text-anchor="end">'
             f'{n} / {len(trophies)} <tspan fill="{MUTED}" font-weight="400">unlocked</tspan></text>'
             f'<rect x="{W - PAD - bw}" y="56" width="{bw}" height="8" rx="4" fill="#21262d"/>'
             f'<rect x="{W - PAD - bw}" y="56" width="{bw * n / max(len(trophies), 1):.1f}" height="8" rx="4" fill="url(#gold)"/>')
    for i, t in enumerate(trophies):
        p.append(tile(i, t))
    p.append(f'<text x="{W / 2}" y="{H - 16}" fill="{MUTED}" font-size="9.5" text-anchor="middle">'
             f'earned from public GitHub activity &#183; checked daily &#183; once unlocked, a trophy stays unlocked</text>')
    p.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}" '
             f'stroke-opacity=".55"/>')
    p.append("</svg>")
    return "".join(p)


def _selfcheck():
    days = [{"date": f"2026-01-{i:02d}", "count": c} for i, c in
            enumerate([1, 1, 1, 0, 30, 1, 1, 1, 1, 1, 1, 1], start=1)]
    contrib = {"days": days, "total_contributions": sum(d["count"] for d in days),
               "longest_streak": {"length": 8}}
    repos = {"username": "me", "repos": [
        {"name": f"r{i}", "language": ["Python", "Go", "Rust", "C", "Java"][i % 5], "stargazers_count": 3}
        for i in range(26)] + [{"name": "secret", "private": True, "stargazers_count": 999}]}
    assert inferred_date("streak", 3, days) == "2026-01-03"
    assert inferred_date("streak", 7, days) == "2026-01-11"         # 5th..11th
    assert inferred_date("best_day", 25, days) == "2026-01-05"
    assert inferred_date("total", 34, days) == "2026-01-06"
    m = metrics(contrib, repos)
    assert m["stars"] == 78 and m["repos"] == 26, m                # private repo ignored
    state, today = {}, datetime.date(2026, 1, 12)
    t = {x["id"]: x for x in evaluate(contrib, repos, state, today)}
    assert t["week"]["earned"] and t["week"]["when"] == "2026-01-11" and t["week"]["new"]
    assert t["polyglot"]["earned"] and t["polyglot"]["when"] is None and not t["polyglot"]["new"]  # first sighting: undated
    assert not t["unstoppable"]["earned"] and t["unstoppable"]["value"] == 8
    # permanence: the streak ages out of the window, the trophy stays
    contrib2 = {"days": [{"date": "2027-01-20", "count": 0}], "total_contributions": 0}
    t2 = {x["id"]: x for x in evaluate(contrib2, repos, state, datetime.date(2027, 1, 20))}
    assert t2["week"]["earned"] and t2["roll"]["earned"] and not t2["week"]["new"]
    # after seeding, a newly met repo trophy is dated the day it's seen
    repos3 = dict(repos, repos=repos["repos"] + [{"name": "x", "stargazers_count": 0}])
    state3 = {"unlocked": {}, "seeded": True}
    t3 = {x["id"]: x for x in evaluate(contrib, repos3, state3, today)}
    assert t3["shipyard"]["when"] == "2026-01-12" and t3["shipyard"]["new"]
    line = summary_line(list(t3.values()))
    assert "unlocked" in line and "new:" in line
    # README markers: replaced, idempotent, untouched when absent
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fp = os.path.join(d, "R.md")
        open(fp, "w").write("a <!-- trophies:summary -->old<!-- /trophies:summary --> b")
        assert update_readme(fp, "X") and open(fp).read() == "a <!-- trophies:summary -->X<!-- /trophies:summary --> b"
        assert not update_readme(fp, "X")
        open(fp, "w").write("no markers")
        assert not update_readme(fp, "X")
    render(list(t3.values()))
    print("selfcheck ok")


if __name__ == "__main__":
    if os.environ.get("SELFCHECK"):
        _selfcheck()
        raise SystemExit
    contrib = json.load(open(CONTRIB)) if os.path.exists(CONTRIB) else {}
    repos = json.load(open(REPOS)) if os.path.exists(REPOS) else {}
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    today = datetime.datetime.now(datetime.timezone.utc).date()
    trophies = evaluate(contrib, repos, state, today)
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    svg = render(trophies)
    with open(OUT, "w") as f:
        f.write(svg)
    changed = update_readme(README, summary_line(trophies))
    print(f"wrote {OUT} ({len(svg)} bytes): {sum(t['earned'] for t in trophies)}/{len(trophies)} unlocked"
          f"{'; README summary updated' if changed else ''}")
