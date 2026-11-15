# -*- coding: utf-8 -*-
"""用本机令牌创建 GitHub 仓库、推送并开启 Pages（令牌不打印）"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

TOKEN_FILE = r"D:\cici\github_token.txt"
REPO_DIR = r"D:\cici\个人工作台\github发布"
ASKPASS = os.path.join(REPO_DIR, "_askpass.bat")
REPO_NAME = "wb"

with open(TOKEN_FILE, encoding="utf-8-sig") as f:
    TOKEN = f.read().strip()
print("token loaded, length:", len(TOKEN), "prefix:", TOKEN[:4] + "***")


def api(method, path, data=None):
    url = "https://api.github.com" + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "workbench-deploy")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:300]}


st, user = api("GET", "/user")
if st != 200:
    print("AUTH FAILED", st, user)
    raise SystemExit(1)
login = user["login"]
print("login:", login)

repo_path = f"/repos/{login}/{REPO_NAME}"
st, info = api("GET", repo_path)
if st == 200:
    print("repo already exists:", info.get("html_url"))
else:
    st, info = api("POST", "/user/repos", {
        "name": REPO_NAME, "private": False, "auto_init": False,
        "description": "Jacqueline 工作台 · 手机版（纯离线个人工作台）",
    })
    print("create repo:", st, info.get("html_url") or info)

env = dict(os.environ)
env["GIT_ASKPASS"] = ASKPASS
env["GIT_TERMINAL_PROMPT"] = "0"
env["GIT_USER"] = login

remote = f"https://github.com/{login}/{REPO_NAME}.git"
cmds = [
    ["git", "remote", "remove", "origin"],
    ["git", "remote", "add", "origin", remote],
    ["git", "push", "-u", "origin", "main"],
]
for c in cmds:
    p = subprocess.run(c, cwd=REPO_DIR, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (p.stdout or "").strip().splitlines()[-3:]
    err = (p.stderr or "").strip().splitlines()[-3:]
    print(">", " ".join(c), "->", p.returncode, "|", " / ".join(out + err))

st, pages = api("GET", repo_path + "/pages")
print("pages status:", st, pages.get("status") if isinstance(pages, dict) else "")
if st != 200:
    st2, pages2 = api("POST", repo_path + "/pages", {"source": {"branch": "main", "path": "/"}})
    print("enable pages:", st2, pages2.get("html_url") or pages2)

url = f"https://{login}.github.io/{REPO_NAME}/index.html"
for i in range(20):
    time.sleep(8)
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            body = r.read().decode("utf-8", "replace")
            print("site live:", r.status, len(body), "bytes")
            break
    except Exception as e:
        print("waiting...", i + 1, type(e).__name__, getattr(e, "code", ""))
else:
    print("site not live yet, try later:", url)

print("FINAL URL:", f"https://{login}.github.io/{REPO_NAME}/")
