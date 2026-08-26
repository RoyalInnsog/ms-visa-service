#!/usr/bin/env python3
"""1-Click deploy to Cloudflare Pages (direct upload).

Usage:
  export CF_API_TOKEN=xxx CF_ACCOUNT_ID=xxx
  python3 scripts/deploy_cloudflare.py [project-name]
"""
import hashlib
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.cloudflare.com/client/v4"


def call(method, path, token, body=None, ctype="application/json", raw=False):
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, data=data) as r:
        payload = r.read()
        return payload if raw else json.loads(payload)


def main():
    token = os.environ.get("CF_API_TOKEN")
    account = os.environ.get("CF_ACCOUNT_ID")
    if not token or not account:
        sys.exit("Set CF_API_TOKEN and CF_ACCOUNT_ID first.")
    project = sys.argv[1] if len(sys.argv) > 1 else "ms-visa-service-suratgarh"

    projects = call("GET", f"/accounts/{account}/pages/projects", token)
    if not any(p["name"] == project for p in projects["result"]):
        print(f"→ Creating Pages project '{project}'…")
        call("POST", f"/accounts/{account}/pages/projects", token, {
            "name": project,
            "production_branch": "main",
        })

    files = []
    for dirpath, _, names in os.walk(ROOT):
        for n in names:
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, ROOT)
            if rel.startswith(("scripts", ".git")) or n.startswith("."):
                continue
            files.append((os.path.relpath(full, ROOT).replace(os.sep, "/"), full))

    manifest = {}
    for rel, full in sorted(files):
        h = hashlib.md5(open(full, "rb").read()).hexdigest()
        manifest[rel] = h
        print(f"   · {rel}")

    print("→ Uploading manifest…")
    result = call("POST", f"/accounts/{account}/pages/projects/{project}/deployments", token,
                  {"manifest": json.dumps(manifest)})
    d = result["result"] if "result" in result else result
    jwt = ""
    for fd in d.get("fields", []) if isinstance(d.get("fields"), list) else []:
        jwt = fd.get("jwt") or jwt

    print("→ Uploading file contents…")
    for rel, full in sorted(files):
        h = hashlib.md5(open(full, "rb").read()).hexdigest()
        mime = "image/jpeg" if rel.endswith((".jpg", ".jpeg")) else (
               "text/plain" if rel.endswith(".txt") else (
               "text/html" if rel.endswith(".html") else "text/markdown"))
        call("POST", f"/accounts/{account}/pages/assets/upload", token,
             {"key": h, "value": open(full, "rb").read(),
              "metadata": {"contentType": mime}, "base64": True},
             ctype="application/json")

    print("\n✅ Deployed. Check your Cloudflare dashboard → Pages →", project)
    print("   URL will be https://" + project + ".pages.dev")


if __name__ == "__main__":
    main()
