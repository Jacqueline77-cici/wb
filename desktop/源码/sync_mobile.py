# -*- coding: utf-8 -*-
"""把电脑端的数据（配色/语录/节假日）同步到手机版 HTML"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from themes_data import THEMES
from quotes_data import QUOTES
from holidays_data import HOLIDAYS

M = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "手机版", "index.html")
s = io.open(M, encoding="utf-8").read()

# ---- 配色 ----
theme_js = ["const THEMES = {"]
for key, t in THEMES.items():
    theme_js.append(
        f"  {key}:{{name:'{t['label']}',dot:'{t['dot']}',bg:'{t['bg']}',card:'{t['card']}',"
        f"main:'{t['main']}',dark:'{t['dark']}',light:'{t['light']}',text:'{t['text']}',"
        f"muted:'{t['muted']}',border:'{t['border']}',soft:'{t['soft']}'}},")
theme_js.append("};")
theme_block = "\n".join(theme_js)

s2, n = re.subn(r"const THEMES = \{.*?\n\};", theme_block, s, flags=re.S)
print("themes replaced:", n)
s = s2

# ---- 语录 ----
q_js = ["const QUOTES = ["]
for text, src in QUOTES:
    q_js.append(f"  {{t:'{text}', s:'{src}'}},")
q_js.append("];")
q_block = "\n".join(q_js)
s2, n = re.subn(r"const QUOTES = \[.*?\n\];", q_block, s, flags=re.S)
print("quotes replaced:", n)
s = s2

# ---- 节假日 ----
h_js = ["const HOLIDAYS = {"]
for ds in sorted(HOLIDAYS):
    name, kind = HOLIDAYS[ds]
    h_js.append(f"  '{ds}':['{name}','{kind}'],")
h_js.append("};")
hol_block = "\n".join(h_js)
if "const HOLIDAYS" not in s:
    s = s.replace("/* ========== 页面状态 ========== */",
                  hol_block + "\n\n/* ========== 页面状态 ========== */")
    print("holidays inserted")
else:
    s2, n = re.subn(r"const HOLIDAYS = \{.*?\n\};", hol_block, s, flags=re.S)
    s = s2
    print("holidays replaced:", n)

io.open(M, "w", encoding="utf-8", newline="\n").write(s)
print("mobile synced, quotes:", len(QUOTES), "themes:", len(THEMES), "holidays:", len(HOLIDAYS))
