#!/usr/bin/env python3
"""1-Click deploy to GitHub Pages (repo: ms-visa-service-suratgarh, gh-pages branch).

Usage:
  export GITHUB_TOKEN=ghp_xxx
  python3 scripts/deploy_github.py
"""
import base64
import json
import mimetypes
import os
import sys
import urllib.request

REPO = "ms-visa-service-suratgarh"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"


def api(method, path, token, body=None, raw=False):
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        print(f"  ! GitHub API {e.code}: {e.read().decode(errors='replace')[:300]}")
        sys.exit(1)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN first: export GITHUB_TOKEN=ghp_xxx")
    user = api("GET", "/user", token)["login"]
    print(f"→ Authenticated as {user}")

    existing = api("GET", f"/repos/{user}/{REPO}", token) if False else None
    try:
        import contextlib
        with contextlib.suppress(SystemExit):
            pass
        req = urllib.request.Request(f"{API}/repos/{user}/{REPO}")
        req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req):
                print(f"→ Repo {REPO} exists")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"→ Creating repo {REPO}…")
                api("POST", "/user/repos", token, {"name": REPO, "private": False})
            else:
                raise
    finally:
        pass

    files = []
    for dirpath, _, names in os.walk(ROOT):
        for n in names:
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, ROOT)
            if rel.startswith(("scripts", ".git")) or n.startswith("."):
                continue
            files.append((full, rel.replace(os.sep, "/")))
    print(f"→ Publishing {len(files)} files to gh-pages…")

    ref = api("GET", f"/repos/{user}/{REPO}/git/ref/heads/gh-pages", token)
    commit = ref["object"]["sha"]
    base_tree = api("GET", f"/repos/{user}/{REPO}/git/commits/{commit}", token)["tree"]["sha"]

    tree_items = []
    for full, rel in files:
        with open(full, "rb") as f:
            blob = api("POST", f"/repos/{user}/{REPO}/git/blobs", token,
                       {"content": base64.b64encode(f.read()).decode(), "encoding": "base64"})
        tree_items.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"   · {rel}")

    tree = api("POST", f"/repos/{user}/{REPO}/git/trees", token,
               {"base_tree": base_tree, "tree": tree_items})
    new_commit = api("POST", f"/repos/{user}/{REPO}/git/commits", token,
                     {"message": "Deploy MS Visa Service portal",
                      "tree": tree["sha"], "parents": [commit]})
    api("PATCH", f"/repos/{user}/{REPO}/git/refs/heads/gh-pages", token,
        {"sha": new_commit["sha"]})

    pages = api("GET", f"/repos/{user}/{REPO}/pages", token)
    url = pages.get("html_url", f"https://{user}.github.io/{REPO}/")
    print(f"\n✅ Live at: {url}")


if __name__ == "__main__":
    main()
