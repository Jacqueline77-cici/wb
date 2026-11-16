#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, sys, calendar, csv, shutil, uuid
from datetime import datetime, timedelta

from themes_data import THEMES
from holidays_data import HOLIDAYS, holiday_text

C = {k: v for k, v in THEMES["morandi_blue"].items() if k not in ("label", "dot")}

APP_NAME = "Jacqueline"

MOTTO = "人生，易如反掌"

from quotes_data import QUOTES


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint(h, k):
    """k=0 接近白色，k=1 原色"""
    r, g, b = hex_rgb(h)
    f = lambda c: int(255 + (c - 255) * k)
    return "#%02x%02x%02x" % (f(r), f(g), f(b))


def apply_theme(store, key):
    t = THEMES.get(key) or THEMES["morandi_blue"]
    store.clear()
    store.update({k: v for k, v in t.items() if k not in ("label", "dot")})


def set_window_icon(root):
    paths = []
    if getattr(sys, "frozen", False):
        paths.append(os.path.join(getattr(sys, "_MEIPASS", BASE_DIR), "app.ico"))
    paths.append(os.path.join(BASE_DIR, "app.ico"))
    for p in paths:
        if os.path.exists(p):
            try:
                root.iconbitmap(p)
                return
            except Exception:
                pass

WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]

NAV_GROUPS = [
    ("日常", [("🏠", "首页", "home"), ("📅", "今日安排", "today"), ("✅", "待办事项", "todos"),
              ("⏰", "定时提醒", "reminders"), ("🗓️", "日历记录", "calendar")]),
    ("工作", [("📋", "项目清单", "projects"), ("💡", "素材库", "material"),
              ("📱", "自媒体", "publish")]),
    ("学习成长", [("📚", "学习清单", "study"), ("📖", "书单", "books"), ("🌱", "习惯打卡", "habits")]),
    ("健康", [("⚖️", "减肥记录", "weight"), ("💄", "医美清单", "beauty")]),
    ("规划", [("📆", "周计划", "weekplan"), ("🔁", "周期任务", "recurring"),
              ("⏳", "倒计时", "countdown"), ("🎯", "每月目标", "goal")]),
    ("其他", [("📝", "随笔备忘", "notes"), ("🔍", "全局搜索", "search"), ("⚙️", "设置", "settings")]),
]
NAV_FLAT = [it for _, items in NAV_GROUPS for it in items]

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE_DIR, "workbench_data.json")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")


def default_data():
    return {
        "settings": {
            "autostart": False,
            "evening_enabled": True,
            "evening_time": "21:30",
            "backup_keep": 30,
            "last_evening": "",
            "theme": "morandi_blue",
        },
        "schedule_blocks": [
            {"time": "06:30", "label": "起床", "note": ""},
            {"time": "07:50", "label": "送孩子上幼儿园", "note": ""},
            {"time": "09:00-12:00", "label": "工作（上午）", "note": ""},
            {"time": "12:00-14:00", "label": "午休 / 普拉提", "note": ""},
            {"time": "14:00-18:00", "label": "工作（下午）", "note": ""},
            {"time": "18:30", "label": "接孩子从幼儿园", "note": ""},
            {"time": "晚上", "label": "护肤 / 家庭时间", "note": ""},
            {"time": "23:00", "label": "睡前准备", "note": ""},
        ],
        "weekly_template": {str(i): [] for i in range(7)},
        "week_goals": {},
        "daily_three": {},
        "recurring_tasks": [],
        "countdowns": [
            {"name": "减肥目标 55kg", "date": "2027-01-31"},
        ],
        "weight_goal": {"current": 65, "target": 55, "date": "2027-01-31"},
        "weight_records": [],
        "diet_records": [],
        "water": {},
        "medical_beauty": [],
        "cpa_subjects": [
            {"name": n, "status": "未报名", "note": ""}
            for n in ["会计", "审计", "财务成本管理", "公司战略与风险管理", "经济法", "税法"]
        ],
        "study_log": [],
        "study_cats": ["CPA专业", "AI", "医学健康", "育儿", "玄学", "理财", "心理成长", "生活美学", "其他"],
        "study_items": [
            {"id": "cpa1", "name": "会计", "cat": "CPA专业", "status": "想学", "note": ""},
            {"id": "cpa2", "name": "审计", "cat": "CPA专业", "status": "想学", "note": ""},
            {"id": "cpa3", "name": "财务成本管理", "cat": "CPA专业", "status": "想学", "note": ""},
            {"id": "cpa4", "name": "公司战略与风险管理", "cat": "CPA专业", "status": "想学", "note": ""},
            {"id": "cpa5", "name": "经济法", "cat": "CPA专业", "status": "想学", "note": ""},
            {"id": "cpa6", "name": "税法", "cat": "CPA专业", "status": "想学", "note": ""},
        ],
        "books": [],
        "habits": ["普拉提", "早睡", "饮水", "学习", "写日记", "少糖少碳水"],
        "habit_done": {},
        "todos": [],
        "daily_logs": {},
        "moods": {},
        "materials": [],
        "publish": {},
        "projects": [],
        "weekly_review": {"good": "", "bad": "", "plan": ""},
        "monthly_goal": "",
        "notes": "",
        "reminders": [],
    }


def week_key(dt=None):
    dt = dt or datetime.now()
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


