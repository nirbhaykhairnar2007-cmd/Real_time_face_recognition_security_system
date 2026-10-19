import tkinter as tk
from tkinter import Label, Entry, Button, ttk, messagebox
import firebase_admin
from firebase_admin import credentials, db
import cv2
import os
from datetime import datetime
from PIL import Image, ImageTk

# ---------------- Firebase Initialization ----------------
cred = credentials.Certificate("firebase_config.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://face-recognition-securit-5dd85-default-rtdb.firebaseio.com/"
    })

admin_ref = db.reference("admins")
user_ref  = db.reference("users")

# ---------------- Colors ----------------
BG         = "#1c1c1e"
SIDEBAR_BG = "#141416"
CARD_BG    = "#2c2c2e"
LINE_COLOR = "#3a3a3c"
BLUE       = "#3b82f6"
GREEN      = "#22c55e"
RED        = "#ef4444"
TEXT       = "#f5f5f5"
MUTED      = "#b0b0ba"
INPUT_BG   = "#3a3a3c"
INPUT_FG   = "#ffffff"

# ---------------- Fonts ----------------
F_TITLE = ("Segoe UI", 22, "bold")
F_HEAD  = ("Segoe UI", 15, "bold")
F_LABEL = ("Segoe UI", 12, "bold")
F_BODY  = ("Segoe UI", 12)
F_BTN   = ("Segoe UI", 12, "bold")
F_SMALL = ("Segoe UI", 11, "bold")

# ---------------- Root ----------------
root = tk.Tk()
root.title("FaceLock Admin")
root.state("zoomed")
root.configure(bg=BG)

# =========================================================
# ================= SHARED HELPERS ========================
# =========================================================

frames = []

def show_frame(frame):
    for f in frames:
        f.pack_forget()
    frame.pack(fill="both", expand=True)

def entry(parent, width=30, show=None):
    e = tk.Entry(
        parent, width=width, font=F_BODY,
        bg=INPUT_BG, fg=INPUT_FG,
        insertbackground=TEXT,
        relief="flat", bd=0,
        highlightthickness=1,
        highlightbackground=LINE_COLOR,
        highlightcolor=BLUE,
    )
    if show:
        e.config(show=show)
    return e

def btn(parent, text, color, command, width=None):
    kw = dict(
        text=text, font=F_BTN,
        fg="#ffffff", bg=color,
        activeforeground="#ffffff", activebackground=color,
        relief="flat", bd=0,
        padx=16, pady=8,
        cursor="hand2", command=command,
    )
    if width:
        kw["width"] = width
    b = tk.Button(parent, **kw)
    def _in(e, c=color):
        r = int(c[1:3],16); g = int(c[3:5],16); bv = int(c[5:7],16)
        b.config(bg=f"#{max(r-25,0):02x}{max(g-25,0):02x}{max(bv-25,0):02x}")
    def _out(e, c=color): b.config(bg=c)
    b.bind("<Enter>", _in)
    b.bind("<Leave>", _out)
    return b

def ghost_btn(parent, text, command, bg=BG):
    b = tk.Button(
        parent, text=text, font=("Segoe UI", 10),
        fg=MUTED, bg=bg,
        activeforeground=TEXT, activebackground=bg,
        relief="flat", bd=0, cursor="hand2", command=command
    )
    b.bind("<Enter>", lambda e: b.config(fg=TEXT))
    b.bind("<Leave>", lambda e: b.config(fg=MUTED))
    return b

def top_bar(parent, title, back_cmd=None):
    bar = tk.Frame(parent, bg=SIDEBAR_BG, pady=14)
    bar.pack(fill="x")
    row = tk.Frame(bar, bg=SIDEBAR_BG)
    row.pack(fill="x", padx=28)
    if back_cmd:
        ghost_btn(row, "← Back", back_cmd, bg=SIDEBAR_BG).pack(side="left", padx=(0, 12))
    tk.Label(row, text=title, font=F_HEAD, fg=TEXT, bg=SIDEBAR_BG).pack(side="left")
    tk.Frame(bar, height=1, bg=LINE_COLOR).pack(fill="x", pady=(12, 0))

# =========================================================
# ================= LOGIN FRAME ===========================
# =========================================================

login_frame = tk.Frame(root, bg=BG)

sidebar = tk.Frame(login_frame, bg=SIDEBAR_BG, width=280)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(sidebar, text="FaceLock", font=("Segoe UI", 22, "bold"),
         fg=TEXT, bg=SIDEBAR_BG).pack(pady=(90, 4))
