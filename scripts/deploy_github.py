#!/usr/bin/env python3
"""1-Click Deployment to GitHub Pages for MS Visa Service."""

import os, sys, subprocess, pathlib, urllib.request, json

SITE_DIR = pathlib.Path(__file__).resolve().parents[1]
ROOT_ENV = SITE_DIR.parent / ".env"

def main():
    token = None
    user = None

    if ROOT_ENV.exists():
        with open(ROOT_ENV) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                elif line.startswith("GITHUB_USERNAME="):
                    user = line.split("=", 1)[1].strip()

    if not token or not user:
        print("❌ GITHUB_TOKEN or GITHUB_USERNAME not found in .env")
        return

    repo_name = "ms-visa-service"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "DeployScript",
        "Accept": "application/vnd.github.v3+json"
    }

    # Ensure repo exists
    create_url = "https://api.github.com/user/repos"
    create_data = json.dumps({"name": repo_name, "private": False, "auto_init": False}).encode()
    req = urllib.request.Request(create_url, data=create_data, headers=headers, method="POST")
    try:
        urllib.request.urlopen(req)
        print(f"✓ Created repository: {repo_name}")
    except Exception:
        pass

    # Push to gh-pages branch
    subprocess.run(["git", "init"], cwd=SITE_DIR, capture_output=True)
    subprocess.run(["git", "config", "user.name", user], cwd=SITE_DIR, capture_output=True)
    subprocess.run(["git", "config", "user.email", "deploy@example.com"], cwd=SITE_DIR, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=SITE_DIR, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Production release of MS Visa Service website"], cwd=SITE_DIR, capture_output=True)
    subprocess.run(["git", "branch", "-M", "gh-pages"], cwd=SITE_DIR, capture_output=True)

    remote_url = f"https://{user}:{token}@github.com/{user}/{repo_name}.git"
    subprocess.run(["git", "remote", "remove", "origin"], cwd=SITE_DIR, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=SITE_DIR, capture_output=True)
    subprocess.run(["git", "push", "-u", "origin", "gh-pages", "--force"], cwd=SITE_DIR, capture_output=True)

    live_url = f"https://{user.lower()}.github.io/{repo_name}/"
    print(f"\n🎉 Successfully Deployed to GitHub Pages! Live URL: {live_url}")

if __name__ == "__main__":
    main()
