import cv2
import face_recognition
import firebase_admin
from firebase_admin import credentials, db
import os
import tkinter as tk
from tkinter import Label, Button, ttk
from PIL import Image, ImageTk
import numpy as np
import time
from datetime import datetime
import subprocess
import sys
import requests
import dlib
from skimage.feature import local_binary_pattern

# ================= TELEGRAM CONFIG =================
TELEGRAM_BOT_TOKEN = "8456263810:AAGMQ8AoTaAKU5OL5OqBZbOsnrmN-iDVEgY"
TELEGRAM_CHAT_ID = "6444617298"

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, data=data)
        print("Telegram Message Response:", response.text)
    except Exception as e:
        print("Telegram Message Error:", e)

def send_telegram_photo_from_frame(frame):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        _, buffer = cv2.imencode(".jpg", frame)
        files = {"photo": ("intruder.jpg", buffer.tobytes())}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "Intruder Detected!"}
        response = requests.post(url, data=data, files=files)
        print("Telegram Photo Response:", response.text)
    except Exception as e:
        print("Telegram Photo Error:", e)

# ================= FIREBASE INIT =================
cred = credentials.Certificate("firebase_config.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://face-recognition-securit-5dd85-default-rtdb.firebaseio.com/"
})

# ================= LOAD FACES =================
def load_known_faces():
    encodings = []
    names = []
    image_folder = "images/"
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
    for filename in os.listdir(image_folder):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            path = os.path.join(image_folder, filename)
            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                encodings.append(encoding[0])
                names.append(filename.split('.')[0])
    return encodings, names

known_face_encodings, known_face_names = load_known_faces()

# ================= DLIB SETUP =================
dlib_detector  = dlib.get_frontal_face_detector()
dlib_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Eye landmark indices (dlib 68-point model)
LEFT_EYE  = list(range(36, 42))
RIGHT_EYE = list(range(42, 48))

# ================= ANTI-SPOOFING HELPERS =================
def eye_aspect_ratio(landmarks, eye_indices):
    pts = [(landmarks.part(i).x, landmarks.part(i).y) for i in eye_indices]
    # vertical distances
    A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    # horizontal distance
    C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    return (A + B) / (2.0 * C)

def check_lbp_texture(gray_face):
    """Returns True if texture looks like real skin (not a flat photo/screen)."""
    if gray_face.size == 0:
        return False
    face_resized = cv2.resize(gray_face, (64, 64))
    lbp = local_binary_pattern(face_resized, P=8, R=1, method="uniform")
    hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 11), range=(0, 10))
    hist = hist.astype("float")
    hist /= (hist.sum() + 1e-6)
    # Real skin has varied LBP distribution; flat photos/screens are too uniform
    entropy = -np.sum(hist * np.log2(hist + 1e-6))
    return entropy > 2.5   # threshold tuned for webcam conditions

# ================= STATE VARIABLES =================
video_capture       = None
selected_camera     = 0
running             = False
scan_start_time     = 0
unauthorized_detected = False

SCAN_TIMEOUT    = 10
UNLOCK_DURATION = 5
last_status     = None

# Anti-spoofing state (reset each scan session)
EAR_THRESHOLD  = 0.22
BLINK_CONSEC   = 2
blink_counter  = 0
blink_detected = False
texture_ok     = False

# ================= COLORS (same as admin panel) =================
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

# ================= FONTS =================
F_TITLE = ("Segoe UI", 22, "bold")
F_HEAD  = ("Segoe UI", 15, "bold")
F_LABEL = ("Segoe UI", 12, "bold")
F_BODY  = ("Segoe UI", 12)
F_BTN   = ("Segoe UI", 12, "bold")
F_SMALL = ("Segoe UI", 11, "bold")