class App:
    def __init__(self, root):
        self.root = root
        root.title(f"{APP_NAME} 的工作台")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(1180, sw - 40), min(880, sh - 60)
        root.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 2)}")
        root.minsize(min(940, sw - 40), min(680, sh - 60))
        set_window_icon(root)
        now = datetime.now()
        self.cal_year, self.cal_month = now.year, now.month
        self.cal_selected = now.strftime("%Y-%m-%d")
        self.pomo_running = False
        self.pomo_left = 25 * 60
        self.current = "home"
        self.proj_filter = "全部"
        self.proj_open = set()
        self.proj_entries = {}
        self.load()
        apply_theme(C, self.data.get("settings", {}).get("theme", "morandi_blue"))
        root.configure(bg=C["bg"])
        root.option_add("*Entry.relief", "flat")
        root.option_add("*Entry.bd", 0)
        root.option_add("*Entry.highlightThickness", 1)
        root.option_add("*Entry.highlightBackground", C["border"])
        root.option_add("*Entry.highlightColor", C["main"])
        root.option_add("*Entry.background", "#FFFFFF")
        root.option_add("*Text.relief", "flat")
        root.option_add("*Text.bd", 0)
        root.option_add("*Text.highlightThickness", 1)
        root.option_add("*Text.highlightBackground", C["border"])
        root.option_add("*Text.highlightColor", C["main"])
        root.option_add("*Text.background", "#FFFFFF")
        self.auto_backup()
        self.build_nav()
        self.build_right()
        self.show("home")
        self.root.after(5000, self.check_reminders)

    # ---------- 数据 ----------
    def load(self):
        d0 = default_data()
        if os.path.exists(DATA):
            try:
                d = json.load(open(DATA, encoding="utf-8"))
                for k, v in d0.items():
                    if k not in d:
                        d[k] = v
                # 旧版 today_schedule(dict) -> schedule_blocks(list)
                if "today_schedule" in d and isinstance(d["today_schedule"], dict):
                    blocks = []
                    for k, v in d["today_schedule"].items():
                        parts = k.split(" ", 1)
                        if len(parts) == 2:
                            blocks.append({"time": parts[0], "label": parts[1], "note": v or ""})
                        else:
                            blocks.append({"time": "", "label": k, "note": v or ""})
                    if blocks:
                        d["schedule_blocks"] = blocks
                self.data = d
            except Exception:
                self.data = d0
        else:
            self.data = d0
        self.data.setdefault("settings", d0["settings"])
        for k, v in d0["settings"].items():
            self.data["settings"].setdefault(k, v)
        if self.data["settings"].get("theme") not in THEMES:
            self.data["settings"]["theme"] = "morandi_blue"

        def _clean(o):
            if isinstance(o, dict):
                for k in [k for k in list(o) if str(k).startswith("_")]:
                    o.pop(k, None)
                for v in o.values():
                    _clean(v)
            elif isinstance(o, list):
                for v in o:
                    _clean(v)

        _clean(self.data)
        try:
            self.save()
        except Exception:
            pass

    def save(self):
        try:
            txt = json.dumps(self.data, ensure_ascii=False, indent=2)
        except TypeError:
            def _clean(o):
                if isinstance(o, dict):
                    for k in list(o):
                        v = o[k]
                        if isinstance(v, (str, int, float, bool)) or v is None or isinstance(v, (dict, list)):
                            _clean(v)
                        else:
                            o.pop(k, None)
                elif isinstance(o, list):
                    for i in range(len(o) - 1, -1, -1):
                        v = o[i]
                        if isinstance(v, (str, int, float, bool)) or v is None or isinstance(v, (dict, list)):
                            _clean(v)
                        else:
                            o.pop(i)
            _clean(self.data)
            txt = json.dumps(self.data, ensure_ascii=False, indent=2)
        with open(DATA, "w", encoding="utf-8") as f:
            f.write(txt)

    def auto_backup(self):
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            target = os.path.join(BACKUP_DIR, f"workbench_{today_str()}.json")
            if not os.path.exists(target) and os.path.exists(DATA):
                shutil.copy2(DATA, target)
            keep = int(self.data.get("settings", {}).get("backup_keep", 30))
            files = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith(".json"))
            for f in files[:-keep] if len(files) > keep else []:
                os.remove(os.path.join(BACKUP_DIR, f))
        except Exception:
            pass

    # ---------- 界面骨架 ----------
    def build_nav(self):
        self.nav = tk.Frame(self.root, bg=C["card"], width=186)
        self.nav.pack(side="left", fill="y")
        self.nav.pack_propagate(False)
        head = tk.Frame(self.nav, bg=C["main"])
        head.pack(fill="x")
        tk.Label(head, text=APP_NAME, bg=C["main"], fg="white",
                 font=("Microsoft YaHei", 14, "bold")).pack(pady=(12, 0))
        tk.Label(head, text=MOTTO, bg=C["main"], fg=tint(C["main"], 0.25),
                 font=("Microsoft YaHei", 9)).pack(pady=(2, 12))

        # 底部固定区：配色按钮
        bottom = tk.Frame(self.nav, bg=C["soft"])
        bottom.pack(side="bottom", fill="x")
        tk.Frame(self.nav, bg=C["border"], height=1).pack(side="bottom", fill="x")
        self.pal_btn = tk.Button(bottom, text="🎨 配色", bg=C["card"], fg=C["muted"], bd=0,
                                 relief="flat", font=("Microsoft YaHei", 8),
                                 activebackground=C["light"], command=self.open_palette)
        self.pal_btn.pack(fill="x", padx=10, pady=8)

        # 可滚动的菜单区
        self.nav_can = tk.Canvas(self.nav, bg=C["card"], highlightthickness=0, width=184)
        self.nav_sb = ttk.Scrollbar(self.nav, orient="vertical", command=self.nav_can.yview)
        self.nav_can.configure(yscrollcommand=self.nav_sb.set)
        self.nav_sb.pack(side="right", fill="y")
        self.nav_can.pack(side="left", fill="both", expand=True)
        self.nav_inner = tk.Frame(self.nav_can, bg=C["card"])
        self.nav_win = self.nav_can.create_window((0, 0), window=self.nav_inner, anchor="nw")
        self.nav_inner.bind("<Configure>",
                            lambda e: self.nav_can.configure(scrollregion=self.nav_can.bbox("all")))
        self.nav_can.bind("<Configure>",
                          lambda e: self.nav_can.itemconfigure(self.nav_win, width=e.width))

        self.btns = {}
        for gname, items in NAV_GROUPS:
            tk.Label(self.nav_inner, text=gname, bg=C["soft"], fg=C["muted"],
                     font=("Microsoft YaHei", 8, "bold"), anchor="w", padx=12, pady=2).pack(fill="x")
            for icon, text, k in items:
                row = tk.Frame(self.nav_inner, bg=C["card"])
                row.pack(fill="x", padx=4)
                acc = tk.Frame(row, bg=C["card"], width=3)
                acc.pack(side="left", fill="y")
                ic = tk.Label(row, text=icon, bg=C["card"], width=3,
                              font=("Microsoft YaHei", 10), anchor="center")
                ic.pack(side="left")
                b = tk.Button(row, text=text, bg=C["card"], fg=C["text"], bd=0,
                              relief="flat", anchor="w", padx=2, pady=5,
                              activebackground=C["light"],
                              font=("Microsoft YaHei", 9),
                              command=lambda k=k: self.show(k))
                b.pack(side="left", fill="x", expand=True)
                self.btns[k] = (b, acc, ic)
        # 让滚轮在侧栏里滚菜单，不带动右侧内容
        for w in [self.nav_can, self.nav_inner] + self.nav_inner.winfo_children():
            w.bind("<MouseWheel>", self.nav_wheel)
        try:
            self.update_proj_badge()
        except Exception:
            pass

    def nav_wheel(self, e):
        try:
            self.nav_can.yview_scroll(int(-1 * (e.delta / 120)), "units")
        except Exception:
            pass
        return "break"

    def open_palette(self):
        win = tk.Toplevel(self.root)
        win.title("配色")
        win.configure(bg=C["card"])
        win.resizable(False, False)
        win.attributes("-topmost", True)
        tk.Label(win, text="选择配色", bg=C["card"], fg=C["dark"],
                 font=("Microsoft YaHei", 11, "bold")).pack(pady=(12, 8))
        cur = self.data.get("settings", {}).get("theme", "morandi_blue")
        for key, t in THEMES.items():
            row = tk.Frame(win, bg=C["card"])
            row.pack(fill="x", padx=16, pady=3)
            sw = tk.Frame(row, bg=t["dot"], width=34, height=20,
                          highlightthickness=2,
                          highlightbackground=C["dark"] if key == cur else t["dot"])
            sw.pack(side="left")
            sw.pack_propagate(False)
            tk.Button(row, text=t["label"] + ("　✓ 当前" if key == cur else ""),
                      bg=C["card"], fg=C["dark"] if key == cur else C["text"],
                      bd=0, relief="flat", anchor="w", font=("Microsoft YaHei", 9),
                      command=lambda k=key: (self.set_theme(k), win.destroy())).pack(
                side="left", fill="x", expand=True, padx=8)
        tk.Button(win, text="关闭", bg=C["light"], fg=C["dark"], bd=0,
                  command=win.destroy).pack(pady=10)

    def build_right(self):
        self.right = tk.Frame(self.root, bg=C["bg"])
        self.right.pack(side="right", fill="both", expand=True)
        self.title_bar = tk.Frame(self.right, bg=C["bg"], height=48)
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)
        self.lbl = tk.Label(self.title_bar, text="", bg=C["bg"],
                            fg=C["dark"], font=("Microsoft YaHei", 16, "bold"))
        self.lbl.pack(side="left", padx=20, pady=10)
        self.can = tk.Canvas(self.right, bg=C["bg"], highlightthickness=0)
        self.sc = tk.Scrollbar(self.right, orient="vertical", command=self.can.yview)
        self.con = tk.Frame(self.can, bg=C["bg"])
        self.con.bind("<Configure>", lambda e: self.can.configure(scrollregion=self.can.bbox("all")))
        self.win_id = self.can.create_window((0, 0), window=self.con, anchor="nw")
        self.can.configure(yscrollcommand=self.sc.set)
        self.can.pack(side="left", fill="both", expand=True)
        self.sc.pack(side="right", fill="y")
        self.can.bind("<Configure>", lambda e: self.can.itemconfigure(self.win_id, width=e.width))
        self.can.bind_all("<MouseWheel>",
                          lambda e: self.can.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def clear(self):
        for w in self.con.winfo_children():
            w.destroy()

    def title(self, t):
        self.lbl.config(text=t)

    def show(self, k):
        self.current = k
        self.clear()
        titles = {
            "home": "首页", "today": "今日安排", "calendar": "日历记录",
            "reminders": "定时提醒", "weekplan": "周计划", "recurring": "周期任务",
            "countdown": "倒计时", "goal": "每月目标", "projects": "项目清单",
            "weight": "减肥记录", "beauty": "医美清单", "habits": "习惯打卡",
            "study": "学习清单", "books": "书单",
            "material": "素材库",
            "publish": "自媒体", "todos": "待办事项", "notes": "随笔备忘",
            "search": "全局搜索", "settings": "设置",
        }
        self.title(titles[k])
        for kk, (b, acc, ic) in self.btns.items():
            on = (kk == k)
            b.config(bg=C["light"] if on else C["card"],
                     fg=C["dark"] if on else C["text"],
                     font=("Microsoft YaHei", 9, "bold") if on else ("Microsoft YaHei", 9))
            acc.config(bg=C["main"] if on else C["card"])
            ic.config(bg=C["light"] if on else C["card"])
        getattr(self, "p_" + k)()

    def set_theme(self, key):
        if key not in THEMES:
            return
        self.data.setdefault("settings", {})["theme"] = key
        self.save()
        apply_theme(C, key)
        try:
            self.root.configure(bg=C["bg"])
        except Exception:
            pass
        cur = self.current
        try:
            self.nav.destroy()
            self.right.destroy()
        except Exception:
            pass
        self.build_nav()
        self.build_right()
        self.show(cur)

    def card(self, t=None):
        f = tk.Frame(self.con, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        f.pack(fill="x", padx=18, pady=7)
        if t:
            tk.Label(f, text=t, bg=C["light"], fg=C["dark"], anchor="w",
                     font=("Microsoft YaHei", 11, "bold"), padx=14, pady=8).pack(fill="x")
            inner = tk.Frame(f, bg=C["card"], padx=14, pady=12)
            inner.pack(fill="x")
            return inner
        return f

    def rowe(self, parent, width=12, val=""):
        e = tk.Entry(parent, width=width)
        e.insert(0, val)
        e.pack(side="left", padx=4)
        return e

    def link(self, parent, text, cmd):
        b = tk.Button(parent, text=text, bg=C["light"], fg=C["dark"], bd=0,
                      padx=12, pady=6, font=("Microsoft YaHei", 9), command=cmd,
                      activebackground=tint(C["main"], 0.3), cursor="hand2")
        b.pack(side="left", padx=4)
        return b

    def primary(self, parent, text, cmd):
        b = tk.Button(parent, text=text, bg=C["main"], fg="white", bd=0,
                      padx=16, pady=6, font=("Microsoft YaHei", 9, "bold"), command=cmd,
                      activebackground=tint(C["main"], 0.78), cursor="hand2")
        b.pack(side="left", padx=4)
        return b

    def ghost(self, parent, text, cmd):
        b = tk.Button(parent, text=text, bg=C["card"], fg=C["muted"], bd=0,
                      padx=10, pady=5, font=("Microsoft YaHei", 9), command=cmd,
                      activebackground=C["light"], cursor="hand2")
        b.pack(side="left", padx=3)
        return b

    def date_pick(self, entry):
        """弹出小日历，点日期填进输入框"""
        win = tk.Toplevel(self.root)
        win.title("选择日期")
        win.configure(bg=C["card"])
        win.resizable(False, False)
        win.transient(self.root)
        state = {"y": datetime.now().year, "m": datetime.now().month}
        body = tk.Frame(win, bg=C["card"])
        body.pack(padx=8, pady=8)

        def move(d):
            y, m = state["y"], state["m"] + d
            if m < 1:
                y, m = y - 1, 12
            elif m > 12:
                y, m = y + 1, 1
            state["y"], state["m"] = y, m
            draw()

        def draw():
            for w in body.winfo_children():
                w.destroy()
            head = tk.Frame(body, bg=C["card"])
            head.pack(fill="x", pady=(0, 4))
            tk.Button(head, text="◀", bg=C["card"], fg=C["muted"], bd=0,
                      font=("Microsoft YaHei", 10), command=lambda: move(-1)).pack(side="left")
            tk.Label(head, text=f"{state['y']}年{state['m']}月", bg=C["card"], fg=C["dark"],
                     font=("Microsoft YaHei", 11, "bold")).pack(side="left", expand=True)
            tk.Button(head, text="▶", bg=C["card"], fg=C["muted"], bd=0,
                      font=("Microsoft YaHei", 10), command=lambda: move(1)).pack(side="right")
            grid = tk.Frame(body, bg=C["card"])
            grid.pack()
            for i, h in enumerate(WEEKDAYS):
                tk.Label(grid, text=h, bg=C["light"], fg=C["dark"], width=4).grid(row=0, column=i)
            weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(state["y"], state["m"])
            for r, wk in enumerate(weeks, start=1):
                for c, d in enumerate(wk):
                    if d == 0:
                        tk.Label(grid, text="", bg=C["card"], width=4).grid(row=r, column=c)
                        continue
                    ds = f"{state['y']:04d}-{state['m']:02d}-{d:02d}"
                    b = tk.Button(grid, text=str(d), bg=C["card"], fg=C["text"], bd=0, width=4,
                                  font=("Microsoft YaHei", 9),
                                  command=lambda ds=ds: self.pick_date(entry, ds, win))
                    b.grid(row=r, column=c, pady=1)

        draw()

    def pick_date(self, entry, ds, win):
        try:
            entry.delete(0, "end")
            entry.insert(0, ds)
        except Exception:
            pass
        win.destroy()

    def date_row(self, parent, entry):
        """日期输入框右边的日历按钮"""
        tk.Button(parent, text="📅", bg=C["card"], fg=C["muted"], bd=0,
                  font=("Microsoft YaHei", 10), cursor="hand2",
                  command=lambda: self.date_pick(entry)).pack(side="left", padx=(4, 0))

    # ---------- 首页 ----------
    def p_home(self):
        now = datetime.now()
        hh = now.hour
        greet = ("早上好" if 5 <= hh < 11 else
                 "中午好" if 11 <= hh < 14 else
                 "下午好" if 14 <= hh < 18 else "晚上好")

        # 顶部渐变横幅
        hero_hint = "今天也要好好照顾自己 🌸"
        hol = HOLIDAYS.get(today_str())
        if hol:
            hero_hint = ("今天放假，好好休息 🎉" if hol[1] == "off"
                         else f"今天调休上班，辛苦了（{hol[0]}）")
        hero = tk.Canvas(self.con, height=124, bg=C["bg"], highlightthickness=0,
                         cursor="hand2")
        hero.pack(fill="x", padx=20, pady=(12, 6))
        hero.bind("<Button-1>", lambda e: self.show("calendar"))

        def draw_hero(event=None):
            try:
                if not hero.winfo_exists():
                    return
            except Exception:
                return
            w = event.width if event else hero.winfo_width()
            h = event.height if event else 124
            if w < 10:
                return
            hero.delete("all")
            r1, g1, b1 = hex_rgb(C["hero1"])
            r2, g2, b2 = hex_rgb(C["hero2"])
            steps = 80
            for i in range(steps):
                k = i / (steps - 1)
                col = "#%02x%02x%02x" % (int(r1 + (r2 - r1) * k),
                                         int(g1 + (g2 - g1) * k),
                                         int(b1 + (b2 - b1) * k))
                x0 = int(w * i / steps)
                x1 = int(w * (i + 1) / steps) + 1
                hero.create_rectangle(x0, 0, x1, h, fill=col, outline=col)
            hero.create_text(28, 32, anchor="w", fill=C["muted"],
                             font=("Microsoft YaHei", 10),
                             text=f"{now.year}年{now.month}月{now.day}日  星期{WEEKDAYS[now.weekday()]}")
            hero.create_text(28, 68, text=f"{greet}，{APP_NAME}", anchor="w", fill=C["dark"],
                             font=("Microsoft YaHei", 20, "bold"))
            hero.create_text(30, 98, anchor="w", fill=C["muted"], font=("Microsoft YaHei", 10),
                             text=hero_hint)

        hero.bind("<Configure>", draw_hero)

        # 数据概览
        habits = self.data.get("habits", [])
        done_h = self.data.get("habit_done", {}).get(today_str(), [])
        water = self.data.get("water", {}).get(today_str(), 0)
        todos = self.data.get("todos", [])
        left = len([t for t in todos if not t.get("done")])
        try:
            latest = float(self.data["weight_records"][-1]["weight"]) if self.data["weight_records"] \
                else float(self.data["weight_goal"]["current"])
            wtxt = f"{latest:g}"
        except Exception:
            wtxt = "--"
        strip = tk.Frame(self.con, bg=C["bg"])
        strip.pack(fill="x", padx=20, pady=(2, 4))
        chips = [
            ("今日打卡", f"{len(done_h)}/{len(habits)}", C["main"]),
            ("饮水", f"{water}/8", tint(C["main"], 0.62)),
            ("待完成", f"{left}", C["dark"]),
            ("体重", f"{wtxt} kg", C["muted"]),
        ]
        for i, (name, val, color) in enumerate(chips):
            f = tk.Frame(strip, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            f.pack(side="left", expand=True, fill="x", padx=(0 if i == 0 else 8, 0), ipady=3)
            tk.Label(f, text=val, bg=C["card"], fg=color,
                     font=("Microsoft YaHei", 15, "bold")).pack(pady=(6, 0))
            tk.Label(f, text=name, bg=C["card"], fg=C["muted"],
                     font=("Microsoft YaHei", 8)).pack(pady=(0, 6))

        # 快捷入口
        quick = self.card("🚀 快捷入口")
        grid = tk.Frame(quick, bg=C["card"])
        grid.pack(fill="x")
        for i, (icon, label, key) in enumerate(NAV_FLAT):
            grid.columnconfigure(i % 5, weight=1, uniform="q")
            cell = tk.Frame(grid, bg=C["soft"], highlightbackground=C["border"],
                            highlightthickness=1, height=64)
            cell.grid(row=i // 5, column=i % 5, sticky="nsew", padx=4, pady=4)
            cell.grid_propagate(False)
            tk.Button(cell, text=icon, bg=C["soft"], bd=0, relief="flat",
                      font=("Microsoft YaHei", 15), activebackground=C["light"],
                      cursor="hand2", command=lambda k=key: self.show(k)).pack(pady=(7, 0))
            tk.Label(cell, text=label, bg=C["soft"], fg=C["text"],
                     font=("Microsoft YaHei", 8)).pack()

        # 今日一句
        inner0 = self.card("📖 今日一句")
        qi, q = self.quote_today()
        qrow = tk.Frame(inner0, bg=C["card"])
        qrow.pack(fill="x")
        tk.Label(qrow, text=q[0], bg=C["card"], fg=C["text"], anchor="w",
                 justify="left", wraplength=780,
                 font=("Microsoft YaHei", 11)).pack(side="left", fill="x", expand=True)
        tk.Label(qrow, text=(f"—— {q[1]}" if q[1] else ""), bg=C["card"], fg=C["muted"], anchor="e",
                 font=("Microsoft YaHei", 8)).pack(side="right", padx=(10, 0))
        qbar = tk.Frame(inner0, bg=C["card"]); qbar.pack(fill="x", pady=(6, 0))
        self.link(qbar, "换一句", self.next_quote)

        # 今日三件事
        inner = self.card("🎯 今日三件事")
        d3 = self.data.get("daily_three", {}).get(today_str(), ["", "", ""])
        if len(d3) < 3:
            d3 = (d3 + ["", "", ""])[:3]
        self.home_three = []
        for i in range(3):
            row = tk.Frame(inner, bg=C["card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=str(i + 1), bg=C["main"], fg="white", width=2,
                     font=("Microsoft YaHei", 9, "bold")).pack(side="left", padx=(0, 8), ipady=2)
            e = tk.Entry(row)
            e.insert(0, d3[i])
            e.pack(side="left", fill="x", expand=True, ipady=4)
            self.home_three.append(e)
        bar = tk.Frame(inner, bg=C["card"]); bar.pack(fill="x", pady=(6, 0))
        self.primary(bar, "保存", self.save_home_three)
        tk.Label(bar, text="写完点保存，首页会一直显示", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 8)).pack(side="left", padx=8)

        # 待办（快速）
        inner2 = self.card("✅ 待办事项")
        addrow = tk.Frame(inner2, bg=C["card"]); addrow.pack(fill="x", pady=(0, 4))
        self.home_todo_entry = tk.Entry(addrow)
        self.home_todo_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.home_todo_entry.bind("<Return>", lambda e: self.home_add_todo())
        self.primary(addrow, "添加", self.home_add_todo)
        self.link(addrow, "全部 →", lambda: self.show("todos"))
        undone = [(i, t) for i, t in enumerate(todos) if not t.get("done")]
        if undone:
            for i, t in undone[:5]:
                row = tk.Frame(inner2, bg=C["card"])
                row.pack(fill="x", pady=1)
                var = tk.BooleanVar(value=False)
                tk.Checkbutton(row, variable=var, bg=C["card"], activebackground=C["card"],
                               command=lambda i=i: self.home_done_todo(i)).pack(side="left")
                tk.Label(row, text=f'· {t.get("text", "")}', bg=C["card"], fg=C["text"],
                         anchor="w", font=("Microsoft YaHei", 10)).pack(side="left", fill="x", expand=True)
            if len(undone) > 5:
                tk.Label(inner2, text=f"还有 {len(undone) - 5} 项，点“全部”查看",
                         bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(2, 0))
        else:
            tk.Label(inner2, text="没有待办了，今天很轻松 🌿", bg=C["card"], fg=C["muted"],
                     font=("Microsoft YaHei", 9)).pack(anchor="w", pady=2)

        # 今日提醒 + 倒计时
        inner3 = self.card("⏰ 今日提醒")
        actives = self.today_reminders()
        if actives:
            for r in actives:
                row = tk.Frame(inner3, bg=C["card"]); row.pack(fill="x", pady=2)
                tk.Label(row, text=r.get("time", ""), bg=C["light"], fg=C["dark"],
                         font=("Microsoft YaHei", 10, "bold"), width=7).pack(side="left", padx=(0, 8), ipady=2)
                tk.Label(row, text=r.get("text", ""), bg=C["card"], fg=C["text"],
                         anchor="w", font=("Microsoft YaHei", 10)).pack(side="left", fill="x", expand=True)
                tk.Label(row, text=str(r.get("repeat", "每天")).replace("每周", "周"),
                         bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(side="right")
        else:
            tk.Label(inner3, text="今天没有定时提醒。", bg=C["card"], fg=C["muted"],
                     font=("Microsoft YaHei", 9)).pack(anchor="w")

        inner4 = self.card("⏳ 倒计时")
        cds = self.data.get("countdowns", [])
        if cds:
            row = tk.Frame(inner4, bg=C["card"]); row.pack(fill="x")
            for c in cds[:4]:
                try:
                    days = (datetime.strptime(c["date"], "%Y-%m-%d").date() - now.date()).days
                    bignum = str(days) if days >= 0 else f"{-days}"
                    cap = "天" if days >= 0 else "天前"
                except Exception:
                    bignum, cap = "--", ""
                box = tk.Frame(row, bg=C["light"], highlightbackground=C["border"], highlightthickness=1)
                box.pack(side="left", padx=(0, 8))
                tk.Label(box, text=bignum, bg=C["light"], fg=C["main"],
                         font=("Microsoft YaHei", 16, "bold")).pack(padx=14, pady=(4, 0))
                tk.Label(box, text=f'{c.get("name", "")} · {cap}', bg=C["light"], fg=C["muted"],
                         font=("Microsoft YaHei", 8)).pack(padx=14, pady=(0, 6))
        else:
            tk.Label(inner4, text="还没有倒计时，去“倒计时”页添加。", bg=C["card"],
                     fg=C["muted"], font=("Microsoft YaHei", 9)).pack(anchor="w")

        self.root.after(30, draw_hero)

    def quote_today(self):
        n = len(QUOTES)
        doy = datetime.now().timetuple().tm_yday
        st = self.data.get("daily_quote", {})
        if st.get("date") == today_str():
            i = int(st.get("i", doy % n)) % n
        else:
            i = doy % n
        return i, QUOTES[i]

    def next_quote(self):
        i, _ = self.quote_today()
        st = self.data.setdefault("daily_quote", {})
        st["date"] = today_str()
        st["i"] = (i + 1) % len(QUOTES)
        self.save()
        self.show("home")

    def home_add_todo(self):
        t = self.home_todo_entry.get().strip()
        if not t:
            return
        self.data.setdefault("todos", []).append({"text": t, "done": False})
        self.save()
        self.show("home")

    def home_done_todo(self, i):
        try:
            self.data["todos"][i]["done"] = True
        except Exception:
            return
        self.save()
        self.show("home")

    def save_home_three(self):
        self.data.setdefault("daily_three", {})[today_str()] = [e.get() for e in self.home_three]
        self.save()
        messagebox.showinfo("提示", "今日三件事已保存")

    # ---------- 今日安排 ----------
    def p_today(self):
        inner = self.card("今日时间安排（可编辑）")
        tk.Label(inner, text="时间、事项、备注都可以直接改；删除不需要的时段，点“保存”后生效。",
                 bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(0, 6))
        self.block_entries = []
        for i, blk in enumerate(self.data.get("schedule_blocks", [])):
            row = tk.Frame(inner, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=3)
            te = tk.Entry(row, width=13); te.insert(0, blk.get("time", "")); te.pack(side="left", padx=4)
            le = tk.Entry(row, width=22); le.insert(0, blk.get("label", "")); le.pack(side="left", padx=4)
            ne = tk.Entry(row, width=40); ne.insert(0, blk.get("note", "")); ne.pack(side="left", padx=4, fill="x", expand=True)
            self.block_entries.append((te, le, ne))
        bar = tk.Frame(inner, bg=C["card"]); bar.pack(fill="x", pady=6)
        self.primary(bar, "＋ 添加时段", self.add_block)
        self.primary(bar, "保存今日安排", self.save_blocks)

        inner2 = self.card("🎯 今日三件事")
        d3 = self.data.get("daily_three", {}).get(today_str(), ["", "", ""])
        if len(d3) < 3:
            d3 = (d3 + ["", "", ""])[:3]
        self.today_three = []
        for i in range(3):
            row = tk.Frame(inner2, bg=C["card"]); row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{i+1}.", bg=C["card"], fg=C["dark"], width=3).pack(side="left")
            e = tk.Entry(row, width=70); e.insert(0, d3[i]); e.pack(side="left", fill="x", expand=True, padx=4)
            self.today_three.append(e)
        self.primary(inner2, "保存三件事", self.save_today_three)

        inner3 = self.card("📆 今日周计划任务")
        tasks = self.data.get("weekly_template", {}).get(str(datetime.now().weekday()), [])
        if tasks:
            for t in tasks:
                tk.Label(inner3, text=f'· {t}', bg=C["card"], fg=C["text"], anchor="w").pack(fill="x", pady=1)
        else:
            tk.Label(inner3, text="今天还没有周计划任务，去“周计划”页添加。",
                     bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x")

    def add_block(self):
        self.data.setdefault("schedule_blocks", []).append({"time": "", "label": "", "note": ""})
        self.save()
        self.show("today")

    def save_blocks(self):
        blocks = []
        for te, le, ne in self.block_entries:
            if te.get().strip() or le.get().strip():
                blocks.append({"time": te.get().strip(), "label": le.get().strip(), "note": ne.get().strip()})
        self.data["schedule_blocks"] = blocks
        self.save()
        messagebox.showinfo("提示", "今日安排已保存")

    def save_today_three(self):
        self.data.setdefault("daily_three", {})[today_str()] = [e.get() for e in self.today_three]
        self.save()
        messagebox.showinfo("提示", "今日三件事已保存")

    # ---------- 日历记录 ----------
    def p_calendar(self):
        inner = self.card("日历记录")
        top = tk.Frame(inner, bg=C["card"]); top.pack(fill="x", pady=3)
        self.link(top, "◀ 上月", lambda: self.cal_move(-1))
        self.cal_title = tk.Label(top, text="", bg=C["card"], fg=C["dark"],
                                  font=("Microsoft YaHei", 13, "bold"))
        self.cal_title.pack(side="left", expand=True)
        self.link(top, "今天", self.cal_today)
        self.link(top, "下月 ▶", lambda: self.cal_move(1))
        self.cal_grid = tk.Frame(inner, bg=C["card"]); self.cal_grid.pack(fill="x", pady=6)
        self.render_calendar()

        inner2 = self.card("当日记录")
        self.cal_day_lbl = tk.Label(inner2, text="", bg=C["card"], fg=C["dark"],
                                    font=("Microsoft YaHei", 10, "bold"), anchor="w")
        self.cal_day_lbl.pack(fill="x", pady=(0, 4))
        mood_row = tk.Frame(inner2, bg=C["card"]); mood_row.pack(fill="x", pady=3)
        tk.Label(mood_row, text="心情：", bg=C["card"]).pack(side="left")
        self.mood_btns = []
        self.mood_sel = 0
        for s in range(1, 6):
            b = tk.Button(mood_row, text=str(s), width=3, bd=0, bg=C["light"], fg=C["dark"],
                          command=lambda s=s: self.set_mood(s))
            b.pack(side="left", padx=2)
            self.mood_btns.append(b)
        self.mood_note = tk.Entry(mood_row, width=36)
        self.mood_note.pack(side="left", padx=8)
        tk.Label(mood_row, text="（1-5分，可写一句）", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 8)).pack(side="left")

        self.cal_text = tk.Text(inner2, height=7)
        self.cal_text.pack(fill="x", pady=5)
        bar = tk.Frame(inner2, bg=C["card"]); bar.pack(fill="x")
        self.primary(bar, "保存当天", self.save_daily_log)
        self.link(bar, "清空当天", self.clear_daily_log)
        self.load_day_editor()

    def render_calendar(self):
        for w in self.cal_grid.winfo_children():
            w.destroy()
        y, m = self.cal_year, self.cal_month
        self.cal_title.config(text=f"{y}年{m}月")
        for i, h in enumerate(WEEKDAYS):
            tk.Label(self.cal_grid, text=h, bg=C["light"], fg=C["dark"],
                     width=6, pady=3).grid(row=0, column=i, padx=1, pady=1)
        weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(y, m)
        logs = self.data.get("daily_logs", {})
        moods = self.data.get("moods", {})
        today = today_str()
        for r, week in enumerate(weeks, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(self.cal_grid, text="", bg=C["card"], width=6, height=2).grid(
                        row=r, column=c, padx=1, pady=1)
                    continue
                ds = f"{y:04d}-{m:02d}-{day:02d}"
                has = bool(str(logs.get(ds, "")).strip())
                sc = int(moods.get(ds, {}).get("score", 0) or 0)
                sel = (ds == self.cal_selected)
                hol = HOLIDAYS.get(ds)
                if sel:
                    bg, fg = C["main"], "white"
                elif hol and hol[1] == "off":
                    bg, fg = C["hol"], C["dark"]
                elif hol and hol[1] == "work":
                    bg, fg = C["work"], "white"
                elif sc >= 4:
                    bg, fg = tint(C["main"], 0.62), "white"
                elif sc in (2, 3):
                    bg, fg = C["light"], C["dark"]
                elif sc == 1:
                    bg, fg = tint(C["main"], 0.22), C["muted"]
                else:
                    bg, fg = C["card"], C["text"]
                # 日期和标记分两格，保证每个格子对齐
                cell = tk.Frame(self.cal_grid, bg=bg, width=64, height=42)
                cell.grid(row=r, column=c, padx=1, pady=1)
                cell.pack_propagate(False)
                num = tk.Label(cell, text=str(day), bg=bg, fg=fg, width=3,
                               font=("Microsoft YaHei", 11, "bold" if sel else "normal"))
                num.pack(side="left", padx=(4, 0))
                mark = ""
                if hol:
                    mark = "休" if hol[1] == "off" else "班"
                elif has:
                    mark = "●"
                if ds == today:
                    mark = "今"
                tk.Label(cell, text=mark, bg=bg, fg=fg, width=2,
                         font=("Microsoft YaHei", 8)).pack(side="left")
                for w in cell.winfo_children():
                    w.bind("<Button-1>", lambda e, ds=ds: self.cal_pick(ds))
                cell.bind("<Button-1>", lambda e, ds=ds: self.cal_pick(ds))
        legend = tk.Frame(self.cal_grid, bg=C["card"])
        legend.grid(row=len(weeks) + 1, column=0, columnspan=7, sticky="w", pady=(8, 0))
        tk.Label(legend, text="休=法定假日　班=调休上班　●=有记录　今=今天", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 8)).pack(side="left")

    def cal_move(self, delta):
        y, m = self.cal_year, self.cal_month + delta
        if m < 1:
            y, m = y - 1, 12
        elif m > 12:
            y, m = y + 1, 1
        self.cal_year, self.cal_month = y, m
        self.render_calendar()

    def cal_today(self):
        now = datetime.now()
        self.cal_year, self.cal_month = now.year, now.month
        self.cal_selected = today_str()
        self.render_calendar()
        self.load_day_editor()

    def cal_pick(self, ds):
        self.cal_selected = ds
        self.render_calendar()
        self.load_day_editor()

    def load_day_editor(self):
        ds = self.cal_selected
        ht = holiday_text(ds)
        self.cal_day_lbl.config(text=f"{ds} 的记录" + (f"　·　{ht}" if ht else ""))
        self.cal_text.delete("1.0", tk.END)
        self.cal_text.insert("1.0", self.data.get("daily_logs", {}).get(ds, ""))
        mood = self.data.get("moods", {}).get(ds, {})
        self.mood_sel = int(mood.get("score", 0) or 0)
        self.mood_note.delete(0, tk.END)
        self.mood_note.insert(0, mood.get("note", ""))
        for i, b in enumerate(self.mood_btns):
            b.config(bg=C["main"] if (i + 1) == self.mood_sel else C["light"],
                     fg="white" if (i + 1) == self.mood_sel else C["dark"])

    def set_mood(self, s):
        self.mood_sel = 0 if self.mood_sel == s else s
        for i, b in enumerate(self.mood_btns):
            b.config(bg=C["main"] if (i + 1) == self.mood_sel else C["light"],
                     fg="white" if (i + 1) == self.mood_sel else C["dark"])

    def save_daily_log(self):
        ds = self.cal_selected
        txt = self.cal_text.get("1.0", "end-1c")
        if txt.strip():
            self.data.setdefault("daily_logs", {})[ds] = txt
        else:
            self.data.setdefault("daily_logs", {}).pop(ds, None)
        note = self.mood_note.get().strip()
        if self.mood_sel or note:
            self.data.setdefault("moods", {})[ds] = {"score": self.mood_sel, "note": note}
        else:
            self.data.setdefault("moods", {}).pop(ds, None)
        self.save()
        self.render_calendar()
        messagebox.showinfo("提示", f"{ds} 已保存")

    def clear_daily_log(self):
        ds = self.cal_selected
        if not messagebox.askyesno("确认", f"清空 {ds} 的记录和心情？"):
            return
        self.data.setdefault("daily_logs", {}).pop(ds, None)
        self.data.setdefault("moods", {}).pop(ds, None)
        self.save()
        self.cal_text.delete("1.0", tk.END)
        self.mood_note.delete(0, tk.END)
        self.mood_sel = 0
        for b in self.mood_btns:
            b.config(bg=C["light"], fg=C["dark"])
        self.render_calendar()

    # ---------- 定时提醒 ----------
    def today_reminders(self):
        now = datetime.now()
        today = today_str()
        wd = WEEKDAYS[now.weekday()]
        out = []
        for r in self.data.get("reminders", []):
            if not r.get("enabled", True):
                continue
            rep = r.get("repeat", "每天")
            if rep == "每天" or (rep == "仅一次" and r.get("date") == today) or rep == f"每周{wd}":
                out.append(r)
        return sorted(out, key=lambda x: x.get("time", ""))

    def p_reminders(self):
        inner = self.card("新增提醒")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=4)
        tk.Label(r, text="内容:", bg=C["card"]).pack(side="left")
        self.rm_text = tk.Entry(r, width=15); self.rm_text.pack(side="left", padx=4)
        tk.Label(r, text="时间:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.rm_time = tk.Entry(r, width=6); self.rm_time.insert(0, "09:00"); self.rm_time.pack(side="left", padx=4)
        tk.Label(r, text="提前:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.rm_adv = ttk.Combobox(r, values=["准点", "提前5分钟", "提前10分钟", "提前15分钟"],
                                   width=10, state="readonly"); self.rm_adv.set("准点"); self.rm_adv.pack(side="left", padx=4)
        tk.Label(r, text="重复:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.rm_rep = ttk.Combobox(r, values=["每天", "仅一次"] + [f"每周{w}" for w in WEEKDAYS],
                                   width=7, state="readonly"); self.rm_rep.set("每天"); self.rm_rep.pack(side="left", padx=4)
        tk.Label(r, text="日期:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.rm_date = tk.Entry(r, width=10); self.rm_date.insert(0, today_str()); self.rm_date.pack(side="left", padx=4)
        self.date_row(r, self.rm_date)
        self.primary(r, "添加", self.add_reminder)

        inner2 = self.card("提醒列表")
        self.rm_list = tk.Frame(inner2, bg=C["card"]); self.rm_list.pack(fill="x", pady=4)
        tk.Label(inner2, text="程序需保持运行才会提醒；可在“设置”里开启开机自启。",
                 bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(4, 0))
        bar2 = tk.Frame(inner2, bg=C["card"]); bar2.pack(fill="x", pady=(4, 0))
        self.link(bar2, "📱 导出到 iPhone 日历", self.export_ics)
        tk.Label(bar2, text="导出后发到手机，点开「添加到日历」，到点由系统提醒（不用开电脑）",
                 bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(side="left", padx=6)
        self.refresh_reminders()

    def add_reminder(self):
        text = self.rm_text.get().strip()
        t = self.rm_time.get().strip()
        if not text:
            messagebox.showwarning("提示", "请填写提醒内容")
            return
        try:
            datetime.strptime(t, "%H:%M")
        except Exception:
            messagebox.showwarning("提示", "时间格式应为 HH:MM，例如 12:30")
            return
        rep = self.rm_rep.get()
        date = self.rm_date.get().strip()
        if rep == "仅一次":
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except Exception:
                messagebox.showwarning("提示", "仅一次提醒请填写日期 YYYY-MM-DD")
                return
        adv = {"准点": 0, "提前5分钟": 5, "提前10分钟": 10, "提前15分钟": 15}.get(self.rm_adv.get(), 0)
        self.data.setdefault("reminders", []).append({
            "text": text, "time": t, "advance": adv, "repeat": rep, "date": date,
            "enabled": True, "fired_for": "", "snooze_until": "",
        })
        self.save()
        self.rm_text.delete(0, tk.END)
        self.refresh_reminders()

    def refresh_reminders(self):
        for w in self.rm_list.winfo_children():
            w.destroy()
        rs = self.data.get("reminders", [])
        if not rs:
            tk.Label(self.rm_list, text="还没有提醒。", bg=C["card"], fg=C["muted"], anchor="w").pack(fill="x", pady=4)
            return
        for idx, r in enumerate(sorted(rs, key=lambda x: x.get("time", ""))):
            i = rs.index(r)
            row = tk.Frame(self.rm_list, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            var = tk.BooleanVar(value=r.get("enabled", True))
            tk.Checkbutton(row, variable=var, bg=C["card"],
                           command=lambda i=i, v=var: self.toggle_reminder(i, v)).pack(side="left", padx=5)
            tk.Label(row, text=r.get("time", ""), bg=C["card"], width=6, fg=C["dark"],
                     font=("Microsoft YaHei", 10, "bold")).pack(side="left")
            adv = r.get("advance", 0)
            if adv:
                tk.Label(row, text=f"提前{adv}分", bg=C["card"], fg=C["muted"], width=8).pack(side="left")
            tk.Label(row, text=r.get("text", ""), bg=C["card"], anchor="w").pack(
                side="left", fill="x", expand=True, padx=5)
            rep = r.get("repeat", "每天")
            if rep == "仅一次":
                rep = f'仅一次 {r.get("date","")}'
            tk.Label(row, text=rep, bg=C["card"], fg=C["muted"], width=15).pack(side="left")
            tk.Button(row, text="删除", bg=C["border"], bd=0,
                      command=lambda i=i: self.del_reminder(i)).pack(side="right", padx=5)

    def toggle_reminder(self, i, var):
        self.data["reminders"][i]["enabled"] = var.get()
        self.save()

    def del_reminder(self, i):
        if messagebox.askyesno("确认", "删除这条提醒？"):
            self.data["reminders"].pop(i)
            self.save()
            self.refresh_reminders()

    def check_reminders(self):
        fired = []
        try:
            now = datetime.now()
            hhmm = now.strftime("%H:%M")
            today = today_str()
            wd = WEEKDAYS[now.weekday()]
            for r in self.data.get("reminders", []):
                if not r.get("enabled", True):
                    continue
                # 贪睡
                if r.get("snooze_until") == f"{today} {hhmm}":
                    r["snooze_until"] = ""
                    fired.append(r)
                    continue
                rep = r.get("repeat", "每天")
                if not (rep == "每天" or (rep == "仅一次" and r.get("date") == today) or rep == f"每周{wd}"):
                    continue
                try:
                    t = datetime.strptime(r.get("time", "00:00"), "%H:%M")
                    target = (t - timedelta(minutes=int(r.get("advance", 0)))).strftime("%H:%M")
                except Exception:
                    continue
                if hhmm == target and r.get("fired_for") != f'{today} {r.get("time")}':
                    r["fired_for"] = f'{today} {r.get("time")}'
                    fired.append(r)
            # 晚间收尾
            st = self.data.get("settings", {})
            if st.get("evening_enabled", True) and hhmm == st.get("evening_time", "21:30") \
                    and st.get("last_evening") != today:
                st["last_evening"] = today
                self.show_evening_check()
            if fired:
                self.save()
                self.fire_alert(fired)
        except Exception:
            pass
        finally:
            self.root.after(30000, self.check_reminders)

    def fire_alert(self, items):
        try:
            self.root.bell()
        except Exception:
            pass
        win = tk.Toplevel(self.root)
        win.title("⏰ 定时提醒")
        win.configure(bg=C["card"])
        win.geometry("420x300")
        win.attributes("-topmost", True)
        tk.Label(win, text="⏰ 到时间啦", bg=C["card"], fg=C["dark"],
                 font=("Microsoft YaHei", 14, "bold")).pack(pady=10)
        for r in items:
            tk.Label(win, text=f'{r.get("time","")}  {r.get("text","")}', bg=C["light"],
                     fg=C["dark"], font=("Microsoft YaHei", 11), pady=8).pack(fill="x", padx=16, pady=3)
        bar = tk.Frame(win, bg=C["card"]); bar.pack(pady=14)
        tk.Button(bar, text="知道了", bg=C["main"], fg="white", bd=0, padx=18, pady=6,
                  command=win.destroy).pack(side="left", padx=8)
        tk.Button(bar, text="5分钟后提醒", bg=C["light"], fg=C["dark"], bd=0, padx=14, pady=6,
                  command=lambda: self.snooze(items, win)).pack(side="left", padx=8)

    def snooze(self, items, win):
        until = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
        for r in items:
            r["snooze_until"] = until
        self.save()
        win.destroy()

    def show_evening_check(self):
        today = today_str()
        todos = self.data.get("todos", [])
        undone = [t for t in todos if not t.get("done")]
        habits = self.data.get("habits", [])
        done = self.data.get("habit_done", {}).get(today, [])
        msg = (f"今天待办还剩 {len(undone)} 项未完成。\n"
               f"习惯打卡 {len(done)}/{len(habits)}。\n"
               f"记得写两句今天的记录。")
        messagebox.showinfo("🌙 晚间收尾", msg)

    # ---------- 周计划 ----------
    def p_weekplan(self):
        wk = week_key()
        inner = self.card(f"本周目标（{wk}）")
        goals = self.data.get("week_goals", {}).get(wk, ["", "", ""])
        if len(goals) < 3:
            goals = (goals + ["", "", ""])[:3]
        self.wk_goals = []
        for i in range(3):
            row = tk.Frame(inner, bg=C["card"]); row.pack(fill="x", pady=2)
            tk.Label(row, text=f"目标{i+1}:", bg=C["card"], fg=C["dark"], width=7).pack(side="left")
            e = tk.Entry(row, width=70); e.insert(0, goals[i]); e.pack(side="left", fill="x", expand=True, padx=4)
            self.wk_goals.append(e)
        self.primary(inner, "保存周目标", self.save_week_goals)

        inner2 = self.card("周计划模板（每天固定要做的事）")
        tk.Label(inner2, text="按星期排，保存后“今日安排”和首页会显示当天任务。",
                 bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(0, 4))
        self.wk_entries = {}
        for d in range(7):
            row = tk.Frame(inner2, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"周{WEEKDAYS[d]}", bg=C["card"], fg=C["dark"],
                     width=5, font=("Microsoft YaHei", 9, "bold")).pack(side="left", padx=5)
            e = tk.Entry(row, width=70)
            e.insert(0, "；".join(self.data.get("weekly_template", {}).get(str(d), [])))
            e.pack(side="left", fill="x", expand=True, padx=4)
            self.wk_entries[d] = e
        tk.Label(inner2, text="多条任务用中文分号“；”隔开，例如：普拉提；19:00 陪娃读书",
                 bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(2, 4))
        self.primary(inner2, "保存周计划", self.save_week_template)

    def save_week_goals(self):
        wk = week_key()
        self.data.setdefault("week_goals", {})[wk] = [e.get() for e in self.wk_goals]
        self.save()
        messagebox.showinfo("提示", "周目标已保存")

    def save_week_template(self):
        tpl = self.data.setdefault("weekly_template", {})
        for d, e in self.wk_entries.items():
            parts = [x.strip() for x in e.get().replace("；", ";").split(";") if x.strip()]
            tpl[str(d)] = parts
        self.save()
        messagebox.showinfo("提示", "周计划模板已保存")

    # ---------- 周期任务 ----------
    def p_recurring(self):
        inner = self.card("新增周期任务")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=4)
        tk.Label(r, text="内容:", bg=C["card"]).pack(side="left")
        self.rc_text = tk.Entry(r, width=18); self.rc_text.pack(side="left", padx=4)
        tk.Label(r, text="时间:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.rc_time = tk.Entry(r, width=6); self.rc_time.insert(0, "12:30"); self.rc_time.pack(side="left", padx=4)
        tk.Label(r, text="重复:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.rc_rep = ttk.Combobox(r, values=["每天"] + [f"每周{w}" for w in WEEKDAYS],
                                   width=7, state="readonly"); self.rc_rep.set("每周一"); self.rc_rep.pack(side="left", padx=4)
        self.primary(r, "添加", self.add_recurring)

        inner2 = self.card("周期任务列表")
        self.rc_list = tk.Frame(inner2, bg=C["card"]); self.rc_list.pack(fill="x", pady=4)
        tk.Label(inner2, text="适合固定安排：普拉提、美容院、每周复盘、每月美甲等。点“加入待办”可生成本次待办。",
                 bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(4, 0))
        self.refresh_recurring()

    def add_recurring(self):
        t = self.rc_text.get().strip()
        if not t:
            messagebox.showwarning("提示", "请填写任务内容")
            return
        tm = self.rc_time.get().strip()
        try:
            datetime.strptime(tm, "%H:%M")
        except Exception:
            messagebox.showwarning("提示", "时间格式 HH:MM")
            return
        self.data.setdefault("recurring_tasks", []).append({
            "text": t, "time": tm, "repeat": self.rc_rep.get(), "enabled": True
        })
        self.save()
        self.rc_text.delete(0, tk.END)
        self.refresh_recurring()

    def refresh_recurring(self):
        for w in self.rc_list.winfo_children():
            w.destroy()
        rs = self.data.get("recurring_tasks", [])
        if not rs:
            tk.Label(self.rc_list, text="还没有周期任务。", bg=C["card"], fg=C["muted"]).pack(anchor="w")
            return
        wd = f"每周{WEEKDAYS[datetime.now().weekday()]}"
        for i, r in enumerate(rs):
            row = tk.Frame(self.rc_list, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            var = tk.BooleanVar(value=r.get("enabled", True))
            tk.Checkbutton(row, variable=var, bg=C["card"],
                           command=lambda i=i, v=var: self.toggle_recurring(i, v)).pack(side="left", padx=5)
            tk.Label(row, text=r.get("time", ""), bg=C["card"], width=6, fg=C["dark"],
                     font=("Microsoft YaHei", 9, "bold")).pack(side="left")
            tk.Label(row, text=r.get("text", ""), bg=C["card"], anchor="w").pack(side="left", fill="x", expand=True, padx=5)
            today_tag = "  ← 今天" if (r.get("repeat") == "每天" or r.get("repeat") == wd) else ""
            tk.Label(row, text=r.get("repeat", "") + today_tag, bg=C["card"], fg=C["muted"], width=16).pack(side="left")
            tk.Button(row, text="加入待办", bg=C["light"], fg=C["dark"], bd=0,
                      command=lambda r=r: self.recurring_to_todo(r)).pack(side="right", padx=3)
            tk.Button(row, text="删除", bg=C["border"], bd=0,
                      command=lambda i=i: self.del_recurring(i)).pack(side="right", padx=3)

    def toggle_recurring(self, i, var):
        self.data["recurring_tasks"][i]["enabled"] = var.get()
        self.save()

    def del_recurring(self, i):
        if messagebox.askyesno("确认", "删除这条周期任务？"):
            self.data["recurring_tasks"].pop(i)
            self.save()
            self.refresh_recurring()

    def recurring_to_todo(self, r):
        self.data.setdefault("todos", []).append({
            "text": f'{r.get("time","")} {r.get("text","")}'.strip(), "done": False
        })
        self.save()
        messagebox.showinfo("提示", "已加入待办")

    # ---------- 倒计时 ----------
    def p_countdown(self):
        inner = self.card("新增倒计时")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=4)
        tk.Label(r, text="名称:", bg=C["card"]).pack(side="left")
        self.cd_name = tk.Entry(r, width=18); self.cd_name.pack(side="left", padx=4)
        tk.Label(r, text="日期:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.cd_date = tk.Entry(r, width=11); self.cd_date.insert(0, "2027-01-31"); self.cd_date.pack(side="left", padx=4)
        self.primary(r, "添加", self.add_countdown)

        inner2 = self.card("倒计时列表")
        self.cd_list = tk.Frame(inner2, bg=C["card"]); self.cd_list.pack(fill="x", pady=4)
        self.refresh_countdown()

    def add_countdown(self):
        n = self.cd_name.get().strip()
        d = self.cd_date.get().strip()
        if not n:
            messagebox.showwarning("提示", "请填写名称")
            return
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except Exception:
            messagebox.showwarning("提示", "日期格式 YYYY-MM-DD")
            return
        self.data.setdefault("countdowns", []).append({"name": n, "date": d})
        self.save()
        self.cd_name.delete(0, tk.END)
        self.refresh_countdown()

    def refresh_countdown(self):
        for w in self.cd_list.winfo_children():
            w.destroy()
        today = datetime.now().date()
        for i, c in enumerate(self.data.get("countdowns", [])):
            row = tk.Frame(self.cd_list, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            try:
                days = (datetime.strptime(c["date"], "%Y-%m-%d").date() - today).days
                txt = f"还剩 {days} 天" if days >= 0 else f"已过 {-days} 天"
                color = C["main"] if 0 <= days <= 30 else C["dark"]
            except Exception:
                txt, color = "日期无效", C["muted"]
            tk.Label(row, text=c["name"], bg=C["card"], anchor="w").pack(side="left", padx=8, fill="x", expand=True)
            tk.Label(row, text=c["date"], bg=C["card"], fg=C["muted"], width=12).pack(side="left")
            tk.Label(row, text=txt, bg=C["card"], fg=color, width=12,
                     font=("Microsoft YaHei", 10, "bold")).pack(side="left")
            tk.Button(row, text="删除", bg=C["border"], bd=0,
                      command=lambda i=i: self.del_countdown(i)).pack(side="right", padx=5)

    def del_countdown(self, i):
        if messagebox.askyesno("确认", "删除这个倒计时？"):
            self.data["countdowns"].pop(i)
            self.save()
            self.refresh_countdown()

    # ---------- 每周复盘（自动带数据） ----------
    def week_range(self):
        now = datetime.now().date()
        start = now - timedelta(days=now.weekday())
        return start, now

    # ---------- 项目清单 ----------
    def proj_color(self, status):
        return {"进行中": C["main"], "未开始": C["muted"], "已完成": "#7FA98A",
                "暂停": "#C9A87C"}.get(status, C["main"])

    def p_projects(self):
        bar = tk.Frame(self.con, bg=C["bg"])
        bar.pack(fill="x", padx=18, pady=(10, 2))
        for st in ["全部", "进行中", "未开始", "已完成", "暂停"]:
            on = (st == self.proj_filter)
            tk.Button(bar, text=st, bg=C["main"] if on else C["card"],
                      fg="white" if on else C["muted"], bd=0, relief="flat",
                      font=("Microsoft YaHei", 9, "bold" if on else "normal"),
                      activebackground=C["light"], padx=14, pady=6,
                      command=lambda s=st: self.set_proj_filter(s)).pack(side="left", padx=(0, 6))
        self.primary(bar, "＋ 新增项目", self.add_project)
        self.link(bar, "批量导入", self.import_projects)

        ps = self.data.get("projects", [])
        running = len([p for p in ps if p.get("status") == "进行中"])
        tk.Label(bar, text=f"进行中 {running} · 共 {len(ps)} 个", bg=C["bg"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(side="right", padx=8)
        shown = [p for p in ps if self.proj_filter == "全部" or p.get("status") == self.proj_filter]
        if not shown:
            inner = self.card("还没有项目")
            tk.Label(inner, text="点上面的「＋ 新增项目」开始记录。",
                     bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 9)).pack(anchor="w")
            return

        for p in shown:
            self.render_project(p)

    def set_proj_filter(self, st):
        self.proj_filter = st
        self.show("projects")

    # ---------- 项目批量导入（粘贴 Excel） ----------
    def import_projects(self):
        win = tk.Toplevel(self.root)
        win.title("批量导入项目")
        win.configure(bg=C["card"])
        win.geometry("640x480")
        win.transient(self.root)
        tk.Label(win, text="在 Excel 里选中表头和数据行，复制（Ctrl+C），粘贴到下面，点「导入」。",
                 bg=C["card"], fg=C["text"], justify="left",
                 font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(win, text="列顺序：项目名称　状态　进度%　负责人　对接人　截止　下一步　备注\n"
                           "第一行是表头会自动识别；列不全也没关系，按顺序排即可。"
                           "和已有项目同名的会更新，不会重复。",
                 bg=C["card"], fg=C["muted"], justify="left",
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=16, pady=(0, 8))
        txt = tk.Text(win, height=13, font=("Microsoft YaHei", 10), undo=True)
        txt.pack(fill="both", expand=True, padx=16)
        bar = tk.Frame(win, bg=C["card"])
        bar.pack(fill="x", padx=16, pady=12)
        self.primary(bar, "导入", lambda: self.do_import_projects(txt.get("1.0", "end"), win))
        self.ghost(bar, "取消", win.destroy)

    def do_import_projects(self, text, win):
        rows = [[c.strip() for c in r.split("\t")]
                for r in text.replace("\r", "").split("\n") if r.strip()]
        if not rows:
            messagebox.showinfo("批量导入", "先粘贴 Excel 内容再导入")
            return
        keys = ["name", "status", "progress", "owner", "contact", "due", "next", "note"]
        words = (("name", "名称|项目"), ("status", "状态"), ("progress", "进度"),
                 ("owner", "负责人"), ("contact", "对接人|联系"), ("due", "截止|期限"),
                 ("next", "下一步|行动"), ("note", "备注|说明"))

        def kw(col):
            for k, ws in words:
                if any(w in col for w in ws.split("|")):
                    return k
            return None

        if sum(1 for c in rows[0] if kw(c)) >= 3:   # 表头至少要命中 3 个列名，避免把数据行误判
            colmap, data_rows = [kw(c) for c in rows[0]], rows[1:]
        else:
            colmap, data_rows = keys, rows
        added = updated = 0
        ps = self.data.setdefault("projects", [])
        byname = {p.get("name", ""): p for p in ps}
        for r in data_rows:
            item = {k: r[i] for i, k in enumerate(colmap) if k and i < len(r)}
            name = item.get("name", "")
            if not name:
                continue
            st = item.get("status", "")
            st = next((s for s in ("进行中", "未开始", "已完成", "暂停") if s in st), "进行中")
            try:
                prog = max(0, min(100, int(float(str(item.get("progress", "0")).replace("%", "")))))
            except Exception:
                prog = 0
            vals = {"status": st, "progress": prog,
                    "owner": item.get("owner", ""), "contact": item.get("contact", ""),
                    "due": item.get("due", ""), "next": item.get("next", ""),
                    "note": item.get("note", "")}
            if name in byname:
                byname[name].update(vals)
                updated += 1
            else:
                p = {"id": uuid.uuid4().hex[:8], "name": name, "todos": []}
                p.update(vals)
                ps.append(p)
                byname[name] = p
                added += 1
        self.save()
        self.update_proj_badge()
        win.destroy()
        self.show("projects")
        messagebox.showinfo("批量导入", f"新增 {added} 个，更新 {updated} 个")

    def render_project(self, p):
        pid = p.get("id", "")
        f = tk.Frame(self.con, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
        f.pack(fill="x", padx=18, pady=6)

        head = tk.Frame(f, bg=C["card"])
        head.pack(fill="x", padx=14, pady=(11, 0))
        tk.Label(head, text=p.get("name", "未命名项目"), bg=C["card"], fg=C["text"],
                 anchor="w", font=("Microsoft YaHei", 12, "bold")).pack(side="left")
        tk.Label(head, text=p.get("status", "进行中"), bg=self.proj_color(p.get("status")),
                 fg="white", font=("Microsoft YaHei", 8, "bold"), padx=9, pady=3).pack(side="right", padx=(6, 0))
        tk.Label(head, text=f'{int(p.get("progress", 0))}%', bg=C["card"], fg=C["dark"],
                 font=("Microsoft YaHei", 12, "bold"), width=5).pack(side="right")

        pct = max(0, min(100, int(p.get("progress", 0) or 0)))
        barbg = tk.Frame(f, bg=C["light"], height=7)
        barbg.pack(fill="x", padx=14, pady=(8, 0))
        barbg.pack_propagate(False)
        fill = tk.Frame(barbg, bg=self.proj_color(p.get("status")), height=7)
        fill.place(relx=0, rely=0, relheight=1, relwidth=pct / 100)

        meta = tk.Frame(f, bg=C["card"])
        meta.pack(fill="x", padx=14, pady=(9, 0))
        for lab, val in [("负责人", p.get("owner", "")), ("对接人", p.get("contact", "")),
                         ("截止", p.get("due", "")), ("下一步", p.get("next", ""))]:
            if not val:
                continue
            cell = tk.Frame(meta, bg=C["card"])
            cell.pack(side="left", padx=(0, 18))
            tk.Label(cell, text=lab, bg=C["card"], fg=C["muted"],
                     font=("Microsoft YaHei", 8)).pack(anchor="w")
            tk.Label(cell, text=val, bg=C["card"], fg=C["text"],
                     font=("Microsoft YaHei", 9, "bold")).pack(anchor="w")
        if p.get("note"):
            tk.Label(f, text=p.get("note", ""), bg=C["card"], fg=C["muted"], anchor="w",
                     justify="left", wraplength=760, font=("Microsoft YaHei", 8)).pack(fill="x", padx=14, pady=(6, 0))

        # 跟进事项
        todos = p.get("todos", [])
        done = len([t for t in todos if t.get("done")])
        line = tk.Frame(f, bg=C["card"])
        line.pack(fill="x", padx=14, pady=(9, 0))
        opened = pid in self.proj_open
        tk.Button(line, text=("▼" if opened else "▶") + f"  跟进事项 {done}/{len(todos)}",
                  bg=C["card"], fg=C["dark"], bd=0, relief="flat", anchor="w",
                  font=("Microsoft YaHei", 9, "bold"), activebackground=C["light"],
                  command=lambda: self.toggle_proj(pid)).pack(side="left")
        tk.Button(line, text="编辑", bg=C["card"], fg=C["muted"], bd=0, relief="flat",
                  font=("Microsoft YaHei", 9), activebackground=C["light"],
                  command=lambda pp=p: self.edit_project(pp)).pack(side="right")
        tk.Button(line, text="删除", bg=C["card"], fg=C["muted"], bd=0, relief="flat",
                  font=("Microsoft YaHei", 9), activebackground=C["light"],
                  command=lambda pp=p: self.del_project(pp)).pack(side="right", padx=(0, 14))

        if opened:
            for i, t in enumerate(todos):
                row = tk.Frame(f, bg=C["card"])
                row.pack(fill="x", padx=30, pady=1)
                var = tk.BooleanVar(value=t.get("done", False))
                tk.Checkbutton(row, variable=var, bg=C["card"], activebackground=C["card"],
                               command=lambda pid=pid, i=i: self.toggle_proj_todo(pid, i)).pack(side="left")
                tk.Label(row, text=t.get("text", ""), bg=C["card"],
                         fg=C["muted"] if t.get("done") else C["text"], anchor="w",
                         font=("Microsoft YaHei", 9)).pack(side="left", fill="x", expand=True)
                if t.get("date"):
                    tk.Label(row, text=t.get("date", ""), bg=C["card"], fg=C["muted"],
                             font=("Microsoft YaHei", 8)).pack(side="right")
            addrow = tk.Frame(f, bg=C["card"])
            addrow.pack(fill="x", padx=30, pady=(4, 10))
            e = tk.Entry(addrow)
            e.pack(side="left", fill="x", expand=True, ipady=4)
            e.bind("<Return>", lambda ev, pid=pid: self.add_proj_todo(pid))
            self.proj_entries[pid] = e
            self.primary(addrow, "添加跟进事项",
                         lambda pid=pid, ent=e: self.add_proj_todo(pid, ent))
        else:
            tk.Frame(f, bg=C["card"], height=10).pack()

    def toggle_proj(self, pid):
        if pid in self.proj_open:
            self.proj_open.discard(pid)
        else:
            self.proj_open.add(pid)
        self.show("projects")

    def find_proj(self, pid):
        for p in self.data.get("projects", []):
            if p.get("id") == pid:
                return p
        return None

    def toggle_proj_todo(self, pid, i):
        p = self.find_proj(pid)
        if p and i < len(p.get("todos", [])):
            p["todos"][i]["done"] = not p["todos"][i].get("done", False)
            self.save()
            self.show("projects")

    def add_proj_todo(self, pid, ent=None):
        p = self.find_proj(pid)
        if not p:
            return
        if ent is None:
            ent = self.proj_entries.get(pid)
        if ent is None:
            return
        txt = ent.get().strip()
        if not txt:
            return
        p.setdefault("todos", []).append({"text": txt, "done": False, "date": ""})
        self.save()
        self.show("projects")

    def del_project(self, p):
        if messagebox.askyesno("确认", f"删除项目「{p.get('name','')}」？"):
            self.data["projects"] = [x for x in self.data.get("projects", []) if x.get("id") != p.get("id")]
            self.save()
            self.update_proj_badge()
            self.show("projects")

    def add_project(self):
        self.project_dialog(None)

    def edit_project(self, p):
        self.project_dialog(p)

    def project_dialog(self, p):
        new = p is None
        win = tk.Toplevel(self.root)
        win.title("新增项目" if new else "编辑项目")
        win.configure(bg=C["card"])
        win.geometry("520x520")
        win.transient(self.root)

        def field(label, key, width=26, default=""):
            tk.Label(win, text=label, bg=C["card"], fg=C["muted"],
                     font=("Microsoft YaHei", 9)).pack(anchor="w", padx=22, pady=(10, 1))
            e = tk.Entry(win, width=width)
            e.insert(0, p.get(key, default) if p else default)
            e.pack(fill="x", padx=22)
            return e

        name_e = field("项目名称", "name")
        st_var = tk.StringVar(value=(p.get("status", "进行中") if p else "进行中"))
        tk.Label(win, text="状态", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=22, pady=(10, 1))
        ttk.Combobox(win, textvariable=st_var, values=["未开始", "进行中", "已完成", "暂停"],
                     width=12, state="readonly").pack(anchor="w", padx=22)
        owner_e = field("负责人（内部）", "owner")
        contact_e = field("对接人（外部）", "contact")
        tk.Label(win, text="截止日期", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=22, pady=(10, 1))
        due_row = tk.Frame(win, bg=C["card"])
        due_row.pack(fill="x", padx=22)
        due_e = tk.Entry(due_row, width=26)
        due_e.insert(0, p.get("due", "") if p else "")
        due_e.pack(side="left", fill="x", expand=True)
        self.date_row(due_row, due_e)
        next_e = field("下一步动作", "next")
        prog_var = tk.IntVar(value=int(p.get("progress", 0) or 0) if p else 0)
        tk.Label(win, text="进度 %", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=22, pady=(10, 1))
        tk.Spinbox(win, from_=0, to=100, increment=5, textvariable=prog_var, width=8).pack(anchor="w", padx=22)
        tk.Label(win, text="备注", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=22, pady=(10, 1))
        note_t = tk.Text(win, height=4)
        note_t.pack(fill="x", padx=22)
        note_t.insert("1.0", p.get("note", "") if p else "")

        def save():
            nm = name_e.get().strip()
            if not nm:
                messagebox.showwarning("提示", "请填写项目名称", parent=win)
                return
            item = p if p else {"id": uuid.uuid4().hex[:8], "todos": []}
            item.update({
                "name": nm, "status": st_var.get(), "owner": owner_e.get().strip(),
                "contact": contact_e.get().strip(), "due": due_e.get().strip(),
                "next": next_e.get().strip(), "progress": max(0, min(100, prog_var.get())),
                "note": note_t.get("1.0", "end-1c").strip(),
            })
            if new:
                self.data.setdefault("projects", []).append(item)
            self.save()
            self.update_proj_badge()
            win.destroy()
            self.show("projects")

        bar = tk.Frame(win, bg=C["card"])
        bar.pack(pady=16)
        tk.Button(bar, text="保存", bg=C["main"], fg="white", bd=0, font=("Microsoft YaHei", 10),
                  padx=22, pady=6, command=save).pack(side="left", padx=6)
        tk.Button(bar, text="取消", bg=C["light"], fg=C["dark"], bd=0, font=("Microsoft YaHei", 10),
                  padx=18, pady=6, command=win.destroy).pack(side="left", padx=6)

    def update_proj_badge(self):
        # 导航里只写名字，不写数字（数字容易看不懂）
        item = self.btns.get("projects")
        if item:
            item[0].config(text="项目清单")

    # ---------- 每月目标 ----------
    def p_goal(self):
        inner = self.card("每月目标")
        tk.Label(inner, text="本月目标与计划", bg=C["card"], anchor="w").pack(fill="x", pady=(6, 0))
        self.gt = tk.Text(inner, width=70, height=12); self.gt.pack(fill="x", pady=4)
        self.gt.insert("1.0", self.data.get("monthly_goal", ""))
        self.primary(inner, "保存目标", self.save_goal)

    def save_goal(self):
        self.data["monthly_goal"] = self.gt.get("1.0", "end-1c")
        self.save()
        messagebox.showinfo("提示", "目标已保存")

    # ---------- 减肥记录 ----------
    def p_weight(self):
        inner = self.card("体重目标与趋势")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=3)
        tk.Label(r, text="当前:", bg=C["card"]).pack(side="left")
        self.wcur = tk.Entry(r, width=6); self.wcur.insert(0, str(self.data["weight_goal"]["current"])); self.wcur.pack(side="left", padx=3)
        tk.Label(r, text="目标:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.wtgt = tk.Entry(r, width=6); self.wtgt.insert(0, str(self.data["weight_goal"]["target"])); self.wtgt.pack(side="left", padx=3)
        tk.Label(r, text="日期:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.wdate = tk.Entry(r, width=11); self.wdate.insert(0, self.data["weight_goal"]["date"]); self.wdate.pack(side="left", padx=3)
        self.primary(r, "保存", self.save_weight_goal)
        self.lblp = tk.Label(inner, text="进度: 0%", bg=C["card"], fg=C["dark"],
                             font=("Microsoft YaHei", 10, "bold")); self.lblp.pack(pady=(6, 0))
        self.barb = tk.Frame(inner, bg=C["light"], height=12, width=300); self.barb.pack(pady=4)
        self.barf = tk.Frame(self.barb, bg=C["main"], height=12, width=0); self.barf.place(relx=0, rely=0, relheight=1)
        self.chart = tk.Canvas(inner, width=560, height=180, bg="white", highlightthickness=1,
                               highlightbackground=C["border"])
        self.chart.pack(pady=6)
        self.draw_weight_chart()

        inner2 = self.card("饮水")
        self.water_lbl = tk.Label(inner2, text="", bg=C["card"], fg=C["dark"], font=("Microsoft YaHei", 10, "bold"))
        self.water_lbl.pack(anchor="w")
        cups = tk.Frame(inner2, bg=C["card"]); cups.pack(fill="x", pady=4)
        self.cup_btns = []
        for i in range(8):
            b = tk.Button(cups, text=f"{i+1}", width=4, bd=0, bg=C["light"], fg=C["dark"],
                          command=lambda i=i: self.set_water(i + 1))
            b.pack(side="left", padx=3)
            self.cup_btns.append(b)
        self.refresh_water()

        inner3 = self.card("体重记录")
        r3 = tk.Frame(inner3, bg=C["card"]); r3.pack(fill="x", pady=3)
        tk.Label(r3, text="日期:", bg=C["card"]).pack(side="left")
        self.wd = tk.Entry(r3, width=11); self.wd.insert(0, today_str()); self.wd.pack(side="left", padx=3)
        self.date_row(r3, self.wd)
        tk.Label(r3, text="体重:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.wv = tk.Entry(r3, width=7); self.wv.pack(side="left", padx=3)
        self.primary(r3, "添加", self.add_weight)
        self.wl = tk.Frame(inner3, bg=C["card"]); self.wl.pack(fill="x", pady=3)
        self.refresh_weight()

        inner4 = self.card("饮食记录")
        r4 = tk.Frame(inner4, bg=C["card"]); r4.pack(fill="x", pady=3)
        tk.Label(r4, text="日期:", bg=C["card"]).pack(side="left")
        self.dd = tk.Entry(r4, width=11); self.dd.insert(0, today_str()); self.dd.pack(side="left", padx=3)
        self.date_row(r4, self.dd)
        tk.Label(r4, text="餐次:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.dm = tk.Entry(r4, width=6); self.dm.insert(0, "早餐"); self.dm.pack(side="left", padx=3)
        tk.Label(r4, text="内容:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.df = tk.Entry(r4, width=22); self.df.pack(side="left", padx=3)
        self.primary(r4, "添加", self.add_diet)
        self.dl = tk.Frame(inner4, bg=C["card"]); self.dl.pack(fill="x", pady=3)
        self.refresh_diet()
        self.refresh_progress()

    def save_weight_goal(self):
        try:
            self.data["weight_goal"]["current"] = float(self.wcur.get())
            self.data["weight_goal"]["target"] = float(self.wtgt.get())
            self.data["weight_goal"]["date"] = self.wdate.get()
            self.save()
            self.refresh_progress()
            messagebox.showinfo("提示", "目标已保存")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def refresh_progress(self):
        try:
            cur = float(self.data["weight_goal"]["current"])
            tgt = float(self.data["weight_goal"]["target"])
            tot = abs(cur - tgt)
            latest = float(self.data["weight_records"][-1]["weight"]) if self.data["weight_records"] else cur
            lost = abs(cur - latest)
            pct = min(100, max(0, int(lost / tot * 100))) if tot > 0 else 0
            self.lblp.config(text=f"进度: {pct}% ({cur}kg → {tgt}kg，已减 {lost:.1f}kg)")
            self.barf.config(width=300 * pct / 100)
        except Exception:
            pass

    def draw_weight_chart(self):
        cv = self.chart
        cv.delete("all")
        recs = self.data.get("weight_records", [])[-20:]
        tgt = self.data["weight_goal"]["target"]
        if len(recs) < 2:
            cv.create_text(280, 90, text="添加至少 2 条体重记录后显示趋势", fill=C["muted"],
                           font=("Microsoft YaHei", 10))
            return
        vals = [float(r["weight"]) for r in recs]
        lo = min(vals + [tgt]) - 1
        hi = max(vals + [tgt]) + 1
        pad_l, pad_r, pad_t, pad_b = 42, 14, 14, 26
        w, h = 560 - pad_l - pad_r, 180 - pad_t - pad_b

        def px(i):
            return pad_l + (w * i / max(1, len(recs) - 1))

        def py(v):
            return pad_t + h - (v - lo) / (hi - lo) * h

        cv.create_line(pad_l, pad_t, pad_l, pad_t + h, fill=C["border"])
        cv.create_line(pad_l, pad_t + h, pad_l + w, pad_t + h, fill=C["border"])
        cv.create_text(6, py(hi) + 6, text=f"{hi:.0f}", fill=C["muted"], font=("Microsoft YaHei", 8))
        cv.create_text(6, py(lo) - 6, text=f"{lo:.0f}", fill=C["muted"], font=("Microsoft YaHei", 8))
        cv.create_line(pad_l, py(tgt), pad_l + w, py(tgt), dash=(4, 3), fill=tint(C["main"], 0.6))
        cv.create_text(pad_l + w - 30, py(tgt) - 9, text=f"目标 {tgt}", fill=C["main"],
                       font=("Microsoft YaHei", 8))
        pts = []
        for i, r in enumerate(recs):
            pts.append((px(i), py(float(r["weight"]))))
        cv.create_line(*[c for p in pts for c in p], fill=C["main"], width=2, smooth=True)
        for i, p in enumerate(pts):
            cv.create_oval(p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3, fill=C["main"], outline="")
        cv.create_text(pts[-1][0] - 8, pts[-1][1] - 12, text=f'{recs[-1]["weight"]}kg',
                       fill=C["dark"], font=("Microsoft YaHei", 9, "bold"))
        cv.create_text(pad_l, pad_t + h + 12, text=recs[0]["date"][5:], fill=C["muted"],
                       font=("Microsoft YaHei", 8))
        cv.create_text(pad_l + w, pad_t + h + 12, text=recs[-1]["date"][5:], fill=C["muted"],
                       font=("Microsoft YaHei", 8))

    def add_weight(self):
        try:
            self.data["weight_records"].append({"date": self.wd.get(), "weight": float(self.wv.get())})
            self.save()
            self.wv.delete(0, tk.END)
            self.refresh_weight()
            self.refresh_progress()
            self.draw_weight_chart()
        except Exception:
            messagebox.showerror("错误", "请输入有效的体重数字")

    def del_weight(self, i):
        if messagebox.askyesno("确认", "删除这条记录？"):
            self.data["weight_records"].pop(i)
            self.save()
            self.refresh_weight()
            self.refresh_progress()
            self.draw_weight_chart()

    def refresh_weight(self):
        for w in self.wl.winfo_children():
            w.destroy()
        for i, r in enumerate(reversed(self.data["weight_records"])):
            row = tk.Frame(self.wl, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=r["date"], bg=C["card"], width=12, anchor="w").pack(side="left", padx=5)
            tk.Label(row, text=f'{r["weight"]}kg', bg=C["card"], width=9, anchor="w",
                     fg=C["dark"], font=("Microsoft YaHei", 10, "bold")).pack(side="left", padx=8)
            tk.Button(row, text="删除", bg=C["border"], bd=0,
                      command=lambda i=len(self.data["weight_records"]) - 1 - i: self.del_weight(i)).pack(side="right", padx=5)

    def set_water(self, n):
        d = today_str()
        cur = self.data.setdefault("water", {}).get(d, 0)
        self.data["water"][d] = n if n != cur else n - 1
        self.save()
        self.refresh_water()

    def refresh_water(self):
        n = self.data.get("water", {}).get(today_str(), 0)
        self.water_lbl.config(text=f"今日饮水：{n} / 8 杯")
        for i, b in enumerate(self.cup_btns):
            b.config(bg=C["main"] if i < n else C["light"],
                     fg="white" if i < n else C["dark"])

    def add_diet(self):
        self.data["diet_records"].append({
            "date": self.dd.get(), "meal": self.dm.get(), "food": self.df.get()
        })
        self.save()
        self.df.delete(0, tk.END)
        self.refresh_diet()

    def del_diet(self, i):
        if messagebox.askyesno("确认", "删除这条记录？"):
            self.data["diet_records"].pop(i)
            self.save()
            self.refresh_diet()

    def refresh_diet(self):
        for w in self.dl.winfo_children():
            w.destroy()
        for i, r in enumerate(reversed(self.data["diet_records"])):
            row = tk.Frame(self.dl, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=r["date"], bg=C["card"], width=12, anchor="w").pack(side="left", padx=5)
            tk.Label(row, text=r["meal"], bg=C["card"], width=7, anchor="w").pack(side="left")
            tk.Label(row, text=r["food"], bg=C["card"], anchor="w").pack(side="left", padx=8, fill="x", expand=True)
            tk.Button(row, text="删除", bg=C["border"], bd=0,
                      command=lambda i=len(self.data["diet_records"]) - 1 - i: self.del_diet(i)).pack(side="right", padx=5)

    # ---------- 医美清单 ----------
    def p_beauty(self):
        inner = self.card("医美清单")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=4)
        tk.Label(r, text="项目:", bg=C["card"]).pack(side="left")
        self.bn = tk.Entry(r, width=12); self.bn.pack(side="left", padx=3)
        tk.Label(r, text="日期:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.bd = tk.Entry(r, width=11); self.bd.insert(0, today_str()); self.bd.pack(side="left", padx=3)
        self.date_row(r, self.bd)
        tk.Label(r, text="费用:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.bc = tk.Entry(r, width=8); self.bc.pack(side="left", padx=3)
        tk.Label(r, text="备注:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.bno = tk.Entry(r, width=16); self.bno.pack(side="left", padx=3)
        self.primary(r, "添加", self.add_beauty)
        self.bl = tk.Frame(inner, bg=C["card"]); self.bl.pack(fill="x", pady=4)
        self.refresh_beauty()

    def add_beauty(self):
        self.data["medical_beauty"].append({
            "name": self.bn.get(), "date": self.bd.get(),
            "cost": self.bc.get(), "note": self.bno.get()
        })
        self.save()
        self.bn.delete(0, tk.END); self.bc.delete(0, tk.END); self.bno.delete(0, tk.END)
        self.refresh_beauty()

    def del_beauty(self, i):
        if messagebox.askyesno("确认", "删除此项？"):
            self.data["medical_beauty"].pop(i)
            self.save()
            self.refresh_beauty()

    def refresh_beauty(self):
        for w in self.bl.winfo_children():
            w.destroy()
        for i, r in enumerate(reversed(self.data["medical_beauty"])):
            row = tk.Frame(self.bl, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=r["name"], bg=C["card"], width=14, anchor="w").pack(side="left", padx=5)
            tk.Label(row, text=r["date"], bg=C["card"], width=11, anchor="w").pack(side="left")
            tk.Label(row, text=r["cost"], bg=C["card"], width=8, anchor="w").pack(side="left", padx=4)
            tk.Label(row, text=r["note"], bg=C["card"], anchor="w").pack(side="left", padx=6, fill="x", expand=True)
            tk.Button(row, text="删除", bg=C["border"], bd=0,
                      command=lambda i=len(self.data["medical_beauty"]) - 1 - i: self.del_beauty(i)).pack(side="right", padx=5)

    # ---------- 习惯打卡（连续天数 + 热力图） ----------
    def habit_streak(self, h):
        n = 0
        d = datetime.now().date()
        while True:
            ds = d.strftime("%Y-%m-%d")
            if h in self.data.get("habit_done", {}).get(ds, []):
                n += 1
                d -= timedelta(days=1)
            else:
                break
        return n

    def p_habits(self):
        today = today_str()
        done = set(self.data.get("habit_done", {}).get(today, []))
        habits = self.data.get("habits", [])
        n_done = len([h for h in habits if h in done])
        inner = self.card(f"今日打卡　{n_done}/{len(habits)}")
        for h in habits:
            on = h in done
            rbg = C["light"] if on else C["soft"]
            row = tk.Frame(inner, bg=rbg, highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=3)
            box = tk.Label(row, text="✓" if on else "", bg=C["main"] if on else C["card"],
                           fg="white" if on else C["muted"], width=2,
                           font=("Microsoft YaHei", 12, "bold"))
            box.pack(side="left", padx=(10, 10), pady=9)
            name = tk.Label(row, text=h, bg=rbg, fg=C["dark"] if on else C["text"],
                            font=("Microsoft YaHei", 11, "bold" if on else "normal"), anchor="w")
            name.pack(side="left", fill="x", expand=True)
            st = tk.Label(row, text=f"连续 {self.habit_streak(h)} 天", bg=rbg, fg=C["muted"],
                          font=("Microsoft YaHei", 8))
            st.pack(side="right", padx=12)
            for w in (row, box, name, st):
                w.bind("<Button-1>", lambda e, hh=h: self.toggle_habit(hh))
                try:
                    w.config(cursor="hand2")
                except Exception:
                    pass

        ar = tk.Frame(inner, bg=C["card"]); ar.pack(fill="x", pady=(10, 0))
        tk.Label(ar, text="新习惯", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 6))
        self.nh = tk.Entry(ar, width=14); self.nh.pack(side="left", padx=2, ipady=3)
        self.primary(ar, "添加", self.add_habit)
        self.ghost(ar, "删除习惯", self.remove_habit)

        inner2 = self.card("最近 16 周打卡热力图")
        cv = tk.Canvas(inner2, width=620, height=248, bg=C["card"],
                       highlightthickness=0)
        cv.pack(pady=4)
        self.draw_heatmap(cv)

    def toggle_habit(self, name):
        d = today_str()
        arr = self.data.setdefault("habit_done", {}).setdefault(d, [])
        if name in arr:
            arr.remove(name)
        else:
            arr.append(name)
        self.save()
        self.show("habits")

    def add_habit(self):
        n = self.nh.get().strip()
        if n and n not in self.data.get("habits", []):
            self.data.setdefault("habits", []).append(n)
            self.save()
            self.show("habits")

    def remove_habit(self):
        habits = self.data.get("habits", [])
        if not habits:
            return
        win = tk.Toplevel(self.root)
        win.title("删除习惯")
        win.configure(bg=C["card"])
        tk.Label(win, text="选择要删除的习惯：", bg=C["card"]).pack(pady=8)
        lb = tk.Listbox(win, height=min(10, len(habits)), width=24)
        lb.pack(padx=10)
        for h in habits:
            lb.insert(tk.END, h)
        def do_del():
            sel = lb.curselection()
            if not sel:
                return
            h = lb.get(sel[0])
            self.data["habits"].remove(h)
            self.save()
            win.destroy()
            self.show("habits")
        tk.Button(win, text="删除", bg=C["main"], fg="white", bd=0,
                  command=do_del).pack(pady=8)

    def draw_heatmap(self, cv):
        habits = self.data.get("habits", [])
        if not habits:
            cv.create_text(310, 75, text="暂无习惯", fill=C["muted"])
            return
        total = len(habits)
        cell, gap = 26, 4
        weeks = 16
        x0, y0 = 44, 14
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        start = monday - timedelta(days=(weeks - 1) * 7)
        done_map = self.data.get("habit_done", {})
        for w in range(weeks):
            for d in range(7):
                day = start + timedelta(days=w * 7 + d)
                if day > today:
                    continue
                n = len([h for h in done_map.get(day.strftime("%Y-%m-%d"), []) if h in habits])
                ratio = n / total if total else 0
                if ratio == 0:
                    color = C["soft"]
                elif ratio < 0.34:
                    color = tint(C["main"], 0.22)
                elif ratio < 0.67:
                    color = tint(C["main"], 0.45)
                elif ratio < 1:
                    color = tint(C["main"], 0.72)
                else:
                    color = C["main"]
                x = x0 + w * (cell + gap)
                y = y0 + d * (cell + gap)
                cv.create_rectangle(x, y, x + cell, y + cell, fill=color, outline=C["card"])
        for d, name in enumerate(WEEKDAYS):
            cv.create_text(26, y0 + d * (cell + gap) + cell / 2, text=name, fill=C["muted"],
                           font=("Microsoft YaHei", 8))
        cv.create_text(x0, y0 + 7 * (cell + gap) + 6,
                       text="颜色越深，当天完成的习惯越多", fill=C["muted"],
                       font=("Microsoft YaHei", 8), anchor="w")

    # ---------- 学习番茄 ----------
    def p_study(self):
        # ---- 分类学习清单 ----
        cats = self.data.get("study_cats", [])
        items = self.data.get("study_items", [])
        head = tk.Frame(self.con, bg=C["bg"])
        head.pack(fill="x", padx=18, pady=(10, 2))
        self.primary(head, "＋ 添加学习条目", self.add_study_item)
        self.link(head, "＋ 新建分类", self.add_study_cat)

        for cat in cats:
            sub = [i for i in items if i.get("cat") == cat]
            inner = self.card(f"📂 {cat}　{len(sub)} 项")
            if not sub:
                tk.Label(inner, text="空", bg=C["card"], fg=C["muted"],
                         font=("Microsoft YaHei", 9)).pack(anchor="w")
            for it in sub:
                row = tk.Frame(inner, bg=C["card"])
                row.pack(fill="x", pady=3)
                col = {"想学": C["muted"], "在学": C["main"], "已学": "#7FA98A"}.get(it.get("status"), C["muted"])
                tk.Label(row, text=it.get("status", "想学"), bg=C["light"], fg=col,
                         font=("Microsoft YaHei", 8, "bold"), padx=8, pady=2).pack(side="left")
                tk.Label(row, text=it.get("name", ""), bg=C["card"], fg=C["text"], anchor="w",
                         font=("Microsoft YaHei", 10)).pack(side="left", fill="x", expand=True, padx=8)
                mins = self.study_minutes_of(it.get("name", ""))
                if mins:
                    tk.Label(row, text=f"{mins} 分钟", bg=C["card"], fg=C["muted"],
                             font=("Microsoft YaHei", 8)).pack(side="right", padx=4)
                self.ghost(row, "改", lambda it=it: self.edit_study_item(it))
                self.ghost(row, "删", lambda it=it: self.del_study_item(it))

        # ---- 番茄钟 ----
        inner = self.card("⏱️ 番茄钟")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=4)
        names = [s["name"] for s in self.data.get("cpa_subjects", [])] + \
                [i.get("name", "") for i in items] + ["其他"]
        names = [n for n in dict.fromkeys(names) if n]
        tk.Label(r, text="学习内容:", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.st_sub = ttk.Combobox(r, values=names, width=16, state="readonly")
        self.st_sub.set(names[0] if names else "其他")
        self.st_sub.pack(side="left", padx=6)
        tk.Label(r, text="时长:", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(side="left", padx=(10, 0))
        self.st_min = tk.Entry(r, width=5); self.st_min.insert(0, "25"); self.st_min.pack(side="left", padx=4)
        self.st_label = tk.Label(inner, text="25:00", bg=C["card"], fg=C["dark"],
                                 font=("Consolas", 34, "bold"))
        self.st_label.pack(pady=6)
        bar = tk.Frame(inner, bg=C["card"]); bar.pack(pady=4)
        self.primary(bar, "开始", self.start_pomo)
        self.link(bar, "暂停", self.pause_pomo)
        self.link(bar, "重置", self.reset_pomo)

        # ---- 统计 ----
        inner2 = self.card("学习统计")
        stats = tk.Frame(inner2, bg=C["card"]); stats.pack(fill="x")
        start, end = self.week_range()
        s_s, e_s = start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        month = datetime.now().strftime("%Y-%m")
        logs = self.data.get("study_log", [])
        wk = sum(int(x.get("minutes", 0)) for x in logs if s_s <= x.get("date", "") <= e_s)
        mo = sum(int(x.get("minutes", 0)) for x in logs if str(x.get("date", "")).startswith(month))
        tk.Label(stats, text=f"本周 {wk} 分钟（约 {wk/60:.1f} 小时）　｜　本月 {mo} 分钟（约 {mo/60:.1f} 小时）",
                 bg=C["card"], fg=C["dark"], font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", pady=3)
        by = {}
        for x in logs:
            if str(x.get("date", "")).startswith(month):
                k = x.get("cat") or x.get("subject", "其他")
                by[k] = by.get(k, 0) + int(x.get("minutes", 0))
        if by:
            for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
                tk.Label(stats, text=f"· {k}：{v} 分钟", bg=C["card"], fg=C["text"]).pack(anchor="w")
        else:
            tk.Label(stats, text="本月还没有学习记录", bg=C["card"], fg=C["muted"]).pack(anchor="w")
        self.primary(inner2, "手动记一笔", self.manual_study)

    def study_minutes_of(self, name):
        return sum(int(x.get("minutes", 0)) for x in self.data.get("study_log", [])
                   if x.get("subject") == name)

    def study_cat_of(self, name):
        for i in self.data.get("study_items", []):
            if i.get("name") == name:
                return i.get("cat", "其他")
        for s in self.data.get("cpa_subjects", []):
            if s.get("name") == name:
                return "CPA专业"
        return "其他"

    def add_study_cat(self):
        win = tk.Toplevel(self.root)
        win.title("新建分类")
        win.configure(bg=C["card"])
        win.geometry("340x150")
        win.transient(self.root)
        tk.Label(win, text="分类名称", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=20, pady=(16, 2))
        e = tk.Entry(win, width=22)
        e.pack(fill="x", padx=20)
        e.insert(0, "")

        def ok():
            t = e.get().strip()
            if not t:
                return
            cats = self.data.setdefault("study_cats", [])
            if t not in cats:
                cats.append(t)
            self.save()
            win.destroy()
            self.show("study")

        tk.Button(win, text="添加", bg=C["main"], fg="white", bd=0, font=("Microsoft YaHei", 10),
                  padx=20, pady=6, command=ok).pack(pady=14)

    def add_study_item(self):
        self.study_item_dialog(None)

    def edit_study_item(self, it):
        self.study_item_dialog(it)

    def study_item_dialog(self, it):
        win = tk.Toplevel(self.root)
        win.title("学习条目")
        win.configure(bg=C["card"])
        win.geometry("440x330")
        win.transient(self.root)
        tk.Label(win, text="学习内容", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=22, pady=(16, 2))
        name_e = tk.Entry(win); name_e.pack(fill="x", padx=22)
        name_e.insert(0, it.get("name", "") if it else "")
        tk.Label(win, text="分类", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=22, pady=(12, 2))
        cat_var = tk.StringVar(value=it.get("cat", "") if it else
                               (self.data.get("study_cats") or ["其他"])[0])
        ttk.Combobox(win, textvariable=cat_var, values=self.data.get("study_cats", []) or ["其他"],
                     width=20, state="readonly").pack(anchor="w", padx=22)
        tk.Label(win, text="状态", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=22, pady=(12, 2))
        st_var = tk.StringVar(value=it.get("status", "想学") if it else "想学")
        ttk.Combobox(win, textvariable=st_var, values=["想学", "在学", "已学"],
                     width=12, state="readonly").pack(anchor="w", padx=22)
        tk.Label(win, text="备注", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w", padx=22, pady=(12, 2))
        note_t = tk.Text(win, height=3)
        note_t.pack(fill="x", padx=22)
        note_t.insert("1.0", it.get("note", "") if it else "")

        def ok():
            n = name_e.get().strip()
            if not n:
                messagebox.showwarning("提示", "请填写学习内容", parent=win)
                return
            if it:
                it.update({"name": n, "cat": cat_var.get(), "status": st_var.get(),
                           "note": note_t.get("1.0", "end-1c").strip()})
            else:
                self.data.setdefault("study_items", []).append({
                    "id": uuid.uuid4().hex[:8], "name": n, "cat": cat_var.get(),
                    "status": st_var.get(), "note": note_t.get("1.0", "end-1c").strip()})
            self.save()
            win.destroy()
            self.show("study")

        bar = tk.Frame(win, bg=C["card"]); bar.pack(pady=14)
        tk.Button(bar, text="保存", bg=C["main"], fg="white", bd=0, font=("Microsoft YaHei", 10),
                  padx=20, pady=6, command=ok).pack(side="left", padx=6)
        tk.Button(bar, text="取消", bg=C["light"], fg=C["dark"], bd=0, font=("Microsoft YaHei", 10),
                  padx=18, pady=6, command=win.destroy).pack(side="left", padx=6)

    def del_study_item(self, it):
        if messagebox.askyesno("确认", f"删除「{it.get('name','')}」？"):
            self.data["study_items"] = [x for x in self.data.get("study_items", [])
                                        if x.get("id") != it.get("id")]
            self.save()
            self.show("study")

    def start_pomo(self):
        if self.pomo_running:
            return
        try:
            self.pomo_left = int(float(self.st_min.get()) * 60)
        except Exception:
            self.pomo_left = 25 * 60
        self.pomo_running = True
        self.tick_pomo()

    def pause_pomo(self):
        self.pomo_running = False

    def reset_pomo(self):
        self.pomo_running = False
        self.pomo_left = 25 * 60
        if hasattr(self, "st_label") and self.st_label.winfo_exists():
            self.st_label.config(text="25:00")

    def tick_pomo(self):
        if not self.pomo_running:
            return
        if not (hasattr(self, "st_label") and self.st_label.winfo_exists()):
            self.pomo_running = False
            return
        m, s = divmod(max(0, self.pomo_left), 60)
        self.st_label.config(text=f"{m:02d}:{s:02d}")
        if self.pomo_left <= 0:
            self.pomo_running = False
            try:
                minutes = int(float(self.st_min.get()))
            except Exception:
                minutes = 25
            self.data.setdefault("study_log", []).append({
                "date": today_str(), "subject": self.st_sub.get(), "minutes": minutes,
                "cat": self.study_cat_of(self.st_sub.get())
            })
            self.save()
            try:
                self.root.bell()
            except Exception:
                pass
            messagebox.showinfo("⏱️ 番茄完成", f'已完成 {minutes} 分钟 {self.st_sub.get()} 学习，记入统计。')
            self.st_label.config(text="25:00")
            self.pomo_left = 25 * 60
            self.show("study")
            return
        self.pomo_left -= 1
        self.root.after(1000, self.tick_pomo)

    def manual_study(self):
        try:
            minutes = int(float(self.st_min.get()))
        except Exception:
            messagebox.showwarning("提示", "请填写有效分钟数")
            return
        self.data.setdefault("study_log", []).append({
            "date": today_str(), "subject": self.st_sub.get(), "minutes": minutes,
            "cat": self.study_cat_of(self.st_sub.get())
        })
        self.save()
        self.show("study")

    # ---------- 书单 ----------
    def p_books(self):
        inner = self.card("书单")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=4)
        tk.Label(r, text="书名:", bg=C["card"]).pack(side="left")
        self.bkt = tk.Entry(r, width=16); self.bkt.pack(side="left", padx=3)
        tk.Label(r, text="作者:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.bka = tk.Entry(r, width=10); self.bka.pack(side="left", padx=3)
        tk.Label(r, text="主题:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.bkcat = ttk.Combobox(r, values=["育儿", "理财", "易经", "养生", "心理", "工作", "其他"],
                                  width=6, state="readonly"); self.bkcat.set("其他"); self.bkcat.pack(side="left", padx=3)
        tk.Label(r, text="状态:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.bks = ttk.Combobox(r, values=["想读", "在读", "已读"], width=6, state="readonly")
        self.bks.set("想读"); self.bks.pack(side="left", padx=3)
        self.primary(r, "添加", self.add_book)
        self.bkl = tk.Frame(inner, bg=C["card"]); self.bkl.pack(fill="x", pady=4)
        self.refresh_book()

    def add_book(self):
        self.data["books"].append({
            "title": self.bkt.get().strip(), "author": self.bka.get().strip(),
            "category": self.bkcat.get(), "status": self.bks.get(),
            "rating": 0, "progress": 0, "note": ""
        })
        self.save()
        self.bkt.delete(0, tk.END); self.bka.delete(0, tk.END)
        self.refresh_book()

    def del_book(self, i):
        if messagebox.askyesno("确认", "删除此书？"):
            self.data["books"].pop(i)
            self.save()
            self.refresh_book()

    def refresh_book(self):
        for w in self.bkl.winfo_children():
            w.destroy()
        for i, b in enumerate(reversed(self.data["books"])):
            idx = len(self.data["books"]) - 1 - i
            row = tk.Frame(self.bkl, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=b.get("title", ""), bg=C["card"], width=18, anchor="w").pack(side="left", padx=5)
            tk.Label(row, text=b.get("category", ""), bg=C["card"], fg=C["muted"], width=5).pack(side="left")
            tk.Label(row, text=b.get("status", ""), bg=C["card"], width=5).pack(side="left")
            rating = int(b.get("rating", 0) or 0)
            tk.Label(row, text="★" * rating + "☆" * (5 - rating), bg=C["card"], fg="#F9A825", width=7).pack(side="left")
            tk.Label(row, text=f'{int(b.get("progress", 0) or 0)}%', bg=C["card"], fg=C["muted"], width=5).pack(side="left")
            tk.Button(row, text="编辑", bg=C["light"], fg=C["dark"], bd=0,
                      command=lambda idx=idx: self.edit_book(idx)).pack(side="right", padx=3)
            tk.Button(row, text="删除", bg=C["border"], bd=0,
                      command=lambda idx=idx: self.del_book(idx)).pack(side="right", padx=3)

    def edit_book(self, idx):
        b = self.data["books"][idx]
        win = tk.Toplevel(self.root)
        win.title("编辑书单")
        win.configure(bg=C["card"])
        win.geometry("420x320")
        tk.Label(win, text=b.get("title", ""), bg=C["card"], fg=C["dark"],
                 font=("Microsoft YaHei", 12, "bold")).pack(pady=8)
        f1 = tk.Frame(win, bg=C["card"]); f1.pack(fill="x", padx=16, pady=4)
        tk.Label(f1, text="评分(1-5):", bg=C["card"]).pack(side="left")
        rating = tk.Entry(f1, width=5); rating.insert(0, str(b.get("rating", 0))); rating.pack(side="left", padx=4)
        tk.Label(f1, text="进度(%):", bg=C["card"]).pack(side="left", padx=(10, 0))
        prog = tk.Entry(f1, width=5); prog.insert(0, str(b.get("progress", 0))); prog.pack(side="left", padx=4)
        f2 = tk.Frame(win, bg=C["card"]); f2.pack(fill="x", padx=16, pady=4)
        tk.Label(f2, text="状态:", bg=C["card"]).pack(side="left")
        st = ttk.Combobox(f2, values=["想读", "在读", "已读"], width=8, state="readonly")
        st.set(b.get("status", "想读")); st.pack(side="left", padx=4)
        tk.Label(win, text="读书笔记", bg=C["card"]).pack(anchor="w", padx=16, pady=(6, 0))
        note = tk.Text(win, height=8); note.pack(fill="both", expand=True, padx=16, pady=4)
        note.insert("1.0", b.get("note", ""))
        def save():
            try:
                b["rating"] = max(0, min(5, int(float(rating.get()))))
                b["progress"] = max(0, min(100, int(float(prog.get()))))
            except Exception:
                pass
            b["status"] = st.get()
            b["note"] = note.get("1.0", "end-1c")
            self.save()
            win.destroy()
            self.refresh_book()
        tk.Button(win, text="保存", bg=C["main"], fg="white", bd=0,
                  command=save).pack(pady=8)

    # ---------- 素材库 ----------
    def p_material(self):
        inner = self.card("素材库（妈妈瞬间 / AI 场景 / 灵感）")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=4)
        tk.Label(r, text="类型:", bg=C["card"]).pack(side="left")
        self.mt_type = ttk.Combobox(r, values=["妈妈瞬间", "AI场景", "灵感", "其他"],
                                    width=8, state="readonly"); self.mt_type.set("妈妈瞬间"); self.mt_type.pack(side="left", padx=4)
        tk.Label(r, text="内容:", bg=C["card"]).pack(side="left", padx=(8, 0))
        self.mt_text = tk.Entry(r, width=52); self.mt_text.pack(side="left", padx=4, fill="x", expand=True)
        self.primary(r, "添加", self.add_material)

        filt = tk.Frame(inner, bg=C["card"]); filt.pack(fill="x", pady=2)
        tk.Label(filt, text="筛选:", bg=C["card"]).pack(side="left")
        self.mt_filter = ttk.Combobox(filt, values=["全部", "妈妈瞬间", "AI场景", "灵感", "其他"],
                                      width=8, state="readonly"); self.mt_filter.set("全部")
        self.mt_filter.pack(side="left", padx=4)
        self.mt_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_material())
        self.mt_list = tk.Frame(inner, bg=C["card"]); self.mt_list.pack(fill="x", pady=4)
        self.refresh_material()

    def add_material(self):
        t = self.mt_text.get().strip()
        if not t:
            return
        self.data.setdefault("materials", []).append({
            "type": self.mt_type.get(), "text": t, "date": today_str()
        })
        self.save()
        self.mt_text.delete(0, tk.END)
        self.refresh_material()

    def del_material(self, i):
        if messagebox.askyesno("确认", "删除这条素材？"):
            self.data["materials"].pop(i)
            self.save()
            self.refresh_material()

    def refresh_material(self):
        for w in self.mt_list.winfo_children():
            w.destroy()
        sel = self.mt_filter.get() if hasattr(self, "mt_filter") else "全部"
        items = self.data.get("materials", [])
        shown = [(i, m) for i, m in enumerate(items) if sel == "全部" or m.get("type") == sel]
        if not shown:
            tk.Label(self.mt_list, text="暂无素材。", bg=C["card"], fg=C["muted"]).pack(anchor="w")
            return
        for i, m in reversed(shown):
            row = tk.Frame(self.mt_list, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=m.get("date", "")[5:], bg=C["card"], fg=C["muted"], width=6).pack(side="left", padx=4)
            tk.Label(row, text=m.get("type", ""), bg=C["light"], fg=C["dark"], width=8).pack(side="left", padx=3)
            tk.Label(row, text=m.get("text", ""), bg=C["card"], anchor="w").pack(side="left", fill="x", expand=True, padx=5)
            tk.Button(row, text="删除", bg=C["border"], bd=0,
                      command=lambda i=i: self.del_material(i)).pack(side="right", padx=4)

    # ---------- 自媒体发布打卡 ----------
    def p_publish(self):
        wk = week_key()
        pub = self.data.setdefault("publish", {}).setdefault(wk, {"b": 0, "a": 0})
        inner = self.card(f"本周发布进度（{wk}）")
        for key, name, target in [("b", "B号 重建日记（主）", 4), ("a", "A号 AI+审计（维持）", 2)]:
            row = tk.Frame(inner, bg=C["card"]); row.pack(fill="x", pady=6)
            tk.Label(row, text=name, bg=C["card"], fg=C["dark"],
                     font=("Microsoft YaHei", 10, "bold"), width=24, anchor="w").pack(side="left")
            tk.Button(row, text="−", bg=C["light"], fg=C["dark"], bd=0, width=3,
                      command=lambda k=key: self.pub_change(k, -1)).pack(side="left", padx=3)
            tk.Label(row, text=f'{pub.get(key, 0)} / {target}', bg=C["card"],
                     fg=C["main"], font=("Microsoft YaHei", 12, "bold"), width=8).pack(side="left")
            tk.Button(row, text="＋", bg=C["main"], fg="white", bd=0, width=3,
                      command=lambda k=key: self.pub_change(k, 1)).pack(side="left", padx=3)
            state = "✅ 已完成" if pub.get(key, 0) >= target else "还差 %d 条" % (target - pub.get(key, 0))
            tk.Label(row, text=state, bg=C["card"], fg=C["muted"]).pack(side="left", padx=10)

        inner2 = self.card("本周排期（来自双号方案）")
        rows = [
            ("周一", "A号·抖音", "事务所带AI小组，最难的三件事"),
            ("周二", "B号·小红书", "S1 孩子刚上幼儿园，我想把这一年记下来"),
            ("周三", "B号·抖音", "S1 同题口播版"),
            ("周四", "B号·小红书", "S2 送园不回头，我练了30天"),
            ("周五", "A号·小红书", "事务所带AI小组，最难的三件事"),
            ("周六", "B号·小红书", "P1 睡前三行小练习卡"),
        ]
        for w, tag, txt in rows:
            row = tk.Frame(inner2, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=w, bg=C["card"], fg=C["dark"], width=5, font=("Microsoft YaHei", 9, "bold")).pack(side="left", padx=5)
            tk.Label(row, text=tag, bg=C["light"], fg=C["dark"], width=12).pack(side="left", padx=3)
            tk.Label(row, text=txt, bg=C["card"], anchor="w").pack(side="left", fill="x", expand=True, padx=5)

        inner3 = self.card("合规红线提醒")
        tk.Label(inner3, text="不露孩子正脸；不报幼儿园名、小区、地址、全名；两号不互关、不互赞、不互相提及；B号不提AI/审计/事务所；A号不提家庭。",
                 bg=C["card"], fg=C["text"], wraplength=820, justify="left").pack(anchor="w")

    def pub_change(self, key, delta):
        wk = week_key()
        pub = self.data.setdefault("publish", {}).setdefault(wk, {"b": 0, "a": 0})
        pub[key] = max(0, pub.get(key, 0) + delta)
        self.save()
        self.show("publish")

    # ---------- 待办事项 ----------
    def p_todos(self):
        inner = self.card("待办事项")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=4)
        self.ti = tk.Entry(r, width=40)
        self.ti.pack(side="left", padx=4)
        self.ti.bind("<Return>", lambda e: self.add_todo())
        self.primary(r, "添加", self.add_todo)
        self.tl = tk.Frame(inner, bg=C["card"]); self.tl.pack(fill="x", pady=4)
        self.refresh_todo()

    def add_todo(self):
        t = self.ti.get().strip()
        if t:
            self.data.setdefault("todos", []).append({"text": t, "done": False})
            self.save()
            self.ti.delete(0, tk.END)
            self.refresh_todo()

    def del_todo(self, i):
        if messagebox.askyesno("确认", "删除此待办？"):
            self.data["todos"].pop(i)
            self.save()
            self.refresh_todo()

    def toggle_todo(self, i):
        self.data["todos"][i]["done"] = not self.data["todos"][i]["done"]
        self.save()
        self.refresh_todo()

    def refresh_todo(self):
        for w in self.tl.winfo_children():
            w.destroy()
        for i, t in enumerate(self.data.get("todos", [])):
            row = tk.Frame(self.tl, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            row.pack(fill="x", pady=2)
            var = tk.BooleanVar(value=t["done"])
            tk.Checkbutton(row, bg=C["card"], variable=var,
                           command=lambda i=i: self.toggle_todo(i)).pack(side="left", padx=6)
            tk.Label(row, text=("☑ " if t["done"] else "") + t["text"],
                     bg=C["card"], anchor="w").pack(side="left", fill="x", expand=True, padx=4)
            tk.Button(row, text="删除", bg=C["border"], bd=0,
                      command=lambda i=i: self.del_todo(i)).pack(side="right", padx=4)

    # ---------- 随笔 ----------
    def p_notes(self):
        inner = self.card("随笔备忘")
        self.nt = tk.Text(inner, width=70, height=20); self.nt.pack(fill="both", expand=True, pady=4)
        self.nt.insert("1.0", self.data.get("notes", ""))
        self.primary(inner, "保存随笔", self.save_notes)

    def save_notes(self):
        self.data["notes"] = self.nt.get("1.0", "end-1c")
        self.save()
        messagebox.showinfo("提示", "随笔已保存")

    # ---------- 全局搜索 ----------
    def p_search(self):
        inner = self.card("搜索全部记录")
        r = tk.Frame(inner, bg=C["card"]); r.pack(fill="x", pady=4)
        self.sq = tk.Entry(r, width=40); self.sq.pack(side="left", padx=4)
        self.sq.bind("<Return>", lambda e: self.do_search())
        self.primary(r, "搜索", self.do_search)
        self.sr = tk.Text(inner, width=80, height=22)
        self.sr.pack(fill="both", expand=True, pady=6)

    def do_search(self):
        q = self.sq.get().strip()
        self.sr.delete("1.0", tk.END)
        if not q:
            return
        out = []
        for ds, txt in self.data.get("daily_logs", {}).items():
            if q in str(txt):
                out.append(f"[日历] {ds}\n{str(txt)[:200]}")
        if q in self.data.get("notes", ""):
            out.append("[随笔]\n" + self.data["notes"][:300])
        for m in self.data.get("materials", []):
            if q in m.get("text", ""):
                out.append(f'[素材] {m.get("date","")} {m.get("type","")}\n{m.get("text","")}')
        for b in self.data.get("books", []):
            if q in b.get("title", "") or q in b.get("note", ""):
                out.append(f'[书单] {b.get("title","")}｜{b.get("status","")}\n{b.get("note","")[:150]}')
        for t in self.data.get("todos", []):
            if q in t.get("text", ""):
                out.append(f'[待办] {"已完成" if t.get("done") else "未完成"}：{t.get("text","")}')
        for d in self.data.get("diet_records", []):
            if q in d.get("food", ""):
                out.append(f'[饮食] {d.get("date","")} {d.get("meal","")}：{d.get("food","")}')
        for r in self.data.get("reminders", []):
            if q in r.get("text", ""):
                out.append(f'[提醒] {r.get("time","")} {r.get("text","")}（{r.get("repeat","")}）')
        self.sr.insert("1.0", f"找到 {len(out)} 条结果：\n\n" + "\n\n".join(out) if out else "没有找到相关记录。")

    # ---------- 设置 ----------
    def p_settings(self):
        inner0 = self.card("🎨 配色")
        tk.Label(inner0, text="点一下立刻换，会记住你的选择。", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(0, 6))
        pick = tk.Frame(inner0, bg=C["card"]); pick.pack(fill="x")
        cur = self.data.get("settings", {}).get("theme", "morandi_blue")
        for key, t in THEMES.items():
            box = tk.Frame(pick, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)
            box.pack(side="left", padx=(0, 8))
            on = (key == cur)
            sw = tk.Frame(box, bg=t["dot"], height=26, width=74,
                          highlightthickness=2,
                          highlightbackground=C["dark"] if on else t["dot"])
            sw.pack(padx=3, pady=(3, 0))
            sw.pack_propagate(False)
            tk.Button(box, text=t["label"] + ("　✓" if on else ""), bg=C["card"],
                      fg=C["dark"] if on else C["text"], bd=0, relief="flat",
                      font=("Microsoft YaHei", 8),
                      command=lambda k=key: self.set_theme(k)).pack(fill="x", padx=2, pady=2)

        inner = self.card("数据与备份")
        tk.Label(inner, text=f"数据文件：{DATA}", bg=C["card"], fg=C["muted"],
                 font=("Microsoft YaHei", 8)).pack(anchor="w", pady=2)
        bar = tk.Frame(inner, bg=C["card"]); bar.pack(fill="x", pady=4)
        self.primary(bar, "立即备份", self.do_backup)
        self.link(bar, "打开备份文件夹", self.open_backup_dir)
        self.link(bar, "从备份恢复", self.restore_backup)
        self.link(bar, "导出 CSV", self.export_csv)

        bar2 = tk.Frame(inner, bg=C["card"]); bar2.pack(fill="x", pady=(2, 4))
        self.primary(bar2, "推送数据到网站（手机同步）", self.push_web_data)
        tk.Label(inner, text="推送后，手机版「我的 → 拉取电脑数据」即可拿到电脑的最新数据。\n"
                             "注意：数据会上传到 GitHub 网页（公开网址），不要推含敏感信息的记录。",
                 bg=C["card"], fg=C["muted"], justify="left",
                 font=("Microsoft YaHei", 8)).pack(anchor="w", pady=2)

        inner2 = self.card("提醒与启动")
        r = tk.Frame(inner2, bg=C["card"]); r.pack(fill="x", pady=3)
        st = self.data.get("settings", {})
        self.autostart_var = tk.BooleanVar(value=st.get("autostart", False))
        tk.Checkbutton(r, text="开机自动启动（保证提醒不断）", variable=self.autostart_var,
                       bg=C["card"], command=self.apply_autostart).pack(side="left")
        r2 = tk.Frame(inner2, bg=C["card"]); r2.pack(fill="x", pady=3)
        self.evening_var = tk.BooleanVar(value=st.get("evening_enabled", True))
        tk.Checkbutton(r2, text="晚间收尾提醒", variable=self.evening_var,
                       bg=C["card"], command=self.save_settings).pack(side="left")
        self.evening_time = tk.Entry(r2, width=6)
        self.evening_time.insert(0, st.get("evening_time", "21:30"))
        self.evening_time.pack(side="left", padx=6)
        self.link(r2, "保存", self.save_settings)
        tk.Label(inner2, text="提醒依赖程序运行；建议同时用手机系统日历（导出的日程）做兜底。",
                 bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(4, 0))

        inner3 = self.card("📱 手机同步（iPhone 日历）")
        tk.Label(inner3, text="导出一个 .ics 文件，用微信/邮件发到 iPhone，点开后「添加到日历」，"
                              "系统会在到点时弹提醒，不需要电脑开着。",
                 bg=C["card"], fg=C["muted"], wraplength=800, justify="left",
                 font=("Microsoft YaHei", 9)).pack(anchor="w", pady=(0, 4))
        bar3 = tk.Frame(inner3, bg=C["card"]); bar3.pack(fill="x", pady=2)
        self.primary(bar3, "导出手机日历(.ics)", self.export_ics)
        self.link(bar3, "导出数据给手机(.json)", self.export_data_file)
        self.link(bar3, "打开手机版文件夹", self.open_mobile_dir)
        tk.Label(inner3, text="包含：定时提醒、周计划的固定任务、倒计时。重复提醒会在日历里自动重复。",
                 bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(4, 0))
        tk.Label(inner3, text="数据文件发到 iPhone 后，在手机版「我的 → 从备份恢复」导入，两边内容就一致了。",
                 bg=C["card"], fg=C["muted"], font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(2, 0))

    def save_settings(self):
        s = self.data.setdefault("settings", {})
        s["evening_enabled"] = self.evening_var.get()
        t = self.evening_time.get().strip()
        try:
            datetime.strptime(t, "%H:%M")
            s["evening_time"] = t
        except Exception:
            messagebox.showwarning("提示", "晚间提醒时间格式 HH:MM")
            return
        self.save()
        messagebox.showinfo("提示", "设置已保存")

    def apply_autostart(self):
        enable = self.autostart_var.get()
        try:
            startup = os.path.join(os.environ["APPDATA"],
                                   r"Microsoft\Windows\Start Menu\Programs\Startup")
            bat = os.path.join(startup, "个人工作台.bat")
            if enable:
                if getattr(sys, "frozen", False):
                    cmd = f'@echo off\r\nstart "" "{sys.executable}"\r\n'
                else:
                    cmd = f'@echo off\r\nstart "" pythonw "{os.path.abspath(__file__)}"\r\n'
                with open(bat, "w", encoding="gbk") as f:
                    f.write(cmd)
            else:
                if os.path.exists(bat):
                    os.remove(bat)
            self.data["settings"]["autostart"] = enable
            self.save()
            messagebox.showinfo("提示", "开机自启已" + ("开启" if enable else "关闭"))
        except Exception as e:
            messagebox.showerror("错误", f"设置失败：{e}")

    def do_backup(self):
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            target = os.path.join(BACKUP_DIR,
                                  f"workbench_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            shutil.copy2(DATA, target)
            messagebox.showinfo("提示", f"已备份到：\n{target}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def open_backup_dir(self):
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            os.startfile(BACKUP_DIR)
        except Exception:
            messagebox.showinfo("提示", BACKUP_DIR)

    def restore_backup(self):
        f = filedialog.askopenfilename(initialdir=BACKUP_DIR if os.path.exists(BACKUP_DIR) else BASE_DIR,
                                       title="选择备份文件", filetypes=[("JSON", "*.json")])
        if not f:
            return
        if not messagebox.askyesno("确认", "恢复会覆盖当前数据，确定继续？"):
            return
        try:
            shutil.copy2(f, DATA)
            self.load()
            messagebox.showinfo("提示", "已恢复，请重新打开程序以完全生效。")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def push_web_data(self):
        """把电脑数据推送到 GitHub 网站，手机版可一键拉取。"""
        pub = os.path.join(BASE_DIR, "发布")
        if not os.path.isdir(pub):
            messagebox.showerror("推送数据", "没找到「发布」文件夹：\n" + pub)
            return
        try:
            shutil.copyfile(DATA, os.path.join(pub, "sync.json"))
        except Exception as e:
            messagebox.showerror("推送数据", "复制数据失败：\n" + str(e))
            return
        import subprocess
        try:
            subprocess.run(["git", "add", "sync.json"], cwd=pub, timeout=60, capture_output=True)
            subprocess.run(["git", "commit", "-m", "数据更新"], cwd=pub, timeout=60, capture_output=True)
            r = subprocess.run(["git", "push"], cwd=pub, timeout=180, capture_output=True)
            if r.returncode == 0:
                messagebox.showinfo(
                    "推送数据",
                    "已推送到网站，约 1 分钟内生效。\n\n"
                    "手机上：我的 → 拉取电脑数据\n"
                    "（会用电脑数据覆盖手机数据，请先确认电脑是最新的）")
            else:
                messagebox.showerror("推送数据", "推送失败，网络不稳时稍后重试即可。")
        except Exception as e:
            messagebox.showerror("推送数据", "推送失败：\n" + str(e))

    def open_mobile_dir(self):
        d = os.path.join(BASE_DIR, "手机版")
        try:
            if not os.path.isdir(d):
                os.makedirs(d, exist_ok=True)
            os.startfile(d)
        except Exception:
            messagebox.showinfo("提示", "手机版文件夹：" + d)

    def export_data_file(self):
        f = filedialog.asksaveasfilename(
            title="导出数据给手机", defaultextension=".json",
            initialfile=f"工作台数据_{today_str()}.json",
            filetypes=[("JSON", "*.json")])
        if not f:
            return
        try:
            self.save()
            shutil.copy2(DATA, f)
            messagebox.showinfo("提示", f"已导出：\n{f}\n\n发到 iPhone，用手机版「我的 → 从备份恢复」导入。")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def export_ics(self):
        def esc(s):
            s = str(s if s is not None else "")
            return (s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
                     .replace("\r", "").replace("\n", "\\n"))

        def fold(line):
            out, cur, limit = [], "", 73
            for ch in line:
                if len((cur + ch).encode("utf-8")) > limit:
                    out.append(cur)
                    cur = " " + ch
                else:
                    cur += ch
            out.append(cur)
            return "\r\n".join(out)

        now = datetime.now()
        stamp = now.strftime("%Y%m%dT%H%M%S")
        ls = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Personal Workbench//CN",
              "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
              "X-WR-CALNAME:个人工作台", "X-WR-TIMEZONE:Asia/Shanghai"]
        seq = [0]

        def add(summary, start, end=None, rrule=None, alarm_min=None, all_day=False):
            seq[0] += 1
            ls.append("BEGIN:VEVENT")
            ls.append(f"UID:wb-{stamp}-{seq[0]}@local")
            ls.append(f"DTSTAMP:{stamp}")
            if all_day:
                ls.append(f"DTSTART;VALUE=DATE:{start}")
                if end:
                    ls.append(f"DTEND;VALUE=DATE:{end}")
            else:
                ls.append(f"DTSTART:{start}")
                if end:
                    ls.append(f"DTEND:{end}")
            if rrule:
                ls.append(f"RRULE:{rrule}")
            ls.append("SUMMARY:" + esc(summary))
            if alarm_min is not None:
                ls.extend(["BEGIN:VALARM", "ACTION:DISPLAY",
                           f"TRIGGER:-PT{max(0, int(alarm_min))}M",
                           "DESCRIPTION:" + esc(summary), "END:VALARM"])
            ls.append("END:VEVENT")

        wd_map = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
        today = now.date()
        today_s = today.strftime("%Y%m%d")

        # 1) 定时提醒
        for r in self.data.get("reminders", []):
            if not r.get("enabled", True):
                continue
            try:
                hh, mm = [int(x) for x in r.get("time", "09:00").split(":")]
            except Exception:
                continue
            adv = int(r.get("advance", 0) or 0)
            rep = r.get("repeat", "每天")
            text = r.get("text", "") or "提醒"
            if rep == "每天":
                start = f"{today_s}T{hh:02d}{mm:02d}00"
                add(text, start, rrule="FREQ=DAILY", alarm_min=adv)
            elif rep == "仅一次":
                try:
                    d = datetime.strptime(r.get("date", ""), "%Y-%m-%d").date()
                except Exception:
                    continue
                add(text, d.strftime("%Y%m%d") + f"T{hh:02d}{mm:02d}00", alarm_min=adv)
            elif rep.startswith("每周") and rep[-1] in WEEKDAYS:
                idx = WEEKDAYS.index(rep[-1])
                delta = (idx - today.weekday()) % 7
                d = today + timedelta(days=delta)
                add(text, d.strftime("%Y%m%d") + f"T{hh:02d}{mm:02d}00",
                    rrule=f"FREQ=WEEKLY;BYDAY={wd_map[idx]}", alarm_min=adv)

        # 2) 周计划模板（按星期，全天）
        for k, tasks in self.data.get("weekly_template", {}).items():
            try:
                idx = int(k)
            except Exception:
                continue
            if not (0 <= idx <= 6) or not tasks:
                continue
            delta = (idx - today.weekday()) % 7
            d = today + timedelta(days=delta)
            d2 = d + timedelta(days=1)
            add(f"周{WEEKDAYS[idx]}计划：" + "；".join(tasks),
                d.strftime("%Y%m%d"), d2.strftime("%Y%m%d"),
                rrule=f"FREQ=WEEKLY;BYDAY={wd_map[idx]}", all_day=True)

        # 3) 倒计时（全天，提前一天提醒）
        for c in self.data.get("countdowns", []):
            try:
                d = datetime.strptime(c.get("date", ""), "%Y-%m-%d").date()
            except Exception:
                continue
            add(c.get("name", "") or "倒计时", d.strftime("%Y%m%d"),
                (d + timedelta(days=1)).strftime("%Y%m%d"), all_day=True, alarm_min=900)

        ls.append("END:VCALENDAR")
        content = "\r\n".join(fold(x) for x in ls) + "\r\n"
        f = filedialog.asksaveasfilename(
            title="保存手机日历文件", defaultextension=".ics",
            initialfile=f"个人工作台日程_{today_s}.ics",
            filetypes=[("日历文件", "*.ics")])
        if not f:
            return
        try:
            with open(f, "w", encoding="utf-8", newline="") as fp:
                fp.write(content)
            messagebox.showinfo("提示", f"已导出：\n{f}\n\n把它发到 iPhone，点开后选「添加到日历」。")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def export_csv(self):
        d = filedialog.askdirectory(title="选择导出文件夹")
        if not d:
            return
        try:
            with open(os.path.join(d, "weight.csv"), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f); w.writerow(["日期", "体重(kg)"])
                for r in self.data.get("weight_records", []):
                    w.writerow([r.get("date", ""), r.get("weight", "")])
            with open(os.path.join(d, "diet.csv"), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f); w.writerow(["日期", "餐次", "内容"])
                for r in self.data.get("diet_records", []):
                    w.writerow([r.get("date", ""), r.get("meal", ""), r.get("food", "")])
            with open(os.path.join(d, "study.csv"), "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f); w.writerow(["日期", "科目", "分钟"])
                for r in self.data.get("study_log", []):
                    w.writerow([r.get("date", ""), r.get("subject", ""), r.get("minutes", "")])
            messagebox.showinfo("提示", f"已导出到：\n{d}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
