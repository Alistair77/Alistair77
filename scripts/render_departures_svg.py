#!/usr/bin/env python3
"""
DEPARTURES -- a split-flap station board for the Repo Express.

Each row is one public repo "departing" with its latest commit: time and date
(UTC), the repo, the commit message as the destination, and a status
(BOARDING if it landed in the last 24h, DEPARTED otherwise). The flaps clatter
through random characters and settle left to right, row by row, and the board
re-flips every LOOP seconds like a real one refreshing. Along the bottom an
amber LED ticker scrolls your year in numbers.

Reads data/departures.json (fetch_departures.py) and data/contributions.json,
writes departures.svg. Run daily by .github/workflows/update-profile-art.yml.
Pure SMIL so it animates inside <img>. STATIC=1 renders the settled board.
"""
import datetime
import html
import json
import os
import random
import re
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
DEPARTURES = os.path.join(HERE, "..", "data", "departures.json")
CONTRIB = os.path.join(HERE, "..", "data", "contributions.json")
OUT = os.path.join(HERE, "..", "departures.svg")
STATIC = bool(os.environ.get("STATIC"))
HOST = os.environ.get("GH_PROFILE_USER", "Alistair77")

ROWS = 4
LOOP = 16.0                 # seconds between board refreshes
BOARD_TZ = "UTC"            # e.g. "Asia/Kolkata" to show times in your local zone
NEXT_RUN_UTC = (6, 17)      # the workflow's cron time, shown in the ticker

W = 860
PAD = 22
TITLEBAR_H = 30
# columns, in tiles; one blank tile between columns
COLS = [("TIME", 5), ("DATE", 6), ("REPO", 16), ("DESTINATION", 30), ("STATUS", 8)]
N_TILES = sum(n for _, n in COLS) + len(COLS) - 1
PITCH = (W - 2 * PAD) / N_TILES
TILE_W, TILE_H = PITCH - 1.6, 20
ROW_PITCH = 25
HEAD_Y = 42                 # top of the big DEPARTURES tiles
LABEL_Y = 86                # baseline of the column labels
ROWS_Y = 92                 # top of the first row of tiles
TICKER_Y = ROWS_Y + (ROWS - 1) * ROW_PITCH + TILE_H + 12
H = TICKER_Y + 20 + 12

INK = "#f0f6fc"
MUTED = "#7d8590"
AMBER = "#f2cc60"
GREEN = "#39d353"
FRAME = "#1f6feb"
TILE = "#161b22"
FLAP_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:;-+/&'!?#()@=")


def board_zone():
    return datetime.timezone.utc if BOARD_TZ == "UTC" else zoneinfo.ZoneInfo(BOARD_TZ)


def next_run(now):
    run = now.replace(hour=NEXT_RUN_UTC[0], minute=NEXT_RUN_UTC[1], second=0, microsecond=0)
    if run <= now:
        run += datetime.timedelta(days=1)
    local = run.astimezone(board_zone())
    return f"{local:%H:%M} {local.tzname()}"