tk.Label(sidebar, text="Admin Panel", font=F_BODY,
         fg=MUTED, bg=SIDEBAR_BG).pack()

tk.Frame(sidebar, height=1, bg=LINE_COLOR).pack(fill="x", padx=28, pady=36)

for line in ["Face Recognition System", "Firebase Real-time DB", "Admin Management"]:
    tk.Label(sidebar, text=line, font=F_SMALL,
             fg=MUTED, bg=SIDEBAR_BG, anchor="w").pack(fill="x", padx=28, pady=3)

right = tk.Frame(login_frame, bg=BG)
right.pack(side="left", fill="both", expand=True)

form_wrap = tk.Frame(right, bg=BG)
form_wrap.place(relx=0.5, rely=0.5, anchor="center")

tk.Label(form_wrap, text="Sign in", font=F_TITLE, fg=TEXT, bg=BG).pack(anchor="w")
tk.Label(form_wrap, text="Enter your admin credentials to continue.",
         font=F_SMALL, fg=MUTED, bg=BG).pack(anchor="w", pady=(3, 22))

tk.Label(form_wrap, text="Email", font=F_LABEL, fg=MUTED, bg=BG).pack(anchor="w")
email_entry = entry(form_wrap, width=34)
email_entry.pack(pady=(3, 14), ipady=7)

tk.Label(form_wrap, text="Password", font=F_LABEL, fg=MUTED, bg=BG).pack(anchor="w")
password_entry = entry(form_wrap, width=34, show="●")
password_entry.pack(pady=(3, 22), ipady=7)

btn_row = tk.Frame(form_wrap, bg=BG)
btn_row.pack(anchor="w")

def login_admin():
    email = email_entry.get()
    password = password_entry.get()
    admins = admin_ref.get()
    if admins:
        for key, value in admins.items():
            if value["email"] == email and value["password"] == password:
                messagebox.showinfo("Success", "Login Successful")
                show_frame(dashboard_frame)
                return
    messagebox.showerror("Error", "Invalid Credentials")

def register_admin():
    email = email_entry.get()
    password = password_entry.get()
    if not email or not password:
        messagebox.showerror("Error", "All fields required")
        return
    admin_ref.push({"email": email, "password": password})
    messagebox.showinfo("Success", "Admin Registered")

btn(btn_row, "Login",    BLUE,    login_admin,    width=13).pack(side="left", padx=(0, 10))
btn(btn_row, "Register", CARD_BG, register_admin, width=13).pack(side="left")

# =========================================================
# ================= DASHBOARD =============================
# =========================================================

dashboard_frame = tk.Frame(root, bg=BG)

top_bar(dashboard_frame, "Dashboard")

dash_body = tk.Frame(dashboard_frame, bg=BG)
dash_body.pack(expand=True)

cards_wrap = tk.Frame(dash_body, bg=BG)
cards_wrap.pack(pady=50)

tk.Label(cards_wrap, text="What would you like to do?",
         font=F_LABEL, fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 14))

def dash_card(parent, title, desc, color, command):
    card = tk.Frame(parent, bg=CARD_BG,
                    highlightthickness=1, highlightbackground=LINE_COLOR)
    card.pack(fill="x", pady=5, ipadx=6, ipady=6)

    info = tk.Frame(card, bg=CARD_BG)
    info.pack(side="left", padx=18, pady=6)
    tk.Label(info, text=title, font=("Segoe UI", 12, "bold"),
             fg=TEXT, bg=CARD_BG, anchor="w").pack(anchor="w")
    tk.Label(info, text=desc, font=F_SMALL,
             fg=MUTED, bg=CARD_BG, anchor="w").pack(anchor="w")

    btn(card, "Open", color, command, width=8).pack(side="right", padx=14, pady=10)

dash_card(cards_wrap, "Add New User",  "Register a user with face capture",  GREEN, lambda: show_frame(add_user_frame))
dash_card(cards_wrap, "View Users",    "Browse all registered users",         BLUE,  lambda: [refresh_users(), show_frame(view_frame)])
dash_card(cards_wrap, "Delete Users",  "Remove a user from the system",       RED,   lambda: [refresh_delete_users(), show_frame(delete_frame)])
dash_card(cards_wrap, "Access Log",    "View face scan history with timestamps", BLUE, lambda: [refresh_log(), show_frame(log_frame)])

