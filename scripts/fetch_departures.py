#!/usr/bin/env python3
"""
Fetch your latest commits for the departures board (render_departures_svg.py).

Reads data/repos.json (written by fetch_repos.py from the PUBLIC repos API),
takes the most recently pushed public, non-fork, non-archived repos, and asks
the public commits API for each one's latest commits on its default branch.
Merge commits and bot commits are skipped. Writes data/departures.json.

Only public repos are ever read: the list comes from the public API, and any
repo flagged private is skipped as a second guard. No token is required
(about 9 calls a day); GITHUB_TOKEN is used for headroom when present. On any
failure the previous data/departures.json is kept so the board never breaks.

Run by .github/workflows/update-profile-art.yml after fetch_repos.py.
"""
import json
import os
import sys

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
REPOS = os.path.join(HERE, "..", "data", "repos.json")
OUT = os.path.join(HERE, "..", "data", "departures.json")
USERNAME = os.environ.get("GH_PROFILE_USER", "Alistair77")

REPOS_TO_SCAN = 8        # most recently pushed public repos to look at
PER_REPO = 6             # latest commits fetched from each
KEEP_PER_REPO = 3        # newest commits kept per repo (the board shows each repo's latest)
BOTS = {"github-actions[bot]", "dependabot[bot]", "renovate[bot]"}


def candidate_repos():
    with open(REPOS) as f:
        data = json.load(f)
    me = data.get("username", USERNAME).lower()
    repos = [r for r in data.get("repos", [])
             if not r.get("private") and not r.get("fork") and not r.get("archived")
             and r["name"].lower() != me]
    repos.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    return repos[:REPOS_TO_SCAN]


def main():
    headers = {"User-Agent": "profile-readme-bot/1.0", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    try:
        repos = candidate_repos()
        out = []
        for r in repos:
            url = f"https://api.github.com/repos/{USERNAME}/{r['name']}/commits"
            resp = requests.get(url, params={"per_page": PER_REPO}, headers=headers, timeout=30)
            if resp.status_code == 409:      # empty repository
                continue
            resp.raise_for_status()
            kept = 0
            for c in resp.json():
                if kept == KEEP_PER_REPO:
                    break
                if len(c.get("parents") or []) > 1:
                    continue
                msg = (c["commit"]["message"] or "").split("\n")[0].strip()
                login = (c.get("author") or {}).get("login") or ""
                if not msg or msg.startswith("Merge ") or login in BOTS:
                    continue
                out.append({
                    "repo": r["name"],
                    "sha": c["sha"],
                    "message": msg,
                    "date": c["commit"]["committer"]["date"],   # UTC, when it landed
                    "url": c.get("html_url"),
                })
                kept += 1
    except Exception as e:  # keep yesterday's board rather than failing the run
        print(f"departures fetch failed ({e}); keeping existing {OUT}", file=sys.stderr)
        return
    out.sort(key=lambda d: d["date"], reverse=True)
    with open(OUT, "w") as f:
        json.dump({"username": USERNAME, "departures": out}, f, indent=2)
    print(f"wrote {OUT}: {len(out)} departures from {len(repos)} repos")


if __name__ == "__main__":
    main()