def board_text(s, width):
    """uppercase, board-safe characters, cut at a word boundary to fit."""
    s = s.upper().replace("—", "-").replace("–", "-")
    s = "".join(c if c in ALLOWED else " " for c in s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= width:
        return s.ljust(width)
    cut = s[:width]
    space = cut.rfind(" ")
    if space >= width - 8:
        cut = cut[:space]
    return cut.rstrip(" ,.;:-").ljust(width)


def clean_message(msg):
    msg = re.sub(r"\s*\(#\d+\)\s*$", "", msg)                     # squash-merge PR suffix
    msg = re.sub(r"^[a-z]+(\([^)]*\))?!?:\s*", "", msg)          # conventional-commit prefix
    return msg[:1].upper() + msg[1:]


def rows_from(data, now):
    seen, rows = set(), []
    for d in sorted(data.get("departures", []), key=lambda d: d["date"], reverse=True):
        if d["repo"] in seen:
            continue                                               # one departure per repo: its latest commit
        seen.add(d["repo"])
        when = datetime.datetime.fromisoformat(d["date"].replace("Z", "+00:00"))
        boarding = (now - when).total_seconds() < 86400
        when = when.astimezone(board_zone())
        rows.append({
            "time": when.strftime("%H:%M"),
            "date": when.strftime("%d %b").upper(),
            "repo": d["repo"],
            "dest": clean_message(d["message"]),
            "status": "BOARDING" if boarding else "DEPARTED",
            "title": f'{d["repo"]}: {d["message"]} ({when:%Y-%m-%d %H:%M} {when.tzname()})',
        })
        if len(rows) == ROWS:
            break
    return rows


def col_starts():
    starts, i = [], 0
    for _, n in COLS:
        starts.append(i)
        i += n + 1
    return starts


def cells_x(first_tile, n):
    """x centres for n tiles starting at tile index first_tile."""
    return " ".join(f"{PAD + (first_tile + i) * PITCH + TILE_W / 2:.1f}" for i in range(n))


def flap_text(chars, first_tile, y, fill, extra=""):
    """one <text> with a glyph centred on each tile (x list + text-anchor middle)."""
    xs = cells_x(first_tile, len(chars))
    return (f'<text x="{xs}" y="{y:.1f}" fill="{fill}" font-size="13" font-weight="700" '
            f'text-anchor="middle" xml:space="preserve">{html.escape(chars)}{extra}</text>')


def shown(a, b):
    """discrete visibility window [a, b) seconds within the loop."""
    if STATIC:
        return ""
    return (f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{a / LOOP:.4f};{b / LOOP:.4f}" '
            f'calcMode="discrete" dur="{LOOP}s" repeatCount="indefinite"/>')


def hidden(a, b):
    """visible except during [a, b) within the loop."""
    if STATIC:
        return ""
    return (f'<animate attributeName="opacity" values="1;0;1" keyTimes="0;{a / LOOP:.4f};{b / LOOP:.4f}" '
            f'calcMode="discrete" dur="{LOOP}s" repeatCount="indefinite"/>')


def ticker(contrib, now):
    cs = contrib.get("current_streak", {}).get("length", 0)
    ls = contrib.get("longest_streak", {}).get("length", 0)
    best = contrib.get("best_day", {}).get("count", 0)
    total = contrib.get("total_contributions", 0)
    parts = ["ALL ABOARD THE REPO EXPRESS", f"{total:,} CONTRIBUTIONS THIS YEAR",
             f"CURRENT STREAK {cs} DAY{'S' if cs != 1 else ''}", f"LONGEST {ls} DAYS",
             f"BEST DAY {best} COMMITS", f"NEXT DEPARTURE {next_run(now)}"]
    msg = "   ★   ".join(parts) + "   ★   "
    adv = 7.4
    L = len(msg) * adv
    x0, y0, w = PAD, TICKER_Y, W - 2 * PAD
    text = lambda x: (f'<text x="{x:.1f}" y="{y0 + 14}" fill="{AMBER}" font-size="11.5" font-weight="700" '
                      f'textLength="{L:.1f}" lengthAdjust="spacing" xml:space="preserve">{html.escape(msg)}</text>')
    move = "" if STATIC else (f'<animateTransform attributeName="transform" type="translate" from="0 0" '
                              f'to="{-L:.1f} 0" dur="{L / 38:.1f}s" repeatCount="indefinite"/>')
    return (f'<rect x="{x0}" y="{y0}" width="{w}" height="20" rx="3" fill="#0b0d10" stroke="#21262d"/>'
            f'<g clip-path="url(#tick)"><g>{text(x0 + 8)}{text(x0 + 8 + L)}{move}</g>'
            f'<rect x="{x0}" y="{y0}" width="{w}" height="20" fill="url(#led)"/></g>')


def loco_icon(x, y):
    return (f'<g transform="translate({x},{y})" fill="none" stroke="{AMBER}" stroke-width="1.6">'
            f'<rect x="1" y="2" width="20" height="18" rx="5"/><rect x="5" y="6" width="12" height="6" rx="1.5"/>'
            f'<circle cx="6.5" cy="16" r="1.4" fill="{AMBER}"/><circle cx="15.5" cy="16" r="1.4" fill="{AMBER}"/>'
            f'<path d="M4 20 L1 24 M18 20 L21 24"/></g>')


def render(dep, contrib, now):
    rnd = random.Random(77)
    rows = rows_from(dep, now)
    starts = col_starts()
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f"<title>Departures: the latest commit to each of {HOST}'s recently active public repos</title>",
        "<defs>"
        '<linearGradient id="dbg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0a0e14"/></linearGradient>'
        # one flap tile (with its hinge line) per pattern cell, aligned to the board grid
        f'<pattern id="tiles" x="{PAD}" y="{ROWS_Y}" width="{PITCH:.3f}" height="{ROW_PITCH}" patternUnits="userSpaceOnUse">'
        f'<rect width="{TILE_W:.2f}" height="{TILE_H}" rx="2" fill="{TILE}"/>'
        f'<rect y="{TILE_H / 2 - 0.5}" width="{TILE_W:.2f}" height="1" fill="#05070a"/></pattern>'
        f'<pattern id="led" width="3" height="3" patternUnits="userSpaceOnUse">'
        f'<rect width="3" height="1" fill="#0b0d10" opacity=".55"/><rect width="1" height="3" fill="#0b0d10" opacity=".55"/></pattern>'
        f'<clipPath id="tick"><rect x="{PAD + 1}" y="{TICKER_Y}" width="{W - 2 * PAD - 2}" height="20" rx="3"/></clipPath>'
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#dbg)"/>',
    ]
    # ---- title bar ----
    p.append(f'<rect width="{W}" height="{TITLEBAR_H}" rx="12" fill="#0b111b"/>'
             f'<rect y="{TITLEBAR_H - 12}" width="{W}" height="12" fill="#0b111b"/>'
             f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity=".35"/>')
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{22 + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{c}"/>')
    p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
             f'{html.escape(HOST)}@github: ~$ ./departures --live</text>')

    # ---- header: DEPARTURES in big flaps + the board clock ----
    big_pitch, big_w, big_h = 19, 17, 26
    hx = PAD + 34
    p.append(loco_icon(PAD + 2, HEAD_Y + 1))
    for i, ch in enumerate("DEPARTURES"):
        x = hx + i * big_pitch
        p.append(f'<rect x="{x}" y="{HEAD_Y}" width="{big_w}" height="{big_h}" rx="2" fill="{TILE}"/>'
                 f'<rect x="{x}" y="{HEAD_Y + big_h / 2 - 0.5}" width="{big_w}" height="1" fill="#05070a"/>'
                 f'<text x="{x + big_w / 2}" y="{HEAD_Y + 19}" fill="{AMBER}" font-size="17" font-weight="700" '
                 f'text-anchor="middle">{ch}</text>')
    local_now = now.astimezone(board_zone())
    clock = local_now.strftime("%H:%M")
    cx0 = W - PAD - 5 * big_pitch - 40
    for i, ch in enumerate(clock):
        x = cx0 + i * big_pitch
        if ch != ":":
            p.append(f'<rect x="{x}" y="{HEAD_Y}" width="{big_w}" height="{big_h}" rx="2" fill="{TILE}"/>'
                     f'<rect x="{x}" y="{HEAD_Y + big_h / 2 - 0.5}" width="{big_w}" height="1" fill="#05070a"/>')
        p.append(f'<text x="{x + big_w / 2}" y="{HEAD_Y + 19}" fill="{INK}" font-size="17" font-weight="700" '
                 f'text-anchor="middle">{ch}</text>')
    p.append(f'<text x="{W - PAD}" y="{HEAD_Y + 11}" fill="{MUTED}" font-size="9.5" text-anchor="end">{local_now.tzname()}</text>'
             f'<text x="{W - PAD}" y="{HEAD_Y + 23}" fill="{MUTED}" font-size="9.5" text-anchor="end">updated</text>')

    # ---- column labels + the empty flap grid ----
    for (label, _), st in zip(COLS, starts):
        p.append(f'<text x="{PAD + st * PITCH:.1f}" y="{LABEL_Y}" fill="{MUTED}" font-size="9.5" '
                 f'letter-spacing="1">{label}</text>')
    for (_, n), st in zip(COLS, starts):
        p.append(f'<rect x="{PAD + st * PITCH:.2f}" y="{ROWS_Y}" width="{n * PITCH:.2f}" '
                 f'height="{ROWS * ROW_PITCH}" fill="url(#tiles)"/>')

    # ---- the rows: scramble, settle left -> right, hold; re-flip each LOOP ----
    frame_t, frames = 0.07, 4
    for r, row in enumerate(rows):
        y = ROWS_Y + r * ROW_PITCH + 14.6
        t0 = 0.6 + r * 0.45
        t_end = t0 + frames * frame_t
        segs = [(row["time"].ljust(5), "time"), (row["date"].ljust(6), "date"),
                (board_text(row["repo"], 16), "repo"), (board_text(row["dest"], 30), "dest"),
                (row["status"].ljust(8), "status")]
        full = " ".join(s for s, _ in segs)               # the whole row, tile by tile
        p.append(f'<g><title>{html.escape(row["title"])}</title>')
        # scramble frames: frame k has the left k/frames of the row settled, the rest random
        for k in range(frames):
            settled = int(len(full) * k / frames)
            chars = "".join(c if i < settled else (rnd.choice(FLAP_CHARS) if c != " " or rnd.random() < .25 else " ")
                            for i, c in enumerate(full))
            if not STATIC:
                p.append(f'<g opacity="0">{flap_text(chars, 0, y, "#c9d1d9")}'
                         f'{shown(t0 + k * frame_t, t0 + (k + 1) * frame_t)}</g>')
        # the settled row: time in amber, repo + destination in white, status in its colour
        status_col = AMBER if row["status"] == "BOARDING" else GREEN
        settled = [flap_text(segs[0][0], starts[0], y, AMBER),
                   flap_text(segs[1][0], starts[1], y, INK),
                   flap_text(segs[2][0], starts[2], y, INK),
                   flap_text(segs[3][0], starts[3], y, INK),
                   flap_text(segs[4][0], starts[4], y, status_col)]
        p.append(f'<g>{"".join(settled)}{hidden(t0, t_end)}</g>')
        if row["status"] == "BOARDING":
            dot_x = PAD + starts[4] * PITCH - PITCH / 2
            blink = "" if STATIC else ('<animate attributeName="opacity" values="1;.15;1" dur="1s" '
                                       'repeatCount="indefinite"/>')
            p.append(f'<circle cx="{dot_x:.1f}" cy="{y - 4.5:.1f}" r="2.6" fill="{AMBER}">{blink}</circle>')
        p.append("</g>")
    if not rows:
        p.append(f'<text x="{W / 2}" y="{ROWS_Y + 2 * ROW_PITCH}" fill="{MUTED}" font-size="12" '
                 f'text-anchor="middle">no departures yet &#183; the first commit to a public repo boards here</text>')

    # ---- LED ticker ----
    p.append(ticker(contrib, now))
    p.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}" '
             f'stroke-opacity=".55"/>')
    p.append("</svg>")
    return "".join(p)