tk.Frame(cards_wrap, height=1, bg=LINE_COLOR).pack(fill="x", pady=14)
ghost_btn(cards_wrap, "Logout", lambda: show_frame(login_frame)).pack(anchor="w")

# =========================================================
# ================= ADD USER FRAME ========================
# =========================================================

add_user_frame = tk.Frame(root, bg=BG)

top_bar(add_user_frame, "Add New User", lambda: show_frame(dashboard_frame))

au_body = tk.Frame(add_user_frame, bg=BG)
au_body.pack(expand=True, fill="both", padx=40, pady=30)

# Left: form
left_form = tk.Frame(au_body, bg=CARD_BG,
                     highlightthickness=1, highlightbackground=LINE_COLOR)
left_form.pack(side="left", fill="y", padx=(0, 20), ipadx=20, ipady=16)

tk.Label(left_form, text="User Details", font=F_HEAD,
         fg=TEXT, bg=CARD_BG).pack(anchor="w", padx=16, pady=(14, 4))
tk.Frame(left_form, height=1, bg=LINE_COLOR).pack(fill="x", padx=16, pady=(0, 6))

def flbl(t): tk.Label(left_form, text=t, font=F_LABEL, fg=MUTED, bg=CARD_BG).pack(anchor="w", padx=16, pady=(10, 2))
def fent(w=28):
    e = entry(left_form, width=w)
    e.pack(padx=16, ipady=6)
    return e

flbl("Full Name")
name_entry2 = fent()

flbl("Gender")
gender_combo = ttk.Combobox(left_form, values=["Male", "Female", "Other"],
                             state="readonly", width=27, font=F_BODY)
s = ttk.Style()
s.theme_use("default")
s.configure("TCombobox",
             fieldbackground=INPUT_BG, background=INPUT_BG,
             foreground=INPUT_FG, selectbackground=BLUE,
             selectforeground="#fff", bordercolor=LINE_COLOR,
             arrowcolor=MUTED)
gender_combo.pack(padx=16, ipady=5)

flbl("Date of Birth  (DD-MM-YYYY)")
dob_entry = fent()

flbl("Mobile Number")
mobile_entry = fent()

tk.Frame(left_form, height=1, bg=LINE_COLOR).pack(fill="x", padx=16, pady=14)

def register_user():
    name   = name_entry2.get()
    gender = gender_combo.get()
    dob    = dob_entry.get()
    mobile = mobile_entry.get()
    if not name or not gender or not dob or not mobile:
        messagebox.showerror("Error", "All fields required")
        return
    if not captured_path["path"]:
        messagebox.showerror("Error", "Capture image first")
        return
    user_ref.child(name).set({
        "name": name, "gender": gender,
        "dob": dob, "mobile": mobile,
        "registered_on": str(datetime.now())
    })
    messagebox.showinfo("Success", "User Registered Successfully")

btn(left_form, "Register User", GREEN, register_user).pack(padx=16, anchor="w")

# Right: camera
right_cam = tk.Frame(au_body, bg=CARD_BG,
                     highlightthickness=1, highlightbackground=LINE_COLOR)
right_cam.pack(side="left", fill="both", expand=True, ipadx=20, ipady=16)

tk.Label(right_cam, text="Face Photo", font=F_HEAD,
         fg=TEXT, bg=CARD_BG).pack(anchor="w", padx=16, pady=(14, 4))
tk.Frame(right_cam, height=1, bg=LINE_COLOR).pack(fill="x", padx=16, pady=(0, 10))

img_box = tk.Frame(right_cam, bg=INPUT_BG, width=320, height=260,
                   highlightthickness=1, highlightbackground=LINE_COLOR)
img_box.pack(padx=16)
img_box.pack_propagate(False)

image_label = Label(img_box, text="No photo captured yet",
                    font=F_SMALL, fg=MUTED, bg=INPUT_BG)
image_label.place(relx=0.5, rely=0.5, anchor="center")

captured_path = {"path": None}

def capture_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        if not os.path.exists("images"):
            os.makedirs("images")
        name = name_entry2.get()
        if not name:
            messagebox.showerror("Error", "Enter name first")
            return
        path = f"images/{name}.png"
        cv2.imwrite(path, frame)
        captured_path["path"] = path
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img = img.resize((320, 260))
        img = ImageTk.PhotoImage(img)
        image_label.config(image=img, text="")
        image_label.image = img

