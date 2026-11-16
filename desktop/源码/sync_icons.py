# -*- coding: utf-8 -*-
import io
import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE_DIR, "图标", "F_目标靶心_莫兰迪灰紫.png")
MOBILE = os.path.join(BASE_DIR, "手机版")
BASE = os.path.join(BASE_DIR, "图标")

im = Image.open(SRC).convert("RGBA")
for size, name in [(180, "icon-180-v3.png"), (192, "icon-192-v3.png"), (512, "icon-512-v3.png")]:
    im.resize((size, size), Image.LANCZOS).save(os.path.join(MOBILE, name), "PNG", optimize=True)
    print("wrote", name)

im2 = Image.open(SRC).convert("RGB")
im2.save(os.path.join(BASE, "app.ico"),
         sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("ico ok (F)")

p = os.path.join(MOBILE, "index.html")
s = io.open(p, encoding="utf-8").read()
s = s.replace('href="icon-180-v2.png"', 'href="icon-180-v3.png"')
s = s.replace('href="icon-192-v2.png"', 'href="icon-192-v3.png"')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)

p = os.path.join(MOBILE, "manifest.webmanifest")
s = io.open(p, encoding="utf-8").read()
s = s.replace("icon-180-v2.png", "icon-180-v3.png").replace("icon-192-v2.png", "icon-192-v3.png")
s = s.replace("icon-512-v2.png", "icon-512-v3.png")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)

p = os.path.join(MOBILE, "sw.js")
s = io.open(p, encoding="utf-8").read()
s = s.replace("wb-cache-v4", "wb-cache-v5")
s = s.replace("icon-180-v2.png", "icon-180-v3.png")
s = s.replace("icon-192-v2.png", "icon-192-v3.png")
s = s.replace("icon-512-v2.png", "icon-512-v3.png")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)

for old in ["icon-180-v2.png", "icon-192-v2.png", "icon-512-v2.png"]:
    f = os.path.join(MOBILE, old)
    if os.path.exists(f):
        os.remove(f)
print("done")