def _selfcheck():
    assert board_text("feat: hello — world", 30).rstrip() == "FEAT: HELLO - WORLD"
    assert len(board_text("x" * 50, 30)) == 30
    assert board_text("one two three four five six seven", 16).rstrip() == "ONE TWO THREE"
    assert clean_message("feat(ui): Add dark mode (#12)") == "Add dark mode"
    assert clean_message("Revert \"thing\"") == "Revert \"thing\""
    now = datetime.datetime(2026, 11, 19, 12, tzinfo=datetime.timezone.utc)
    data = {"departures": [
        {"repo": "a", "message": "fix: x", "date": "2026-11-19T08:00:00Z"},
        {"repo": "a", "message": "older", "date": "2026-11-18T08:00:00Z"},
        {"repo": "b", "message": "y", "date": "2026-11-10T08:00:00Z"}]}
    rows = rows_from(data, now)
    assert [r["repo"] for r in rows] == ["a", "b"]                 # one row per repo, newest first
    assert rows[0]["status"] == "BOARDING" and rows[1]["status"] == "DEPARTED"
    assert rows[0]["dest"] == "X"
    assert next_run(now) == "06:17 UTC"                         # 12:00 UTC -> tomorrow 06:17
    global BOARD_TZ
    BOARD_TZ = "Asia/Kolkata"
    assert rows_from(data, now)[0]["time"] == "13:30"           # 08:00 UTC = 13:30 IST
    assert next_run(now) == "11:47 IST"
    BOARD_TZ = "UTC"
    render(data, {}, now)
    render({"departures": []}, {}, now)
    print("selfcheck ok")


if __name__ == "__main__":
    if os.environ.get("SELFCHECK"):
        _selfcheck()
        raise SystemExit
    dep = json.load(open(DEPARTURES)) if os.path.exists(DEPARTURES) else {"departures": []}
    contrib = json.load(open(CONTRIB)) if os.path.exists(CONTRIB) else {}
    svg = render(dep, contrib, datetime.datetime.now(datetime.timezone.utc))
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes, {W} x {H})")