cam_btns = tk.Frame(right_cam, bg=CARD_BG)
cam_btns.pack(padx=16, pady=12, anchor="w")
btn(cam_btns, "Capture", BLUE,    capture_image).pack(side="left", padx=(0, 8))
btn(cam_btns, "Retake",  CARD_BG, capture_image).pack(side="left")

# =========================================================
# ================= VIEW USERS ============================
# =========================================================

view_frame = tk.Frame(root, bg=BG)
top_bar(view_frame, "All Users", lambda: show_frame(dashboard_frame))

th = tk.Frame(view_frame, bg=SIDEBAR_BG)
th.pack(fill="x", padx=28, pady=(16, 0))
for col, w in [("Name", 22), ("Gender", 10), ("Date of Birth", 16), ("Mobile", 14)]:
    tk.Label(th, text=col, font=("Segoe UI", 10, "bold"),
             fg=MUTED, bg=SIDEBAR_BG,
             width=w, anchor="w").pack(side="left", padx=4, pady=6)
tk.Frame(view_frame, height=1, bg=LINE_COLOR).pack(fill="x", padx=28, pady=4)

user_list_frame = tk.Frame(view_frame, bg=BG)
user_list_frame.pack(fill="both", expand=True, padx=28)

def refresh_users():
    for w in user_list_frame.winfo_children():
        w.destroy()
    users = user_ref.get()
    if users:
        for i, (key, value) in enumerate(users.items()):
            row_bg = CARD_BG if i % 2 == 0 else BG
            row = tk.Frame(user_list_frame, bg=row_bg)
            row.pack(fill="x")
            for val, w in [
                (value.get("name", ""),   22),
                (value.get("gender", ""), 10),
                (value.get("dob", ""),    16),
                (value.get("mobile", ""), 14),
            ]:
                tk.Label(row, text=val, font=F_BODY,
                         fg=TEXT, bg=row_bg,
                         width=w, anchor="w").pack(side="left", padx=4, pady=8)
    else:
        tk.Label(user_list_frame, text="No users found.",
                 font=F_BODY, fg=MUTED, bg=BG).pack(pady=40)

# =========================================================
# ================= DELETE USERS ==========================
# =========================================================

delete_frame = tk.Frame(root, bg=BG)
top_bar(delete_frame, "Delete Users", lambda: show_frame(dashboard_frame))

delete_list_frame = tk.Frame(delete_frame, bg=BG)
delete_list_frame.pack(fill="both", expand=True, padx=28, pady=14)

def refresh_delete_users():
    for w in delete_list_frame.winfo_children():
        w.destroy()
    users = user_ref.get()
    if users:
        for i, (key, value) in enumerate(users.items()):
            row_bg = CARD_BG if i % 2 == 0 else BG
            row = tk.Frame(delete_list_frame, bg=row_bg)
            row.pack(fill="x", pady=1)

            info = tk.Frame(row, bg=row_bg)
            info.pack(side="left", padx=14, pady=8)
            tk.Label(info, text=value.get("name", key),
                     font=("Segoe UI", 11, "bold"),
                     fg=TEXT, bg=row_bg).pack(anchor="w")
            tk.Label(info,
                     text=f"{value.get('gender','')}    {value.get('mobile','')}",
                     font=F_SMALL, fg=MUTED, bg=row_bg).pack(anchor="w")

            btn(row, "Delete", RED, lambda k=key: delete_user(k)).pack(
                side="right", padx=14, pady=8)
    else:
        tk.Label(delete_list_frame, text="No users found.",
                 font=F_BODY, fg=MUTED, bg=BG).pack(pady=40)

def delete_user(user_id):
    user_ref.child(user_id).delete()
    image_path = f"images/{user_id}.png"
    if os.path.exists(image_path):
        os.remove(image_path)
    messagebox.showinfo("Deleted", "User Deleted Successfully")
    refresh_delete_users()

# =========================================================

# =========================================================
# ================= ACCESS LOG ============================
# =========================================================

log_frame = tk.Frame(root, bg=BG)
top_bar(log_frame, "Access Log", lambda: show_frame(dashboard_frame))

# ---- Filter bar ----
filter_bar = tk.Frame(log_frame, bg=BG)
filter_bar.pack(fill="x", padx=28, pady=(14, 0))