# ================= HELPERS =================
def solid_btn(parent, text, color, command, width=None):
    kw = dict(
        text=text, font=F_BTN,
        fg="#ffffff", bg=color,
        activeforeground="#ffffff", activebackground=color,
        relief="flat", bd=0,
        padx=18, pady=10,
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

def ghost_btn(parent, text, command):
    b = tk.Button(
        parent, text=text, font=F_SMALL,
        fg=MUTED, bg=CARD_BG,
        activeforeground=TEXT, activebackground=CARD_BG,
        relief="flat", bd=0, cursor="hand2", command=command
    )
    b.bind("<Enter>", lambda e: b.config(fg=TEXT))
    b.bind("<Leave>", lambda e: b.config(fg=MUTED))
    return b

# ================= ADMIN PANEL =================
def open_admin_panel():
    subprocess.Popen([sys.executable, "admin.py"])

# ================= FIREBASE UPDATE =================
def update_firebase(status):
    global last_status
    if status == last_status:
        return
    try:
        ref = db.reference("/door_lock")
        if status == "Yes":
            ref.set({"access": "Yes", "command": "UNLOCK"})
        else:
            ref.set({"access": "No", "command": "LOCK"})
        last_status = status
    except Exception as e:
        print("Firebase Error:", e)

# ================= ACCESS LOG =================
def log_access_to_firebase(name, status):
    try:
        log_ref = db.reference("/access_log")
        log_ref.push({
            "name": name,
            "status": status,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        print("Log Error:", e)

# ================= AUTO LOCK =================
def auto_lock():
    update_firebase("No")
    # restore locked state
    status_dot.config(bg=RED)
    door_label.config(text="Door: Locked", fg=RED)
    access_label.config(text="Waiting for scan...", fg=MUTED)
    close_camera()

# ================= CAMERA =================
def open_camera():
    global video_capture, running, scan_start_time, unauthorized_detected
    global blink_counter, blink_detected, texture_ok
    if running:
        return
    unauthorized_detected = False
    blink_counter  = 0
    blink_detected = False
    texture_ok     = False
    video_capture = cv2.VideoCapture(selected_camera)
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    running = True
    scan_start_time = time.time()
    access_label.config(text="Scanning face...", fg=BLUE)
    scan_face()

def close_camera():
    global video_capture, running
    running = False
    if video_capture:
        video_capture.release()
        video_capture = None
    canvas.delete("all")
    # draw idle placeholder
    canvas.create_text(
        360, 240,
        text="Camera off",
        fill=MUTED,
        font=F_SMALL
    )

# ================= FACE SCAN =================
def scan_face():
    global running, unauthorized_detected, scan_start_time
    global blink_counter, blink_detected, texture_ok

    if not running or video_capture is None:
        return

    ret, frame = video_capture.read()
    if not ret:
        return

    # 0.5x scale for reliable multi-face detection
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_frame   = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    gray_frame  = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

    face_locations = face_recognition.face_locations(rgb_frame)

    # ---- Block multiple faces ----
    if len(face_locations) > 1:
        scan_start_time = time.time()
        access_label.config(
            text=f"Multiple faces detected ({len(face_locations)})  —  please scan one person at a time",
            fg=RED
        )
        status_dot.config(bg=RED)
        door_label.config(text="Door: Locked", fg=RED)
        _draw_camera_frame(frame)
        canvas.create_text(
            360, 20,
            text=f"WARNING: {len(face_locations)} faces detected — one person only",
            fill=RED, font=F_SMALL
        )
        if running:
            canvas.after(20, scan_face)
        return

    # ---- No face in frame ----
    if len(face_locations) == 0:
        access_label.config(text="No face detected — please look at the camera", fg=MUTED)
        _draw_camera_frame(frame)
        if running:
            canvas.after(20, scan_face)
        return

    # ---- Single face: run anti-spoofing ----
    top, right, bottom, left = face_locations[0]

    # 1. LBP Texture check
    face_gray = gray_frame[top:bottom, left:right]
    if not texture_ok:
        texture_ok = check_lbp_texture(face_gray)

    # 2. Blink detection via dlib landmarks
    dlib_rect  = dlib.rectangle(left, top, right, bottom)
    landmarks  = dlib_predictor(gray_frame, dlib_rect)
    left_ear   = eye_aspect_ratio(landmarks, LEFT_EYE)
    right_ear  = eye_aspect_ratio(landmarks, RIGHT_EYE)
    ear        = (left_ear + right_ear) / 2.0

    if ear < EAR_THRESHOLD:
        blink_counter += 1
    else:
        if blink_counter >= BLINK_CONSEC:
            blink_detected = True
        blink_counter = 0

    # ---- Show live liveness status on UI ----
    blink_status   = "Blink detected" if blink_detected   else "Waiting for blink..."
    texture_status = "Texture OK"     if texture_ok       else "Checking texture..."

    if not blink_detected or not texture_ok:
        access_label.config(
            text=f"Liveness check  —  {blink_status}  |  {texture_status}",
            fg=BLUE
        )
        status_dot.config(bg=RED)
        door_label.config(text="Door: Locked", fg=RED)
        _draw_camera_frame(frame)

        # Timeout with no liveness = spoof attempt
        if (time.time() - scan_start_time > SCAN_TIMEOUT) and not unauthorized_detected:
            unauthorized_detected = True
            running = False
            message = f"ALERT!\nSpoof/unauthorized attempt detected!\nTime: {datetime.now()}"
            send_telegram_alert(message)
            send_telegram_photo_from_frame(frame)
            log_access_to_firebase("Unknown", "DENIED")
            access_label.config(text="Access denied  —  Spoof detected, alert sent", fg=RED)
            close_camera()
            return

        if running:
            canvas.after(20, scan_face)
        return

    # ---- Both checks passed: now run face recognition ----
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    recognized     = False
    detected_name  = "Unknown"

    for face_encoding in face_encodings:
        if len(known_face_encodings) == 0:
            break
        face_distances    = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index  = np.argmin(face_distances)
        if face_distances[best_match_index] < 0.5:
            recognized    = True
            detected_name = known_face_names[best_match_index]
        break

    if recognized:
        access_label.config(text=f"Access granted  —  {detected_name}", fg=GREEN)
        status_dot.config(bg=GREEN)
        door_label.config(text="Door: Unlocked", fg=GREEN)
        update_firebase("Yes")
        log_access_to_firebase(detected_name, "GRANTED")
        running = False
        app.after(UNLOCK_DURATION * 1000, auto_lock)
    else:
        access_label.config(text="Face not recognized  —  Access denied", fg=RED)
        status_dot.config(bg=RED)
        door_label.config(text="Door: Locked", fg=RED)
        update_firebase("No")

        if (time.time() - scan_start_time > SCAN_TIMEOUT) and not unauthorized_detected:
            unauthorized_detected = True
            running = False
            message = f"ALERT!\nUnauthorized person detected!\nTime: {datetime.now()}"
            send_telegram_alert(message)
            send_telegram_photo_from_frame(frame)
            log_access_to_firebase("Unknown", "DENIED")
            access_label.config(text="Access denied  —  Alert sent", fg=RED)
            close_camera()
            return

    _draw_camera_frame(frame)

    if running:
        canvas.after(20, scan_face)

# ================= CAMERA DRAW HELPER =================
def _draw_camera_frame(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)

    canvas_w, canvas_h = 720, 400
    img_ratio = img.width / img.height
    canvas_ratio = canvas_w / canvas_h

    if img_ratio > canvas_ratio:
        new_w = canvas_w
        new_h = int(canvas_w / img_ratio)
    else:
        new_h = canvas_h
        new_w = int(canvas_h * img_ratio)

    img = img.resize((new_w, new_h))
    imgtk = ImageTk.PhotoImage(image=img)

    canvas.delete("all")
    x_off = (canvas_w - new_w) // 2
    y_off = (canvas_h - new_h) // 2
    canvas.create_image(x_off, y_off, anchor=tk.NW, image=imgtk)
    canvas.image = imgtk

# ================= CAMERA SELECTION =================
def select_camera(event):
    global selected_camera
    selected_camera = int(camera_selection.get().split()[0])

# ================= UI =================
app = tk.Tk()
app.title("FaceLock — Door Security")
app.geometry("980x800")
app.configure(bg=BG)

# ---- Top bar ----
topbar = tk.Frame(app, bg=SIDEBAR_BG, pady=16)
topbar.pack(fill="x")

tk.Label(topbar, text="FaceLock", font=F_TITLE, fg=TEXT, bg=SIDEBAR_BG).pack(side="left", padx=24)
tk.Label(topbar, text="AI Door Security System", font=F_SMALL, fg=MUTED, bg=SIDEBAR_BG).pack(side="left", padx=4, pady=6)

ghost_btn(topbar, "Admin Panel →", open_admin_panel).pack(side="right", padx=20)

tk.Frame(app, height=1, bg=LINE_COLOR).pack(fill="x")

# ---- Main body ----
body = tk.Frame(app, bg=BG)
body.pack(fill="both", expand=True, padx=30, pady=24)

# ---- Status row ----
status_row = tk.Frame(body, bg=CARD_BG,
                      highlightthickness=1, highlightbackground=LINE_COLOR)
status_row.pack(fill="x", pady=(0, 16))

status_inner = tk.Frame(status_row, bg=CARD_BG)
status_inner.pack(fill="x", padx=20, pady=14)

# left: access status
left_status = tk.Frame(status_inner, bg=CARD_BG)
left_status.pack(side="left")

tk.Label(left_status, text="Status", font=F_LABEL, fg=MUTED, bg=CARD_BG).pack(anchor="w")
access_label = tk.Label(left_status, text="Waiting for scan...",
                        font=F_HEAD, fg=MUTED, bg=CARD_BG)
access_label.pack(anchor="w")

# right: door lock indicator
right_status = tk.Frame(status_inner, bg=CARD_BG)
right_status.pack(side="right")

dot_row = tk.Frame(right_status, bg=CARD_BG)
dot_row.pack(anchor="e")

status_dot = tk.Label(dot_row, text="  ", bg=RED,
                      width=2, relief="flat")
status_dot.pack(side="left", padx=(0, 8))

door_label = tk.Label(dot_row, text="Door: Locked",
                      font=F_LABEL, fg=RED, bg=CARD_BG)
door_label.pack(side="left")

# ---- Camera canvas ----
cam_wrap = tk.Frame(body, bg=CARD_BG,
                    highlightthickness=1, highlightbackground=LINE_COLOR)
cam_wrap.pack(fill="x")

canvas = tk.Canvas(cam_wrap, width=720, height=400,
                   bg=INPUT_BG, highlightthickness=0)
canvas.pack(padx=16, pady=16)

canvas.create_text(360, 200, text="Camera off", fill=MUTED, font=F_SMALL)

# ---- Camera selector ----
cam_sel_row = tk.Frame(body, bg=BG)
cam_sel_row.pack(fill="x", pady=(14, 0))

tk.Label(cam_sel_row, text="Camera", font=F_LABEL, fg=MUTED, bg=BG).pack(side="left", padx=(0, 10))

s = ttk.Style()
s.theme_use("default")
s.configure("TCombobox",
             fieldbackground=INPUT_BG, background=INPUT_BG,
             foreground=TEXT, selectbackground=BLUE,
             selectforeground="#fff", bordercolor=LINE_COLOR,
             arrowcolor=MUTED)

camera_selection = ttk.Combobox(
    cam_sel_row,
    values=["0 (Main Camera)", "1 (External Camera)"],
    state="readonly", width=22, font=F_BODY
)
camera_selection.current(0)
camera_selection.pack(side="left", ipady=4)
camera_selection.bind("<<ComboboxSelected>>", select_camera)

# ---- Action buttons ----
btn_row = tk.Frame(body, bg=BG)
btn_row.pack(fill="x", pady=18)

solid_btn(btn_row, "Start Scan",  GREEN, open_camera,  width=14).pack(side="left", padx=(0, 10))
solid_btn(btn_row, "Stop Camera", RED,   close_camera, width=14).pack(side="left")

app.mainloop()