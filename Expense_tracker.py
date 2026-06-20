import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import re


# DATABASE   


def connect_db():
    conn = sqlite3.connect("expenses.db")
    cur = conn.cursor()
    return conn, cur


def create_tables():
    conn, cur = connect_db()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            monthly_budget REAL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL
        )
    """)

    conn.commit()
    conn.close()



# AUTH   


def register(u, p):
    conn, cur = connect_db()
    try:
        cur.execute("INSERT INTO users(username,password) VALUES(?,?)", (u, p))
        conn.commit()
        return True, "Account created successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists. Choose another."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()


def login(u, p):
    conn, cur = connect_db()
    cur.execute("SELECT id FROM users WHERE username=? AND password=?", (u, p))
    user = cur.fetchone()
    conn.close()
    return user[0] if user else None



# EXPENSE FUNCTIONS  


def add_expense(uid, d, c, desc, amt):
    conn, cur = connect_db()
    cur.execute("""
        INSERT INTO expenses(user_id,date,category,description,amount)
        VALUES(?,?,?,?,?)
    """, (uid, d, c, desc, amt))
    conn.commit()
    conn.close()


def fetch_all(uid):
    conn, cur = connect_db()
    cur.execute("""
        SELECT id,date,category,description,amount
        FROM expenses
        WHERE user_id=?
        ORDER BY id DESC
    """, (uid,))
    data = cur.fetchall()
    conn.close()
    return data


def total(uid):
    conn, cur = connect_db()
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=?", (uid,))
    t = cur.fetchone()[0]
    conn.close()
    return t


def delete(exp_id):
    conn, cur = connect_db()
    cur.execute("DELETE FROM expenses WHERE id=?", (exp_id,))
    conn.commit()
    conn.close()


def update(exp_id, d, c, desc, amt):
    conn, cur = connect_db()
    cur.execute("""
        UPDATE expenses
        SET date=?, category=?, description=?, amount=?
        WHERE id=?
    """, (d, c, desc, amt, exp_id))
    conn.commit()
    conn.close()


def search(uid, keyword):
    conn, cur = connect_db()
    cur.execute("""
        SELECT id,date,category,description,amount
        FROM expenses
        WHERE user_id=? AND category LIKE ?
    """, (uid, "%" + keyword + "%"))
    data = cur.fetchall()
    conn.close()
    return data

# BUDGET SYSTEM + SMART ADVISOR  

def set_budget(uid, amount):
    conn, cur = connect_db()
    cur.execute("UPDATE users SET monthly_budget=? WHERE id=?", (amount, uid))
    conn.commit()
    conn.close()


def get_budget(uid):
    conn, cur = connect_db()
    cur.execute("SELECT COALESCE(monthly_budget,0) FROM users WHERE id=?", (uid,))
    b = cur.fetchone()[0]
    conn.close()
    return b


def smart_budget_advisor(uid):
    b = get_budget(uid)
    t = total(uid)

    print("\n========== SMART BUDGET ADVISOR ==========")

    if b == 0:
        print("No budget set. Set budget to get insights.")
        return

    remaining = b - t
    percent = (t / b) * 100

    print(f"Budget     : Rs {b}")
    print(f"Spent      : Rs {t}")
    print(f"Remaining  : Rs {remaining}")

    if t > b:
        print("ALERT: You are OVER BUDGET!")
        print("Advice: Stop unnecessary spending immediately.")
    elif percent >= 90:
        print("WARNING: 90% budget used!")
        print("Advice: Reduce shopping & luxury expenses.")
    elif percent >= 70:
        print("Caution: More than 70% used.")
        print("Advice: Control spending for rest of month.")
    else:
        print("Good: Spending is under control.")


def show_table(data):
    print("\n====================================================")
    print("ID | DATE       | CATEGORY   | DESCRIPTION   | AMOUNT")
    print("====================================================")
    for r in data:
        print(f"{r[0]:<2} | {r[1]:<10} | {r[2]:<10} | {r[3]:<12} | Rs {r[4]}")
    print("====================================================\n")



#PALETTE & TYPOGRAPHY


BG_DEEP       = "#F4F1EA"
BG_SURFACE    = "#FFFFFF"
BG_ELEVATED   = "#F7F4ED"
BORDER        = "#E3DDD0"
ACCENT        = "#0E7C7B"
ACCENT_GLOW   = "#DCEFEE"
GREEN         = "#2F9E5B"
RED           = "#E2543D"
ORANGE        = "#E8A53D"
PURPLE        = "#8E5BC4"
TEXT_PRIMARY  = "#2B2620"
TEXT_SECONDARY= "#7A7266"
TEXT_INVERSE  = "#FFFFFF"

F_HEADLINE  = ("Segoe UI", 22, "bold")
F_TITLE     = ("Segoe UI", 16, "bold")
F_SUBTITLE  = ("Segoe UI", 11)
F_BODY      = ("Segoe UI", 11)
F_LABEL     = ("Segoe UI", 8, "bold")
F_NAV       = ("Segoe UI", 11, "bold")
F_STAT      = ("Segoe UI", 26, "bold")
F_MONO      = ("Consolas", 11)

CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment",
               "Health", "Education", "Rent", "Travel", "Other"]

CATEGORY_ICONS = {
    "Food": "🍽", "Transport": "🚗", "Shopping": "🛍",
    "Bills": "📋", "Entertainment": "🎬", "Health": "💊",
    "Education": "📚", "Rent": "🏠", "Travel": "✈", "Other": "📦"
}


def get_advisor_status(uid):
    b = get_budget(uid)
    t = total(uid)
    if b == 0:
        return ("No budget set", "Add a monthly budget to unlock spending insights.", TEXT_SECONDARY, 0)
    remaining = b - t
    percent = (t / b) * 100
    if t > b:
        return ("Over Budget", "Stop unnecessary spending immediately.", RED, min(percent, 100))
    elif percent >= 90:
        return ("Critical — 90% Used", "Reduce shopping & luxury expenses now.", RED, percent)
    elif percent >= 70:
        return ("Caution — 70% Used", "Control spending for the rest of the month.", ORANGE, percent)
    else:
        return ("On Track", "Your spending is well within budget.", GREEN, percent)


# ── VALIDATION  
def validate_date(s):
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return False
    try:
        year, month, day = map(int, s.split("-"))
        date(year, month, day)
        return True
    except ValueError:
        return False


def validate_amount(s):
    try:
        v = float(s)
        if v <= 0:
            return False, None
        return True, v
    except ValueError:
        return False, None


# ── WIDGET HELPERS
def _entry(parent, width=32, show=None, font=F_BODY):
    kw = dict(font=font, relief="flat", bg=BG_ELEVATED, fg=TEXT_PRIMARY,
              insertbackground=ACCENT, highlightthickness=1,
              highlightbackground=BORDER, highlightcolor=ACCENT, width=width)
    if show:
        kw["show"] = show
    e = tk.Entry(parent, **kw)
    # Focus highlight effect
    e.bind("<FocusIn>",  lambda ev: e.config(highlightbackground=ACCENT, bg="#EEF9F8"))
    e.bind("<FocusOut>", lambda ev: e.config(highlightbackground=BORDER, bg=BG_ELEVATED))
    return e


def _label(parent, text, font=F_BODY, fg=TEXT_PRIMARY, bg=None, **kw):
    bg = bg or _get_bg(parent)
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)


def _get_bg(widget):
    try:
        return widget.cget("bg")
    except Exception:
        return BG_SURFACE


def _shade(hex_color, amt):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#" + hex_color
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r = max(0, min(255, r + amt))
    g = max(0, min(255, g + amt))
    b = max(0, min(255, b + amt))
    return f"#{r:02x}{g:02x}{b:02x}"


def _btn(parent, text, command, bg=ACCENT, fg=TEXT_INVERSE, font=F_NAV,
         padx=20, pady=10, radius=8, **kw):
    tmp = tk.Label(parent, text=text, font=font)
    tmp.update_idletasks()
    text_w = tmp.winfo_reqwidth()
    text_h = tmp.winfo_reqheight()
    tmp.destroy()

    w = text_w + padx * 2
    h = text_h + pady * 2
    host_bg = _get_bg(parent)

    canvas = tk.Canvas(parent, width=w, height=h, bg=host_bg,
                       highlightthickness=0, cursor="hand2")

    state = {"bg": bg, "fg": fg, "text": text, "cmd": command}

    def _round_rect(x1, y1, x2, y2, r, **opts):
        r = min(r, (y2 - y1) / 2, (x2 - x1) / 2)
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **opts)

    def render(fill_color):
        canvas.delete("all")
        cw = canvas.winfo_width() or w
        ch = canvas.winfo_height() or h
        _round_rect(1, 1, cw - 1, ch - 1, radius, fill=fill_color, outline="")
        canvas.create_text(cw / 2, ch / 2, text=state["text"],
                           font=font, fill=state["fg"])

    render(bg)
    canvas.bind("<Configure>", lambda e: render(state["bg"]))
    canvas.bind("<Enter>",         lambda e: render(_shade(state["bg"],  16)))
    canvas.bind("<Leave>",         lambda e: render(state["bg"]))
    canvas.bind("<ButtonPress-1>", lambda e: render(_shade(state["bg"], -18)))
    canvas.bind("<ButtonRelease-1>", lambda e: [render(_shade(state["bg"], 16)),
                                                 state["cmd"]() if state["cmd"] else None])

    def configure(**opts):
        if "text"    in opts: state["text"] = opts["text"]
        if "command" in opts: state["cmd"]  = opts["command"]
        if "bg"      in opts: state["bg"]   = opts["bg"]
        if "fg"      in opts: state["fg"]   = opts["fg"]
        render(state["bg"])

    canvas.config     = configure
    canvas.configure  = configure
    return canvas


def _divider(parent, bg=BORDER):
    return tk.Frame(parent, bg=bg, height=1)


def _card(parent, padx=24, pady=20, **kw):
    return tk.Frame(parent, bg=BG_SURFACE,
                    highlightbackground=BORDER, highlightthickness=1,
                    padx=padx, pady=pady, **kw)


# ── TOAST 

class ToastNotification:
    def __init__(self, root):
        self.root = root
        self._job = None
        self._win = None

    def show(self, message, color=GREEN, duration=3000):
        if self._win is not None and self._win.winfo_exists():
            self._win.destroy()
        if self._job:
            self.root.after_cancel(self._job)

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        try:
            win.attributes("-alpha", 0.0)
        except Exception:
            pass

        # Nicer toast layout
        outer = tk.Frame(win, bg=BG_SURFACE,
                         highlightbackground=color, highlightthickness=2)
        outer.pack()

        accent_bar = tk.Frame(outer, bg=color, width=4)
        accent_bar.pack(side="left", fill="y")

        inner = tk.Frame(outer, bg=BG_SURFACE, padx=16, pady=12)
        inner.pack(side="left")

        # Icon + message on same line
        icon = "✅" if color == GREEN else ("❌" if color == RED else "ℹ️")
        tk.Label(inner, text=f"{icon}  {message}",
                 font=("Segoe UI", 10), bg=BG_SURFACE,
                 fg=TEXT_PRIMARY, wraplength=320, justify="left").pack(anchor="w")

        self.root.update_idletasks()
        win.update_idletasks()
        ww = win.winfo_reqwidth()
        wh = win.winfo_reqheight()
        sw = self.root.winfo_width()
        sh = self.root.winfo_height()
        x  = self.root.winfo_x() + sw - ww - 20
        y_final = self.root.winfo_y() + sh - wh - 20
        y_start = y_final + 40
        win.geometry(f"+{x}+{y_start}")
        self._win = win

        steps = 12

        def animate(i=0):
            if not win.winfo_exists():
                return
            frac = i / steps
            try:
                win.attributes("-alpha", frac)
            except Exception:
                pass
            y = int(y_start + (y_final - y_start) * frac)
            win.geometry(f"+{x}+{y}")
            if i < steps:
                win.after(14, lambda: animate(i + 1))

        animate()
        self._job = self.root.after(duration,
            lambda: win.destroy() if win.winfo_exists() else None)


# ── PROGRESS BAR ─────────────────────────────────────────────

class ProgressBar(tk.Canvas):
    def __init__(self, parent, height=8, bg=BG_ELEVATED, fill=ACCENT, **kw):
        super().__init__(parent, height=height, bg=bg,
                         highlightthickness=0, relief="flat", **kw)
        self._fill = fill
        self._pct  = 0
        self._target = 0

    def set_percent(self, pct, color=None, animate=True):
        self._target = max(0, min(pct, 100))
        if color:
            self._fill = color
        if animate:
            self._animate_to_target()
        else:
            self._pct = self._target
            self._draw()

    def _animate_to_target(self):
        diff = self._target - self._pct
        if abs(diff) < 0.5:
            self._pct = self._target
            self._draw()
            return
        self._pct += diff * 0.18
        self._draw()
        self.after(16, self._animate_to_target)

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2:
            self.after(50, self._draw)
            return
        r = h / 2
        filled = int(w * self._pct / 100)
        self._round_rect(0, 0, w, h, r, fill=BG_ELEVATED)
        if filled > 2:
            self._round_rect(0, 0, filled, h, r, fill=self._fill)
        elif filled > 0:
            self.create_oval(0, 0, h, h, fill=self._fill, outline="")

    def _round_rect(self, x1, y1, x2, y2, r, fill):
        r = min(r, (y2 - y1) / 2, (x2 - x1) / 2) if (x2 - x1) > 0 else 0
        if r <= 0:
            self.create_rectangle(x1, y1, x2, y2, fill=fill, outline="")
            return
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        self.create_polygon(points, fill=fill, outline="", smooth=True)


# FIELD VALIDATOR
class FieldValidator:
    def __init__(self, parent, bg=BG_SURFACE):
        self.lbl = tk.Label(parent, text="", font=("Segoe UI", 8),
                            bg=bg, fg=RED)
        self.lbl.pack(anchor="w", pady=(0, 4))

    def error(self, msg):
        self.lbl.config(text=f"  ⚠  {msg}", fg=RED)

    def ok(self, msg=""):
        self.lbl.config(text=f"  ✓  {msg}" if msg else "", fg=GREEN)

    def clear(self):
        self.lbl.config(text="")



#  CUSTOM MODAL DIALOG  (replaces ugly messagebox)


class ConfirmDialog:
    """Clean centered confirmation dialog."""
    def __init__(self, root, title, message, confirm_text="Confirm",
                 confirm_color=RED, cancel_text="Cancel"):
        self.result = False
        self.root   = root

        overlay = tk.Toplevel(root)
        overlay.transient(root)
        overlay.grab_set()
        overlay.overrideredirect(True)
        overlay.configure(bg=BG_DEEP)
        overlay.attributes("-topmost", True)
        try:
            overlay.attributes("-alpha", 0.0)
        except Exception:
            pass

        # Dialog panel
        panel = tk.Frame(overlay, bg=BG_SURFACE,
                         highlightbackground=BORDER, highlightthickness=1,
                         padx=36, pady=30)
        panel.pack(padx=2, pady=2)

        # Icon row
        icon_frame = tk.Frame(panel, bg=BG_SURFACE)
        icon_frame.pack(pady=(0, 14))
        icon_circle = tk.Frame(icon_frame, bg="#FBE4DF", width=52, height=52)
        icon_circle.pack()
        icon_circle.pack_propagate(False)
        tk.Label(icon_circle, text="🗑", font=("Segoe UI", 20),
                 bg="#FBE4DF").place(relx=0.5, rely=0.5, anchor="center")

        # Title
        tk.Label(panel, text=title, font=("Segoe UI", 14, "bold"),
                 bg=BG_SURFACE, fg=TEXT_PRIMARY).pack()

        # Message
        tk.Label(panel, text=message, font=("Segoe UI", 10),
                 bg=BG_SURFACE, fg=TEXT_SECONDARY,
                 wraplength=280, justify="center").pack(pady=(8, 22))

        # Buttons
        btn_row = tk.Frame(panel, bg=BG_SURFACE)
        btn_row.pack(fill="x")

        def _cancel():
            self.result = False
            overlay.destroy()

        def _confirm():
            self.result = True
            overlay.destroy()

        cancel_btn = tk.Button(btn_row, text=cancel_text,
                               font=("Segoe UI", 10), bg=BG_ELEVATED,
                               fg=TEXT_PRIMARY, relief="flat", bd=0,
                               padx=20, pady=10, cursor="hand2",
                               activebackground=BORDER,
                               command=_cancel)
        cancel_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        confirm_btn = tk.Button(btn_row, text=confirm_text,
                                font=("Segoe UI", 10, "bold"),
                                bg=confirm_color, fg="white",
                                relief="flat", bd=0,
                                padx=20, pady=10, cursor="hand2",
                                activebackground=_shade(confirm_color, -20),
                                command=_confirm)
        confirm_btn.pack(side="left", expand=True, fill="x")

        # Center on root
        root.update_idletasks()
        overlay.update_idletasks()
        dw = overlay.winfo_reqwidth()
        dh = overlay.winfo_reqheight()
        rx = root.winfo_x() + root.winfo_width()  // 2 - dw // 2
        ry = root.winfo_y() + root.winfo_height() // 2 - dh // 2
        overlay.geometry(f"+{rx}+{ry}")

        # Fade in
        def fade(i=0, steps=8):
            if not overlay.winfo_exists():
                return
            try:
                overlay.attributes("-alpha", i / steps)
            except Exception:
                pass
            if i < steps:
                overlay.after(12, lambda: fade(i + 1, steps))
        fade()

        overlay.wait_window()

    @property
    def confirmed(self):
        return self.result



#  MAIN APPLICATION

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Expense Tracker")
        self.root.geometry("1240x740")
        self.root.minsize(1040, 660)
        self.root.configure(bg=BG_DEEP)

        self.uid = None
        self.username = None
        self.selected_expense_id = None
        self.toast = ToastNotification(self.root)

        self._setup_styles()
        self.show_login()

    #STYLES 

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        rowheight=36,
                        font=F_MONO,
                        background=BG_ELEVATED,
                        fieldbackground=BG_ELEVATED,
                        foreground=TEXT_PRIMARY,
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background=BG_SURFACE,
                        foreground=TEXT_SECONDARY,
                        relief="flat", borderwidth=0)
        style.map("Treeview.Heading", background=[("active", BG_ELEVATED)])
        style.map("Treeview",
                  background=[("selected", ACCENT_GLOW)],
                  foreground=[("selected", ACCENT)])

        style.configure("TCombobox",
                        fieldbackground=BG_ELEVATED,
                        background=BG_ELEVATED,
                        foreground=TEXT_PRIMARY,
                        arrowcolor=TEXT_SECONDARY,
                        selectbackground=BG_ELEVATED,
                        selectforeground=TEXT_PRIMARY,
                        font=F_BODY)
        style.map("TCombobox",
                  fieldbackground=[("readonly", BG_ELEVATED)],
                  selectbackground=[("readonly", BG_ELEVATED)])

        style.configure("Vertical.TScrollbar",
                        background=BG_ELEVATED,
                        troughcolor=BG_SURFACE,
                        arrowcolor=TEXT_SECONDARY,
                        borderwidth=0)

    #UTILS

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _page_header(self, title, subtitle=None):
        hdr = tk.Frame(self.content, bg=BG_DEEP, padx=32, pady=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text=title, font=F_HEADLINE,
                 bg=BG_DEEP, fg=TEXT_PRIMARY).pack(anchor="w")
        if subtitle:
            tk.Label(hdr, text=subtitle, font=F_SUBTITLE,
                     bg=BG_DEEP, fg=TEXT_SECONDARY).pack(anchor="w", pady=(2, 0))
        _divider(hdr, bg=BORDER).pack(fill="x", pady=(12, 0))
        return hdr

    def _highlight_nav(self, key):
        for k, btn in self.sidebar_buttons.items():
            if k == key:
                btn.config(bg=ACCENT_GLOW, fg=ACCENT)
            else:
                btn.config(bg=BG_SURFACE, fg=TEXT_SECONDARY)

    #LOGIN

    def show_login(self):
        self.clear()
        self.root.configure(bg=BG_DEEP)

        outer = tk.Frame(self.root, bg=BG_DEEP)
        outer.pack(expand=True, fill="both")

        HERO_BG   = ACCENT
        HERO_GLOW = "#0A6362"

        left = tk.Frame(outer, bg=HERO_BG, width=440)
        left.pack(side="left", fill="both")
        left.pack_propagate(False)

        brand_wrap = tk.Frame(left, bg=HERO_BG)
        brand_wrap.place(relx=0.5, rely=0.46, anchor="center")

        icon_ring = tk.Frame(brand_wrap, bg=HERO_GLOW, width=86, height=86)
        icon_ring.pack()
        icon_ring.pack_propagate(False)
        tk.Label(icon_ring, text="₨", font=("Segoe UI", 36, "bold"),
                 bg=HERO_GLOW, fg="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(brand_wrap, text="Smart Expense",
                 font=("Segoe UI", 26, "bold"), bg=HERO_BG, fg="#FFFFFF").pack(pady=(18, 0))
        tk.Label(brand_wrap, text="Tracker",
                 font=("Segoe UI", 26, "bold"), bg=HERO_BG, fg="#F4C95D").pack()
        _divider(brand_wrap, bg=HERO_GLOW).pack(fill="x", pady=16)
        tk.Label(brand_wrap, text="Track. Budget. Save Smarter.",
                 font=("Segoe UI", 11), bg=HERO_BG, fg="#D9F0EF").pack()

        pills_frame = tk.Frame(brand_wrap, bg=HERO_BG)
        pills_frame.pack(pady=20)
        for feat in ["📊 Analytics", "🎯 Budget Goals", "💡 Smart Insights"]:
            pill = tk.Frame(pills_frame, bg=HERO_GLOW)
            pill.pack(side="left", padx=4, ipadx=10, ipady=5)
            tk.Label(pill, text=feat, font=("Segoe UI", 8),
                     bg=HERO_GLOW, fg="#FFFFFF").pack()

        right = tk.Frame(outer, bg=BG_DEEP)
        right.pack(side="left", expand=True, fill="both")

        form_wrap = tk.Frame(right, bg=BG_SURFACE,
                             highlightbackground=BORDER, highlightthickness=1,
                             padx=44, pady=40)
        form_wrap.place(relx=0.5, rely=0.5, anchor="center")

        self._auth_mode = tk.StringVar(value="login")

        # Tab row
        tab_row = tk.Frame(form_wrap, bg=BG_ELEVATED,
                           highlightbackground=BORDER, highlightthickness=1)
        tab_row.pack(fill="x", pady=(0, 26))

        def make_tab(text, val):
            def _switch():
                self._auth_mode.set(val)
                _refresh_tabs()
            return tk.Button(tab_row, text=text, font=("Segoe UI", 9, "bold"),
                             bg=BG_ELEVATED, fg=TEXT_SECONDARY, relief="flat",
                             bd=0, padx=0, pady=9, cursor="hand2", command=_switch)

        self._tab_login    = make_tab("  Sign In  ", "login")
        self._tab_login.pack(side="left", expand=True, fill="x")
        self._tab_register = make_tab("  Create Account  ", "register")
        self._tab_register.pack(side="left", expand=True, fill="x")

        def _refresh_tabs():
            mode = self._auth_mode.get()
            if mode == "login":
                self._tab_login.config(bg=ACCENT, fg=TEXT_INVERSE)
                self._tab_register.config(bg=BG_ELEVATED, fg=TEXT_SECONDARY)
                action_btn.config(text="Sign In", command=self.do_login)
                secondary_btn.config(
                    text="New here? Create Account",
                    command=lambda: [self._auth_mode.set("register"), _refresh_tabs()])
            else:
                self._tab_register.config(bg=ACCENT, fg=TEXT_INVERSE)
                self._tab_login.config(bg=BG_ELEVATED, fg=TEXT_SECONDARY)
                action_btn.config(text="Create Account", command=self.do_register)
                secondary_btn.config(
                    text="Already have an account? Sign In",
                    command=lambda: [self._auth_mode.set("login"), _refresh_tabs()])

        # Fields
        tk.Label(form_wrap, text="USERNAME", font=F_LABEL,
                 bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(anchor="w")
        self.login_user_entry = _entry(form_wrap, width=32)
        self.login_user_entry.pack(anchor="w", ipady=8, pady=(4, 14))

        tk.Label(form_wrap, text="PASSWORD", font=F_LABEL,
                 bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(anchor="w")
        self.login_pass_entry = _entry(form_wrap, width=32, show="●")
        self.login_pass_entry.pack(anchor="w", ipady=8, pady=(4, 22))

        action_btn = _btn(form_wrap, "Sign In", self.do_login,
                          bg=ACCENT, fg=TEXT_INVERSE)
        action_btn.pack(fill="x", pady=(0, 10))

        secondary_btn = tk.Button(
            form_wrap, text="New here? Create Account",
            font=("Segoe UI", 9), bg=BG_SURFACE, fg=TEXT_SECONDARY,
            relief="flat", bd=0, cursor="hand2",
            activebackground=BG_SURFACE, activeforeground=ACCENT,
            command=lambda: [self._auth_mode.set("register"), _refresh_tabs()])
        secondary_btn.pack()

        self.login_status = tk.Label(form_wrap, text="", font=("Segoe UI", 9),
                                     bg=BG_SURFACE, fg=RED, wraplength=300)
        self.login_status.pack(pady=(10, 0))

        def _submit_current_mode():
            if self._auth_mode.get() == "login":
                self.do_login()
            else:
                self.do_register()

        _refresh_tabs()
        self.login_user_entry.focus_set()
        self.login_pass_entry.bind("<Return>", lambda e: _submit_current_mode())
        self.login_user_entry.bind("<Return>", lambda e: self.login_pass_entry.focus_set())

    def do_login(self):
        u = self.login_user_entry.get().strip()
        p = self.login_pass_entry.get().strip()
        if not u:
            self.login_status.config(text="⚠  Username cannot be empty.", fg=RED)
            self.login_user_entry.focus_set()
            return
        if not p:
            self.login_status.config(text="⚠  Password cannot be empty.", fg=RED)
            self.login_pass_entry.focus_set()
            return
        uid = login(u, p)
        if uid:
            self.uid = uid
            self.username = u
            self.show_main()
        else:
            self.login_status.config(
                text="⚠  Invalid username or password. Please try again.", fg=RED)
            self.login_pass_entry.delete(0, "end")
            self.login_pass_entry.focus_set()

    def do_register(self):
        u = self.login_user_entry.get().strip()
        p = self.login_pass_entry.get().strip()
        if not u:
            self.login_status.config(text="⚠  Username cannot be empty.", fg=RED)
            return
        if len(u) < 3:
            self.login_status.config(
                text="⚠  Username must be at least 3 characters.", fg=RED)
            return
        if not p:
            self.login_status.config(text="⚠  Password cannot be empty.", fg=RED)
            return
        if len(p) < 4:
            self.login_status.config(
                text="⚠  Password must be at least 4 characters.", fg=RED)
            return
        ok, msg = register(u, p)
        if ok:
            self.login_status.config(text=f"✅  {msg}", fg=GREEN)
        else:
            self.login_status.config(text=f"⚠  {msg}", fg=RED)

    # MAIN SHELL 

    def show_main(self):
        self.clear()
        self.root.configure(bg=BG_DEEP)

        # ── Sidebar ──
        sidebar = tk.Frame(self.root, bg=BG_SURFACE, width=228,
                           highlightbackground=BORDER, highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(sidebar, bg=BG_SURFACE, pady=20, padx=18)
        logo_frame.pack(fill="x")
        logo_inner = tk.Frame(logo_frame, bg=ACCENT_GLOW, width=34, height=34)
        logo_inner.pack(side="left")
        logo_inner.pack_propagate(False)
        tk.Label(logo_inner, text="₨", font=("Segoe UI", 15, "bold"),
                 bg=ACCENT_GLOW, fg=ACCENT).place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(logo_frame, text=" Expense\n Tracker",
                 font=("Segoe UI", 11, "bold"),
                 bg=BG_SURFACE, fg=TEXT_PRIMARY, justify="left").pack(side="left")

        _divider(sidebar, bg=BORDER).pack(fill="x", padx=14)

        # User card
        user_frame = tk.Frame(sidebar, bg=BG_ELEVATED, padx=14, pady=12,
                              highlightbackground=BORDER, highlightthickness=0)
        user_frame.pack(fill="x", padx=12, pady=10)
        avatar = tk.Frame(user_frame, bg=PURPLE, width=34, height=34)
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        tk.Label(avatar, text=self.username[0].upper(),
                 font=("Segoe UI", 13, "bold"), bg=PURPLE, fg="white").place(
            relx=0.5, rely=0.5, anchor="center")
        info = tk.Frame(user_frame, bg=BG_ELEVATED)
        info.pack(side="left", padx=(10, 0))
        tk.Label(info, text=self.username, font=("Segoe UI", 10, "bold"),
                 bg=BG_ELEVATED, fg=TEXT_PRIMARY).pack(anchor="w")
        tk.Label(info, text="Personal Account", font=("Segoe UI", 7),
                 bg=BG_ELEVATED, fg=TEXT_SECONDARY).pack(anchor="w")

        _divider(sidebar, bg=BORDER).pack(fill="x", padx=14, pady=(0, 8))

        # Nav items
        self.sidebar_buttons = {}
        nav_items = [
            ("📊  Dashboard",      self.show_dashboard),
            ("➕  Add Expense",    self.show_add_expense),
            ("📜  View Expenses",  self.show_view_expenses),
            ("✏️  Update / Delete", self.show_update_delete),
            ("🔍  Search",         self.show_search),
            ("🎯  Budget",         self.show_budget),
        ]

        nav_wrap = tk.Frame(sidebar, bg=BG_SURFACE, padx=8)
        nav_wrap.pack(fill="x")

        for label, cmd in nav_items:
            btn = tk.Button(nav_wrap, text=f"  {label}", font=("Segoe UI", 10, "bold"),
                            bg=BG_SURFACE, fg=TEXT_SECONDARY,
                            anchor="w", relief="flat", bd=0,
                            padx=10, pady=9,
                            activebackground=ACCENT_GLOW, activeforeground=ACCENT,
                            cursor="hand2", command=cmd)
            btn.pack(fill="x", pady=1)
            self.sidebar_buttons[label] = btn

            def make_hover(b=btn, k=label):
                def on_enter(e):
                    if b.cget("bg") != ACCENT_GLOW:
                        b.config(bg=BG_ELEVATED)
                def on_leave(e):
                    if b.cget("bg") == BG_ELEVATED:
                        b.config(bg=BG_SURFACE)
                b.bind("<Enter>", on_enter)
                b.bind("<Leave>", on_leave)
            make_hover()

        tk.Frame(sidebar, bg=BG_SURFACE).pack(expand=True, fill="both")
        _divider(sidebar, bg=BORDER).pack(fill="x", padx=14, pady=4)

        logout_btn = tk.Button(sidebar, text="  🚪  Sign Out",
                               font=("Segoe UI", 10, "bold"),
                               bg=BG_SURFACE, fg=RED,
                               activebackground="#FBE4DF", activeforeground=RED,
                               relief="flat", bd=0, padx=18, pady=10,
                               cursor="hand2", anchor="w",
                               command=self.logout)
        logout_btn.pack(fill="x", padx=8, pady=(0, 14))

        self.content = tk.Frame(self.root, bg=BG_DEEP)
        self.content.pack(side="left", expand=True, fill="both")

        self.show_dashboard()

    def logout(self):
        self.uid = None
        self.username = None
        self.show_login()

    # DASHBOARD

    def show_dashboard(self):
        self.clear_content()
        self._highlight_nav("📊  Dashboard")

        self._page_header("Dashboard",
                          f"Welcome back, {self.username} — here's your financial snapshot")

        # Scrollable body
        scroll_canvas = tk.Canvas(self.content, bg=BG_DEEP, highlightthickness=0)
        scroll_canvas.pack(fill="both", expand=True)
        inner = tk.Frame(scroll_canvas, bg=BG_DEEP)
        win_id = scroll_canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: scroll_canvas.configure(
            scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.bind("<Configure>",
            lambda e: scroll_canvas.itemconfig(win_id, width=e.width))

        b = get_budget(self.uid)
        t = total(self.uid)
        remaining = b - t

        # ── Stat cards ──
        cards_row = tk.Frame(inner, bg=BG_DEEP, padx=28, pady=14)
        cards_row.pack(fill="x")

        def stat_card(parent, label, value, icon, color, sublabel=None):
            card = tk.Frame(parent, bg=BG_SURFACE,
                            highlightbackground=BORDER, highlightthickness=1,
                            padx=20, pady=16)
            top = tk.Frame(card, bg=BG_SURFACE)
            top.pack(fill="x")
            tk.Label(top, text=label, font=F_LABEL,
                     bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(side="left", anchor="w")
            icon_box = tk.Frame(top, bg=ACCENT_GLOW, width=28, height=28)
            icon_box.pack(side="right")
            icon_box.pack_propagate(False)
            tk.Label(icon_box, text=icon, font=("Segoe UI", 12),
                     bg=ACCENT_GLOW).place(relx=0.5, rely=0.5, anchor="center")

            val_lbl = tk.Label(card, text="Rs 0", font=F_STAT,
                               bg=BG_SURFACE, fg=color)
            val_lbl.pack(anchor="w", pady=(6, 0))
            if sublabel:
                tk.Label(card, text=sublabel, font=("Segoe UI", 8),
                         bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(anchor="w", pady=(1, 0))

            def on_enter(e): card.config(highlightbackground=color)
            def on_leave(e): card.config(highlightbackground=BORDER)
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)
            self._animate_counter(val_lbl, value, color)
            return card

        rem_color = GREEN if remaining >= 0 else RED
        c1 = stat_card(cards_row, "MONTHLY BUDGET", b, "🎯", ACCENT, "Current month")
        c2 = stat_card(cards_row, "TOTAL SPENT", t, "💸", PURPLE,
                       f"{len(fetch_all(self.uid))} transactions")
        c3 = stat_card(cards_row, "REMAINING", remaining, "💰", rem_color,
                       "Over limit!" if remaining < 0 else "Available to spend")

        c1.pack(side="left", expand=True, fill="both", padx=(0, 8))
        c2.pack(side="left", expand=True, fill="both", padx=8)
        c3.pack(side="left", expand=True, fill="both", padx=(8, 0))

        # ── Advisor card ──
        adv_title, adv_msg, adv_color, pct = get_advisor_status(self.uid)

        adv_card = tk.Frame(inner, bg=BG_SURFACE,
                            highlightbackground=adv_color, highlightthickness=1,
                            padx=26, pady=18)
        adv_card.pack(fill="x", padx=28, pady=(14, 0))

        adv_top = tk.Frame(adv_card, bg=BG_SURFACE)
        adv_top.pack(fill="x")
        tk.Label(adv_top, text="SMART BUDGET ADVISOR", font=F_LABEL,
                 bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(side="left", anchor="w")
        status_pill = tk.Frame(adv_top, bg=adv_color, padx=10, pady=3)
        status_pill.pack(side="right")
        tk.Label(status_pill, text=adv_title, font=("Segoe UI", 8, "bold"),
                 bg=adv_color, fg="white").pack()

        tk.Label(adv_card, text=adv_msg, font=("Segoe UI", 12),
                 bg=BG_SURFACE, fg=TEXT_PRIMARY).pack(anchor="w", pady=(8, 10))

        if pct > 0:
            pbar = ProgressBar(adv_card, height=10, bg=BG_ELEVATED)
            pbar.pack(fill="x", pady=(0, 4))
            pct_color = GREEN if pct < 70 else (ORANGE if pct < 90 else RED)
            adv_card.after(80, lambda: pbar.set_percent(pct, color=pct_color))
            tk.Label(adv_card, text=f"{pct:.1f}% of budget used",
                     font=("Segoe UI", 8), bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(anchor="e")

        # ── Recent transactions ──
        rec_hdr = tk.Frame(inner, bg=BG_DEEP, padx=28)
        rec_hdr.pack(fill="x", pady=(18, 6))
        tk.Label(rec_hdr, text="Recent Transactions", font=F_TITLE,
                 bg=BG_DEEP, fg=TEXT_PRIMARY).pack(side="left")
        _btn(rec_hdr, "View All →", self.show_view_expenses,
             bg=BG_ELEVATED, fg=ACCENT, font=("Segoe UI", 8)).pack(side="right")

        tree_frame = tk.Frame(inner, bg=BG_SURFACE,
                              highlightbackground=BORDER, highlightthickness=1)
        tree_frame.pack(fill="x", padx=28, pady=(0, 22))

        cols = ("ID", "Date", "Category", "Description", "Amount")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                            height=8, selectmode="none")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.column("ID", width=50)
        tree.column("Date", width=110)
        tree.column("Category", width=130)
        tree.column("Description", anchor="w", width=340)
        tree.column("Amount", width=120)
        tree.pack(fill="both", padx=1, pady=1)

        tree.tag_configure("oddrow",  background=BG_ELEVATED)
        tree.tag_configure("evenrow", background=BG_SURFACE)

        for idx, row in enumerate(fetch_all(self.uid)[:10]):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            tree.insert("", "end",
                        values=(row[0], row[1], row[2], row[3], f"Rs {row[4]:,.2f}"),
                        tags=(tag,))

    def _animate_counter(self, label, target_value, color, steps=14, delay=18):
        start  = 0.0
        target = float(target_value)

        def step(i=0):
            if not label.winfo_exists():
                return
            frac = i / steps
            frac = 1 - (1 - frac) ** 2
            current = start + (target - start) * frac
            label.config(text=f"Rs {current:,.0f}")
            if i < steps:
                label.after(delay, lambda: step(i + 1))
            else:
                label.config(text=f"Rs {target:,.0f}")
        step()

    # ADD EXPENSE 

    def show_add_expense(self):
        self.clear_content()
        self._highlight_nav("➕  Add Expense")

        self._page_header("Add Expense", "Record a new transaction")

        # Two-column layout: form left, summary right
        body = tk.Frame(self.content, bg=BG_DEEP, padx=28, pady=16)
        body.pack(fill="both", expand=True)

        # ── LEFT: main form card ──
        form_card = tk.Frame(body, bg=BG_SURFACE,
                             highlightbackground=BORDER, highlightthickness=1)
        form_card.pack(side="left", fill="both", expand=True, padx=(0, 16))

        # Card header strip
        hdr_strip = tk.Frame(form_card, bg=ACCENT, padx=24, pady=14)
        hdr_strip.pack(fill="x")
        tk.Label(hdr_strip, text="New Transaction",
                 font=("Segoe UI", 13, "bold"), bg=ACCENT, fg="white").pack(side="left")
        tk.Label(hdr_strip, text="➕", font=("Segoe UI", 16),
                 bg=ACCENT, fg="white").pack(side="right")

        fields_area = tk.Frame(form_card, bg=BG_SURFACE, padx=28, pady=24)
        fields_area.pack(fill="both", expand=True)

        def field_row(parent, label, widget_factory, tip_text=None):
            """Renders a labeled field block stacked vertically."""
            block = tk.Frame(parent, bg=BG_SURFACE)
            block.pack(fill="x", pady=(0, 6))

            lbl_row = tk.Frame(block, bg=BG_SURFACE)
            lbl_row.pack(fill="x")
            tk.Label(lbl_row, text=label, font=F_LABEL,
                     bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(side="left", anchor="w")
            if tip_text:
                tk.Label(lbl_row, text=tip_text, font=("Segoe UI", 7),
                         bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(side="right", anchor="e")

            widget = widget_factory(block)
            v = FieldValidator(block, bg=BG_SURFACE)
            return widget, v

        # DATE
        def make_date(p):
            e = _entry(p, width=40)
            e.insert(0, str(date.today()))
            e.pack(fill="x", ipady=9, pady=(4, 0))
            return e

        date_entry, date_v = field_row(fields_area, "DATE", make_date, "YYYY-MM-DD")

        # CATEGORY
        def make_cat(p):
            combo = ttk.Combobox(p, values=CATEGORIES, font=F_BODY, state="normal")
            combo.pack(fill="x", ipady=6, pady=(4, 0))
            return combo

        cat_combo, cat_v = field_row(fields_area, "CATEGORY", make_cat)

        # DESCRIPTION
        def make_desc(p):
            e = _entry(p, width=40)
            e.pack(fill="x", ipady=9, pady=(4, 0))
            return e

        desc_entry, desc_v = field_row(fields_area, "DESCRIPTION", make_desc)

        # AMOUNT
        def make_amt(p):
            wrap = tk.Frame(p, bg=BG_SURFACE)
            wrap.pack(fill="x", pady=(4, 0))
            prefix = tk.Label(wrap, text="Rs", font=("Segoe UI", 11, "bold"),
                              bg=BG_ELEVATED, fg=ACCENT,
                              padx=10, pady=9, relief="flat")
            prefix.pack(side="left")
            e = _entry(wrap, width=34)
            e.pack(side="left", fill="x", expand=True, ipady=9)
            return e

        amt_entry, amt_v = field_row(fields_area, "AMOUNT", make_amt)

        _divider(fields_area, bg=BORDER).pack(fill="x", pady=(16, 20))

        # Buttons
        btn_row = tk.Frame(fields_area, bg=BG_SURFACE)
        btn_row.pack(fill="x")

        def validate_and_submit():
            ok = True

            d = date_entry.get().strip()
            if not d:
                date_v.error("Date is required")
                ok = False
            elif not validate_date(d):
                date_v.error("Use YYYY-MM-DD (e.g. 2025-06-15)")
                ok = False
            else:
                date_v.ok()

            c = cat_combo.get().strip()
            if not c:
                cat_v.error("Please select or type a category")
                ok = False
            else:
                cat_v.ok()

            desc = desc_entry.get().strip()
            if not desc:
                desc_v.error("Description cannot be empty")
                ok = False
            elif len(desc) < 2:
                desc_v.error("Too short — min 2 characters")
                ok = False
            else:
                desc_v.ok()

            amt_ok, amt = validate_amount(amt_entry.get().strip())
            if not amt_ok:
                amt_v.error("Enter a positive number (e.g. 250 or 1450.50)")
                ok = False
            else:
                amt_v.ok(f"Rs {amt:,.2f}")

            if not ok:
                return

            add_expense(self.uid, d, c, desc, amt)
            self.toast.show(f"Expense of Rs {amt:,.2f} added successfully", color=GREEN)

            # Refresh preview panel
            _refresh_preview()

            date_entry.delete(0, "end")
            date_entry.insert(0, str(date.today()))
            cat_combo.set("")
            desc_entry.delete(0, "end")
            amt_entry.delete(0, "end")
            for v in (date_v, cat_v, desc_v, amt_v):
                v.clear()
            desc_entry.focus_set()

        def reset_form():
            date_entry.delete(0, "end")
            date_entry.insert(0, str(date.today()))
            cat_combo.set("")
            desc_entry.delete(0, "end")
            amt_entry.delete(0, "end")
            for v in (date_v, cat_v, desc_v, amt_v):
                v.clear()

        add_btn = _btn(btn_row, "  ➕  Add Expense", validate_and_submit,
                       bg=GREEN, fg="white", font=("Segoe UI", 11, "bold"),
                       padx=24, pady=12)
        add_btn.pack(side="left", padx=(0, 10))
        reset_btn = _btn(btn_row, "  ↺  Reset", reset_form,
                         bg=BG_ELEVATED, fg=TEXT_SECONDARY,
                         padx=18, pady=12)
        reset_btn.pack(side="left")

        # ── RIGHT: info panel ──
        right_panel = tk.Frame(body, bg=BG_DEEP, width=240)
        right_panel.pack(side="left", fill="y")
        right_panel.pack_propagate(False)

        # Budget snapshot card
        snap_card = tk.Frame(right_panel, bg=BG_SURFACE,
                             highlightbackground=BORDER, highlightthickness=1)
        snap_card.pack(fill="x", pady=(0, 12))

        snap_hdr = tk.Frame(snap_card, bg=ACCENT_GLOW, padx=16, pady=10)
        snap_hdr.pack(fill="x")
        tk.Label(snap_hdr, text="Budget Snapshot",
                 font=("Segoe UI", 9, "bold"), bg=ACCENT_GLOW, fg=ACCENT).pack(anchor="w")

        snap_body = tk.Frame(snap_card, bg=BG_SURFACE, padx=16, pady=14)
        snap_body.pack(fill="x")

        b  = get_budget(self.uid)
        t  = total(self.uid)
        rem = b - t

        def _snap_row(parent, label, value, color):
            row = tk.Frame(parent, bg=BG_SURFACE)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, font=("Segoe UI", 8),
                     bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(side="left")
            tk.Label(row, text=value, font=("Segoe UI", 10, "bold"),
                     bg=BG_SURFACE, fg=color).pack(side="right")

        _snap_row(snap_body, "Budget",    f"Rs {b:,.0f}",   ACCENT)
        _snap_row(snap_body, "Spent",     f"Rs {t:,.0f}",   PURPLE)
        _snap_row(snap_body, "Remaining", f"Rs {rem:,.0f}", GREEN if rem >= 0 else RED)

        if b > 0:
            pct = min((t / b) * 100, 100)
            pb = ProgressBar(snap_body, height=7)
            pb.pack(fill="x", pady=(8, 2))
            pct_col = GREEN if pct < 70 else (ORANGE if pct < 90 else RED)
            snap_card.after(120, lambda: pb.set_percent(pct, color=pct_col))

        # Category icons quick-pick hint
        cat_card = tk.Frame(right_panel, bg=BG_SURFACE,
                            highlightbackground=BORDER, highlightthickness=1)
        cat_card.pack(fill="x", pady=(0, 12))

        cat_hdr = tk.Frame(cat_card, bg=ACCENT_GLOW, padx=16, pady=10)
        cat_hdr.pack(fill="x")
        tk.Label(cat_hdr, text="Quick Category",
                 font=("Segoe UI", 9, "bold"), bg=ACCENT_GLOW, fg=ACCENT).pack(anchor="w")

        cat_grid = tk.Frame(cat_card, bg=BG_SURFACE, padx=12, pady=12)
        cat_grid.pack(fill="x")

        for i, cat in enumerate(CATEGORIES):
            icon = CATEGORY_ICONS.get(cat, "📦")
            def _pick(c=cat):
                cat_combo.set(c)
                cat_v.clear()
            btn = tk.Button(cat_grid, text=f"{icon}\n{cat}",
                            font=("Segoe UI", 7), bg=BG_ELEVATED,
                            fg=TEXT_PRIMARY, relief="flat", bd=0,
                            width=6, pady=6, cursor="hand2",
                            activebackground=ACCENT_GLOW, activeforeground=ACCENT,
                            command=_pick)
            btn.grid(row=i // 2, column=i % 2, padx=4, pady=3, sticky="ew")
        cat_grid.columnconfigure(0, weight=1)
        cat_grid.columnconfigure(1, weight=1)

        # Recent 3 transactions preview
        recent_card = tk.Frame(right_panel, bg=BG_SURFACE,
                               highlightbackground=BORDER, highlightthickness=1)
        recent_card.pack(fill="x")

        rec_hdr = tk.Frame(recent_card, bg=ACCENT_GLOW, padx=16, pady=10)
        rec_hdr.pack(fill="x")
        tk.Label(rec_hdr, text="Recent",
                 font=("Segoe UI", 9, "bold"), bg=ACCENT_GLOW, fg=ACCENT).pack(anchor="w")

        rec_body = tk.Frame(recent_card, bg=BG_SURFACE, padx=14, pady=10)
        rec_body.pack(fill="x")

        def _refresh_preview():
            for w in rec_body.winfo_children():
                w.destroy()
            rows = fetch_all(self.uid)[:3]
            if not rows:
                tk.Label(rec_body, text="No expenses yet",
                         font=("Segoe UI", 8), bg=BG_SURFACE,
                         fg=TEXT_SECONDARY).pack(anchor="w")
                return
            for row in rows:
                r = tk.Frame(rec_body, bg=BG_SURFACE)
                r.pack(fill="x", pady=3)
                icon = CATEGORY_ICONS.get(row[2], "📦")
                tk.Label(r, text=f"{icon} {row[3][:18]}",
                         font=("Segoe UI", 8), bg=BG_SURFACE,
                         fg=TEXT_PRIMARY).pack(side="left")
                tk.Label(r, text=f"Rs {row[4]:,.0f}",
                         font=("Segoe UI", 8, "bold"), bg=BG_SURFACE,
                         fg=PURPLE).pack(side="right")

        _refresh_preview()

        # Tab key order
        date_entry.bind("<Tab>", lambda e: [cat_combo.focus_set(), "break"])
        cat_combo.bind("<Tab>", lambda e: [desc_entry.focus_set(), "break"])
        desc_entry.bind("<Tab>", lambda e: [amt_entry.focus_set(), "break"])
        amt_entry.bind("<Return>", lambda e: validate_and_submit())
        date_entry.focus_set()

    #VIEW EXPENSES 

    def show_view_expenses(self):
        self.clear_content()
        self._highlight_nav("📜  View Expenses")

        self._page_header("All Expenses", "Complete history of your recorded transactions")

        toolbar = tk.Frame(self.content, bg=BG_DEEP, padx=28, pady=6)
        toolbar.pack(fill="x")
        _btn(toolbar, "  🔄  Refresh", self.show_view_expenses,
             bg=BG_ELEVATED, fg=TEXT_SECONDARY, font=("Segoe UI", 9)).pack(side="left")
        t = total(self.uid)
        tk.Label(toolbar, text=f"Total Spent: Rs {t:,.2f}",
                 font=("Segoe UI", 11, "bold"), bg=BG_DEEP, fg=ACCENT).pack(side="right")

        tframe = tk.Frame(self.content, bg=BG_SURFACE,
                          highlightbackground=BORDER, highlightthickness=1)
        tframe.pack(fill="both", expand=True, padx=28, pady=(8, 22))

        cols = ("ID", "Date", "Category", "Description", "Amount")
        tree = ttk.Treeview(tframe, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.column("ID", width=55)
        tree.column("Date", width=110)
        tree.column("Category", width=130)
        tree.column("Description", anchor="w", width=380)
        tree.column("Amount", width=120)

        vsb = ttk.Scrollbar(tframe, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tree.tag_configure("oddrow",  background=BG_ELEVATED)
        tree.tag_configure("evenrow", background=BG_SURFACE)

        for idx, row in enumerate(fetch_all(self.uid)):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            tree.insert("", "end",
                        values=(row[0], row[1], row[2], row[3], f"Rs {row[4]:,.2f}"),
                        tags=(tag,))

    # UPDATE / DELETE 

    def show_update_delete(self):
        self.clear_content()
        self._highlight_nav("✏️  Update / Delete")
        self.selected_expense_id = None

        self._page_header("Update / Delete",
                          "Select a row from the table, then edit or remove it")

        body = tk.Frame(self.content, bg=BG_DEEP, padx=28, pady=10)
        body.pack(fill="both", expand=True)

        # Table
        tframe = tk.Frame(body, bg=BG_SURFACE,
                          highlightbackground=BORDER, highlightthickness=1)
        tframe.pack(side="left", fill="both", expand=True, padx=(0, 16))

        cols = ("ID", "Date", "Category", "Description", "Amount")
        tree = ttk.Treeview(tframe, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.column("ID", width=55)
        tree.column("Date", width=100)
        tree.column("Category", width=110)
        tree.column("Description", anchor="w", width=220)
        tree.column("Amount", width=100)

        vsb = ttk.Scrollbar(tframe, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tree.tag_configure("oddrow",  background=BG_ELEVATED)
        tree.tag_configure("evenrow", background=BG_SURFACE)

        for idx, row in enumerate(fetch_all(self.uid)):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            tree.insert("", "end",
                        values=(row[0], row[1], row[2], row[3], row[4]),
                        tags=(tag,))

        # Edit form
        form = _card(body, padx=20, pady=22)
        form.pack(side="left", fill="y")
        form.pack_propagate(False)
        form.configure(width=280)

        sel_pill = tk.Frame(form, bg=ACCENT_GLOW,
                            highlightbackground=BORDER, highlightthickness=1,
                            padx=12, pady=6)
        sel_pill.pack(fill="x", pady=(0, 16))
        self._sel_label = tk.Label(sel_pill,
                                   text="← Select a row to edit",
                                   font=("Segoe UI", 9),
                                   bg=ACCENT_GLOW, fg=TEXT_SECONDARY)
        self._sel_label.pack(anchor="w")

        def field_block(label_text):
            tk.Label(form, text=label_text, font=F_LABEL,
                     bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(anchor="w")
            e = _entry(form, width=24)
            e.pack(anchor="w", ipady=7, pady=(3, 0))
            v = FieldValidator(form, bg=BG_SURFACE)
            return e, v

        date_entry, date_v = field_block("DATE")
        cat_entry,  cat_v  = field_block("CATEGORY")
        desc_entry, desc_v = field_block("DESCRIPTION")
        amt_entry,  amt_v  = field_block("AMOUNT (Rs)")

        def on_select(event):
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            self.selected_expense_id = vals[0]
            self._sel_label.config(
                text=f"Editing Expense #{self.selected_expense_id}", fg=ACCENT)
            for e in (date_entry, cat_entry, desc_entry, amt_entry):
                e.delete(0, "end")
            date_entry.insert(0, vals[1])
            cat_entry.insert(0,  vals[2])
            desc_entry.insert(0, vals[3])
            amt_entry.insert(0,  vals[4])
            for v in (date_v, cat_v, desc_v, amt_v):
                v.clear()

        tree.bind("<<TreeviewSelect>>", on_select)

        def do_update():
            if not self.selected_expense_id:
                self._sel_label.config(text="⚠  Select an expense first", fg=RED)
                return
            ok = True
            d = date_entry.get().strip()
            if not validate_date(d):
                date_v.error("Use YYYY-MM-DD")
                ok = False
            else:
                date_v.ok()
            c = cat_entry.get().strip()
            if not c:
                cat_v.error("Category required")
                ok = False
            else:
                cat_v.ok()
            desc = desc_entry.get().strip()
            if not desc:
                desc_v.error("Description required")
                ok = False
            else:
                desc_v.ok()
            amt_ok, amt = validate_amount(amt_entry.get().strip())
            if not amt_ok:
                amt_v.error("Positive number required")
                ok = False
            else:
                amt_v.ok(f"Rs {amt:,.2f}")
            if not ok:
                return
            update(self.selected_expense_id, d, c, desc, amt)
            self.toast.show(f"Expense #{self.selected_expense_id} updated", color=ACCENT)
            self.show_update_delete()

        def do_delete():
            if not self.selected_expense_id:
                self._sel_label.config(text="⚠  Select an expense first", fg=RED)
                return
            dlg = ConfirmDialog(
                self.root,
                "Delete Expense",
                f"Permanently delete expense #{self.selected_expense_id}?\n\nThis cannot be undone.",
                confirm_text="Yes, Delete",
                confirm_color=RED,
                cancel_text="Cancel"
            )
            if dlg.confirmed:
                delete(self.selected_expense_id)
                self.toast.show(f"Expense #{self.selected_expense_id} deleted", color=RED)
                self.show_update_delete()

        btn_row = tk.Frame(form, bg=BG_SURFACE)
        btn_row.pack(fill="x", pady=(8, 0))
        _btn(btn_row, "Update", do_update, bg=ACCENT, fg="white",
             font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x", padx=(0, 5))
        _btn(btn_row, "Delete", do_delete, bg=RED, fg="white",
             font=("Segoe UI", 9, "bold")).pack(side="left", expand=True, fill="x")

    # SEARCH 
    def show_search(self):
        self.clear_content()
        self._highlight_nav("🔍  Search")

        self._page_header("Search Expenses", "Filter transactions by category keyword")

        search_bar = tk.Frame(self.content, bg=BG_DEEP, padx=28, pady=10)
        search_bar.pack(fill="x")

        search_entry = _entry(search_bar, width=36)
        search_entry.pack(side="left", ipady=8, padx=(0, 10))

        result_count = tk.Label(search_bar, text="", font=("Segoe UI", 9),
                                bg=BG_DEEP, fg=TEXT_SECONDARY)
        result_count.pack(side="right")

        tframe = tk.Frame(self.content, bg=BG_SURFACE,
                          highlightbackground=BORDER, highlightthickness=1)
        tframe.pack(fill="both", expand=True, padx=28, pady=(6, 22))

        cols = ("ID", "Date", "Category", "Description", "Amount")
        tree = ttk.Treeview(tframe, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.column("ID", width=55)
        tree.column("Date", width=110)
        tree.column("Category", width=130)
        tree.column("Description", anchor="w", width=400)
        tree.column("Amount", width=120)

        vsb = ttk.Scrollbar(tframe, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tree.tag_configure("oddrow",  background=BG_ELEVATED)
        tree.tag_configure("evenrow", background=BG_SURFACE)

        def do_search(event=None):
            for i in tree.get_children():
                tree.delete(i)
            keyword = search_entry.get().strip()
            results = search(self.uid, keyword)
            for idx, row in enumerate(results):
                tag = "evenrow" if idx % 2 == 0 else "oddrow"
                tree.insert("", "end",
                            values=(row[0], row[1], row[2], row[3], f"Rs {row[4]:,.2f}"),
                            tags=(tag,))
            count = len(results)
            result_count.config(
                text=f"{count} result{'s' if count != 1 else ''} found",
                fg=ACCENT if count else TEXT_SECONDARY)

        _btn(search_bar, "  🔍  Search", do_search, bg=ACCENT, fg=TEXT_INVERSE).pack(side="left")

        search_entry.bind("<Return>",     do_search)
        search_entry.bind("<KeyRelease>", do_search)
        search_entry.focus_set()
        do_search()

    # BUDGET 

    def show_budget(self):
        self.clear_content()
        self._highlight_nav("Budget")

        self._page_header("Monthly Budget",
                          "Configure your spending limit and view advisor insights")

        outer = tk.Frame(self.content, bg=BG_DEEP, padx=28, pady=14)
        outer.pack(fill="both", expand=True)

        b_card = _card(outer, padx=26, pady=22)
        b_card.pack(fill="x")

        current_b = get_budget(self.uid)
        t = total(self.uid)

        top_row = tk.Frame(b_card, bg=BG_SURFACE)
        top_row.pack(fill="x", pady=(0, 16))
        tk.Label(top_row, text="Current Budget", font=F_LABEL,
                 bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(anchor="w")
        tk.Label(top_row, text=f"Rs {current_b:,.2f}",
                 font=("Segoe UI", 20, "bold"), bg=BG_SURFACE, fg=ACCENT).pack(anchor="w", pady=(4, 0))

        _divider(b_card, bg=BORDER).pack(fill="x", pady=(0, 16))

        tk.Label(b_card, text="SET NEW BUDGET (Rs)", font=F_LABEL,
                 bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(anchor="w")
        budget_entry = _entry(b_card, width=26)
        budget_entry.pack(anchor="w", ipady=8, pady=(4, 0))
        budget_v = FieldValidator(b_card, bg=BG_SURFACE)

        def save_budget():
            ok, amount = validate_amount(budget_entry.get().strip())
            if not ok:
                budget_v.error("Enter a valid positive number (e.g. 15000)")
                return
            budget_v.ok(f"Rs {amount:,.2f} saved")
            set_budget(self.uid, amount)
            self.toast.show(f"Budget set to Rs {amount:,.2f}", color=GREEN)
            self.show_budget()

        _btn(b_card, "  💾  Save Budget", save_budget, bg=GREEN, fg="white").pack(
            anchor="w", pady=(10, 0))

        # Advisor
        adv_title, adv_msg, adv_color, pct = get_advisor_status(self.uid)

        adv_card = tk.Frame(outer, bg=BG_SURFACE,
                            highlightbackground=adv_color, highlightthickness=1,
                            padx=26, pady=20)
        adv_card.pack(fill="x", pady=(18, 0))

        tk.Label(adv_card, text="🤖  SMART BUDGET ADVISOR", font=F_LABEL,
                 bg=BG_SURFACE, fg=TEXT_SECONDARY).pack(anchor="w")

        badge = tk.Frame(adv_card, bg=adv_color, padx=12, pady=4)
        badge.pack(anchor="w", pady=(8, 4))
        tk.Label(badge, text=adv_title, font=("Segoe UI", 11, "bold"),
                 bg=adv_color, fg="white").pack()

        tk.Label(adv_card, text=adv_msg, font=("Segoe UI", 11),
                 bg=BG_SURFACE, fg=TEXT_PRIMARY).pack(anchor="w", pady=(4, 12))

        if pct > 0:
            pb = ProgressBar(adv_card, height=10)
            pb.pack(fill="x", pady=(0, 4))
            pct_col = GREEN if pct < 70 else (ORANGE if pct < 90 else RED)
            adv_card.after(80, lambda: pb.set_percent(pct, color=pct_col))

        if current_b > 0:
            stats_row = tk.Frame(adv_card, bg=BG_ELEVATED,
                                 highlightbackground=BORDER, highlightthickness=1,
                                 padx=14, pady=12)
            stats_row.pack(fill="x", pady=(10, 0))

            def mini_stat(parent, label, value, color):
                f = tk.Frame(parent, bg=BG_ELEVATED)
                f.pack(side="left", expand=True)
                tk.Label(f, text=label, font=("Segoe UI", 7, "bold"),
                         bg=BG_ELEVATED, fg=TEXT_SECONDARY).pack()
                tk.Label(f, text=value, font=("Segoe UI", 12, "bold"),
                         bg=BG_ELEVATED, fg=color).pack()

            mini_stat(stats_row, "BUDGET",    f"Rs {current_b:,.0f}", ACCENT)
            tk.Frame(stats_row, bg=BORDER, width=1).pack(side="left", fill="y", padx=6)
            mini_stat(stats_row, "SPENT",     f"Rs {t:,.0f}", PURPLE)
            tk.Frame(stats_row, bg=BORDER, width=1).pack(side="left", fill="y", padx=6)
            rem = current_b - t
            mini_stat(stats_row, "REMAINING", f"Rs {rem:,.0f}", GREEN if rem >= 0 else RED)
            tk.Frame(stats_row, bg=BORDER, width=1).pack(side="left", fill="y", padx=6)
            mini_stat(stats_row, "USED",      f"{pct:.1f}%", adv_color)


# ENTRY POINT


if __name__ == "__main__":
    create_tables()
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()