tk.Label(filter_bar, text="Filter by status:", font=F_LABEL, fg=MUTED, bg=BG).pack(side="left", padx=(0, 10))

filter_var = tk.StringVar(value="All")
for label in ["All", "GRANTED", "DENIED"]:
    tk.Radiobutton(
        filter_bar, text=label, variable=filter_var, value=label,
        font=F_SMALL, fg=TEXT, bg=BG,
        activeforeground=TEXT, activebackground=BG,
        selectcolor=CARD_BG, indicatoron=False,
        relief="flat", bd=0, padx=10, pady=4,
        cursor="hand2",
        command=lambda: refresh_log()
    ).pack(side="left", padx=4)

# ---- Refresh button ----
btn(filter_bar, "Refresh", CARD_BG, lambda: refresh_log(), width=8).pack(side="right")

# ---- Column header ----
log_header = tk.Frame(log_frame, bg=SIDEBAR_BG)
log_header.pack(fill="x", padx=28, pady=(12, 0))
for col, w in [("#", 4), ("Name", 22), ("Date & Time", 22), ("Status", 10)]:
    tk.Label(
        log_header, text=col, font=("Segoe UI", 10, "bold"),
        fg=MUTED, bg=SIDEBAR_BG,
        width=w, anchor="w"
    ).pack(side="left", padx=4, pady=6)

tk.Frame(log_frame, height=1, bg=LINE_COLOR).pack(fill="x", padx=28, pady=(4, 0))

# ---- Scrollable log list ----
log_canvas = tk.Canvas(log_frame, bg=BG, highlightthickness=0)
log_scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=log_canvas.yview)
log_canvas.configure(yscrollcommand=log_scrollbar.set)

log_scrollbar.pack(side="right", fill="y", padx=(0, 8))
log_canvas.pack(fill="both", expand=True, padx=28, pady=(0, 14))

log_inner = tk.Frame(log_canvas, bg=BG)
log_canvas_window = log_canvas.create_window((0, 0), window=log_inner, anchor="nw")

def _on_log_resize(event):
    log_canvas.itemconfig(log_canvas_window, width=event.width)
log_canvas.bind("<Configure>", _on_log_resize)

def _on_log_scroll(event):
    log_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
log_canvas.bind_all("<MouseWheel>", _on_log_scroll)

log_inner.bind("<Configure>", lambda e: log_canvas.configure(scrollregion=log_canvas.bbox("all")))

def refresh_log():
    for w in log_inner.winfo_children():
        w.destroy()

    raw = db.reference("/access_log").get()
    chosen = filter_var.get()

    if not raw:
        tk.Label(log_inner, text="No access log entries found.",
                 font=F_BODY, fg=MUTED, bg=BG).pack(pady=40)
        return

    # Sort newest first
    entries = sorted(raw.values(), key=lambda x: x.get("timestamp", ""), reverse=True)

    if chosen != "All":
        entries = [e for e in entries if e.get("status", "") == chosen]

    if not entries:
        tk.Label(log_inner, text=f"No {chosen} entries found.",
                 font=F_BODY, fg=MUTED, bg=BG).pack(pady=40)
        return

    for i, entry in enumerate(entries):
        row_bg = CARD_BG if i % 2 == 0 else BG
        row = tk.Frame(log_inner, bg=row_bg)
        row.pack(fill="x")

        status  = entry.get("status", "")
        name    = entry.get("name", "Unknown")
        ts      = entry.get("timestamp", "")
        status_color = GREEN if status == "GRANTED" else RED

        # Serial number
        tk.Label(row, text=str(i + 1), font=F_BODY,
                 fg=MUTED, bg=row_bg, width=4, anchor="w").pack(side="left", padx=4, pady=8)

        # Name
        tk.Label(row, text=name, font=F_BODY,
                 fg=TEXT, bg=row_bg, width=22, anchor="w").pack(side="left", padx=4, pady=8)

        # Timestamp
        tk.Label(row, text=ts, font=F_BODY,
                 fg=MUTED, bg=row_bg, width=22, anchor="w").pack(side="left", padx=4, pady=8)

        # Status badge
        tk.Label(row, text=status, font=("Segoe UI", 10, "bold"),
                 fg=status_color, bg=row_bg, width=10, anchor="w").pack(side="left", padx=4, pady=8)

# =========================================================

frames = [login_frame, dashboard_frame, add_user_frame, view_frame, delete_frame, log_frame]

show_frame(login_frame)

root.mainloop()