#!/usr/bin/env python3
"""
Fetch your public repos (most recently pushed first) into data/repos.json for
render_train_svg.py. Uses the public REST API -- no token required (60 req/h
is plenty for one call a day); if GITHUB_TOKEN is set it's used for a higher
limit. On any failure the previous data/repos.json is left untouched so the
daily workflow never breaks the train.

Run by .github/workflows/update-profile-art.yml.
"""
import json
import os
import sys

import requests

USERNAME = os.environ.get("GH_PROFILE_USER", "Alistair77")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "repos.json")
KEEP = ("name", "description", "language", "stargazers_count", "pushed_at", "html_url", "fork", "archived", "private")


def main():
    headers = {"User-Agent": "profile-readme-bot/1.0", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    url = f"https://api.github.com/users/{USERNAME}/repos"
    try:
        resp = requests.get(url, params={"per_page": 100, "sort": "pushed", "type": "owner"},
                            headers=headers, timeout=30)
        resp.raise_for_status()
        repos = resp.json()
    except Exception as e:  # keep yesterday's train rather than failing the run
        print(f"repo fetch failed ({e}); keeping existing {OUT}", file=sys.stderr)
        return
    slim = [{k: r.get(k) for k in KEEP} for r in repos]
    slim.sort(key=lambda r: r["pushed_at"] or "", reverse=True)
    with open(OUT, "w") as f:
        json.dump({"username": USERNAME, "repos": slim}, f, indent=2)
    print(f"wrote {OUT}: {len(slim)} repos")


if __name__ == "__main__":
    main()
