"""
Smart Voting System - UI Application
"""
import warnings
warnings.filterwarnings("ignore", message=".*CTkImage.*PhotoImage.*")
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import customtkinter as ctk
import os
import csv
from datetime import datetime

from core.vote_engine import VoteEngine, PARTIES, VOTE_CSV
from core.register_engine import RegisterEngine, FRAMES_TOTAL

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg": "#0f0f14",
    "card": "#1a1a24",
    "accent": "#6366f1",
    "success": "#10b981",
    "error": "#ef4444",
    "text": "#f8fafc",
    "muted": "#94a3b8",
}

PARTY_COLORS = {
    "BJP": ("#ff9933", "#000000"),
    "CONGRESS": ("#22c55e", "#ffffff"),
    "AAP": ("#2563eb", "#ffffff"),
    "NOTA": ("#ec4899", "#ffffff"),
}


def get_vote_count():
    try:
        with open(VOTE_CSV, 'r', encoding='utf-8') as f:
            return max(0, sum(1 for _ in csv.reader(f)) - 1)
    except (FileNotFoundError, csv.Error):
        return 0


class CameraFrame(ctk.CTkFrame):
    def __init__(self, master, width=320, height=240, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.width, self.height = width, height
        self.label = ctk.CTkLabel(self, text="Camera", width=width, height=height,
            fg_color=COLORS["card"], corner_radius=8, text_color=COLORS["muted"])
        self.label.pack()
        self._photo = None

    def update_frame(self, cv_frame):
        if cv_frame is None:
            return
        rgb = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb).resize((self.width, self.height), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(image=img)
        self.label.configure(image=self._photo, text="")


# ========== REGISTER PANEL ==========
class RegisterPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.engine = RegisterEngine()
        self.running = False
        self._after_id = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="New Voter Registration", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"]).pack(pady=(0, 8))
        ctk.CTkLabel(self, text="Enter ID, start capture, wait for 25+ faces (or 51 for best)", font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"]).pack(pady=(0, 12))

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        ctk.CTkLabel(row1, text="Aadhar/ID:", width=80, text_color=COLORS["text"]).pack(side="left", padx=(0, 8))
        self.name_entry = ctk.CTkEntry(row1, placeholder_text="e.g. 12345", width=200, height=36)
        self.name_entry.pack(side="left", padx=(0, 12))
        self.start_btn = ctk.CTkButton(row1, text="Start Capture", width=120, height=36,
            fg_color=COLORS["accent"], command=self._start)
        self.start_btn.pack(side="left", padx=4)
        self.stop_btn = ctk.CTkButton(row1, text="Stop", width=80, height=36, fg_color=COLORS["error"],
            command=self._stop, state="disabled")
        self.stop_btn.pack(side="left", padx=4)
        self.save_btn = ctk.CTkButton(row1, text="Save & Register", width=120, height=36,
            fg_color=COLORS["success"], command=self._save, state="disabled")
        self.save_btn.pack(side="left", padx=4)

        self.camera = CameraFrame(self, width=320, height=240)
        self.camera.pack(pady=12)
        self.progress_label = ctk.CTkLabel(self, text="Press Start Capture", font=ctk.CTkFont(size=13),
            text_color=COLORS["muted"])
        self.progress_label.pack(pady=4)
        self.progress = ctk.CTkProgressBar(self, width=400, height=8)
        self.progress.pack(pady=4)
        self.progress.set(0)

    def _start(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Error", "Enter Aadhar/ID first.")
            return
        self.engine.faces_data = []
        self.engine.frame_counter = 0
        if not self.engine.start_camera():
            messagebox.showerror("Error", "Cannot open camera.")
            return
        self.running = True
        self.start_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress.set(0)
        self.progress_label.configure(text="Capturing... Keep face in frame")
        self._loop()

    def _loop(self):
        if not self.running or not self.engine.video:
            return
        ok, frame, count = self.engine.capture_frame()
        if ok and frame is not None:
            self.camera.update_frame(frame)
        self.progress.set(min(1.0, count / FRAMES_TOTAL))
        self.progress_label.configure(text=f"Faces: {count} / {FRAMES_TOTAL}")
        if count >= FRAMES_TOTAL:
            self.running = False
            if self._after_id:
                self.after_cancel(self._after_id)
            self.engine.stop_camera()
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.save_btn.configure(state="normal")
            self.progress_label.configure(text=f"Complete! {count} faces. Click Save & Register")
            return
        if count >= 25:
            self.save_btn.configure(state="normal")
        self._after_id = self.after(30, self._loop)

    def _stop(self):
        self.running = False
        if self._after_id:
            self.after_cancel(self._after_id)
        self.engine.stop_camera()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        c = len(self.engine.faces_data)
        self.progress_label.configure(text=f"Stopped. Got {c} faces.")
        if c >= 25:
            self.save_btn.configure(state="normal")

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Error", "Enter Aadhar/ID.")
            return
        ok, msg = self.engine.save_registration(name)
        self.engine.stop_camera()
        self.save_btn.configure(state="disabled")
        self.progress.set(0)
        self.progress_label.configure(text="Press Start Capture")
        if ok:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

    def stop_if_running(self):
        if self.running:
            self._stop()


# ========== VOTE PANEL ==========
class VotePanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.engine = None
        self.running = False
        self.current_voter = None
        self._after_id = None
        self._build()

    def _build(self):
        # STEP 1: Recognize button - AT TOP
        ctk.CTkLabel(self, text="Cast Your Vote", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"]).pack(pady=(0, 4))
        ctk.CTkLabel(self, text="Step 1: Click Recognize   Step 2: Click your party", font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"]).pack(pady=(0, 12))

        self.recognize_btn = ctk.CTkButton(
            self, text="Recognize Me Now",
            width=200, height=50, font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS["accent"], command=self._recognize,
        )
        self.recognize_btn.pack(pady=(0, 16))

        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=14), text_color=COLORS["accent"])
        self.status_label.pack(pady=4)

        # STEP 2: Vote buttons - BIG, VISIBLE
        ctk.CTkLabel(self, text="Step 2: Choose your vote", font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"]).pack(pady=(16, 8))
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=8)
        self.vote_buttons = {}
        labels = ["1. BJP", "2. CONGRESS", "3. AAP", "4. NOTA"]
        for i, party in enumerate(PARTIES):
            fg, txt = PARTY_COLORS[party]
            btn = ctk.CTkButton(
                btn_frame, text=labels[i], width=160, height=55,
                font=ctk.CTkFont(size=16, weight="bold"),
                fg_color=fg, text_color=txt,
                command=lambda p=party: self._cast(p), state="disabled",
            )
            self.vote_buttons[party] = btn
            btn.grid(row=i // 2, column=i % 2, padx=12, pady=10)
        self.rescan_btn = ctk.CTkButton(self, text="Rescan", width=100, height=36,
            fg_color="transparent", text_color=COLORS["muted"], command=self._rescan, state="disabled")
        self.rescan_btn.pack(pady=12)

        # Camera - smaller, at bottom
        self.camera = CameraFrame(self, width=320, height=240)
        self.camera.pack(pady=16)

    def _recognize(self):
        if self.engine is None:
            self.engine = VoteEngine()
        else:
            self.engine.reload_model()
        if not self.engine.knn:
            self.status_label.configure(text="Register first in Register tab.", text_color=COLORS["error"])
            return
        if not self.engine.video or not self.engine.video.isOpened():
            self.engine.start_camera()
        if not self.engine.video or not self.engine.video.isOpened():
            self.status_label.configure(text="Camera error.", text_color=COLORS["error"])
            return
        ok, frame, name = self.engine.get_frame_with_detection()
        if ok and frame is not None:
            self.camera.update_frame(frame)
        if not name:
            self.status_label.configure(text="No face. Look at camera and try again.", text_color=COLORS["error"])
            return
        name_str = str(name).strip()
        if self.engine.check_already_voted(name_str):
            self.engine.speak_already_voted()
            self.status_label.configure(text="Already voted.", text_color=COLORS["error"])
            return
        self.current_voter = name_str
        self.status_label.configure(text=f"Identified: {name_str} - Click your vote!", text_color=COLORS["success"])
        for b in self.vote_buttons.values():
            b.configure(state="normal")
        self.rescan_btn.configure(state="normal")

    def _rescan(self):
        self.current_voter = None
        for b in self.vote_buttons.values():
            b.configure(state="disabled")
        self.rescan_btn.configure(state="disabled")
        self.status_label.configure(text="Click Recognize Me Now")

    def _cast(self, party):
        if not self.current_voter or not self.engine:
            return
        for b in self.vote_buttons.values():
            b.configure(state="disabled")
        self.rescan_btn.configure(state="disabled")
        ok, msg = self.engine.cast_vote(str(self.current_voter).strip(), party)
        self.status_label.configure(text="Thank you! Vote recorded.", text_color=COLORS["success"])
        self.current_voter = None
        self.engine.stop_camera()
        if self._after_id:
            self.after_cancel(self._after_id)
        self.after(3000, self._reset)

    def _reset(self):
        self.status_label.configure(text="Click Recognize Me Now", text_color=COLORS["accent"])
        self.start_voting()

    def _camera_loop(self):
        if not self.running or not self.engine or not self.engine.video:
            return
        if not self.engine.video.isOpened():
            return
        ok, frame, _ = self.engine.get_frame_with_detection()
        if ok and frame is not None:
            self.camera.update_frame(frame)
        self._after_id = self.after(33, self._camera_loop)

    def start_voting(self):
        if self.engine is None:
            self.engine = VoteEngine()
        else:
            self.engine.reload_model()
        if not self.engine.knn:
            self.status_label.configure(text="Register first in Register tab.", text_color=COLORS["error"])
            return
        if self.engine.start_camera():
            self.running = True
            self.status_label.configure(text="Face camera, then click Recognize Me Now", text_color=COLORS["accent"])
            self._camera_loop()
        else:
            self.status_label.configure(text="Camera error.", text_color=COLORS["error"])

    def stop_voting(self):
        self.running = False
        if self._after_id:
            self.after_cancel(self._after_id)
        if self.engine:
            self.engine.stop_camera()


# ========== MAIN APP ==========
def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app = ctk.CTk()
    app.title("Smart Voting System")
    app.geometry("900x750")
    app.minsize(700, 600)
    app.configure(fg_color=COLORS["bg"])

    ctk.CTkLabel(app, text="Smart Voting System", font=ctk.CTkFont(size=24, weight="bold"),
        text_color=COLORS["text"]).pack(pady=(20, 8))
    ctk.CTkLabel(app, text="Register | Vote", font=ctk.CTkFont(size=12),
        text_color=COLORS["muted"]).pack(pady=(0, 16))

    tabview = ctk.CTkTabview(app, width=800, height=580)
    tabview.pack(padx=20, pady=(0, 20))
    tabview.add("Register")
    tabview.add("Vote")

    reg = RegisterPanel(tabview.tab("Register"))
    reg.pack(fill="both", expand=True, padx=20, pady=20)
    vote = VotePanel(tabview.tab("Vote"))
    vote.pack(fill="both", expand=True, padx=20, pady=20)

    app._last_tab = "Vote" # type: ignore
    app._poll = lambda: None # type: ignore

    def poll():
        t = tabview.get()
        if t != app._last_tab: # type: ignore
            app._last_tab = t # type: ignore
            if t == "Vote":
                reg.stop_if_running()
                vote.start_voting()
            else:
                vote.stop_voting()
        app.after(300, poll)
    app._poll = poll # type: ignore
    app.after(500, vote.start_voting)
    app.after(600, poll)

    def close():
        vote.stop_voting()
        reg.engine.stop_camera()
        app.destroy()
    app.protocol("WM_DELETE_WINDOW", close)
    app.mainloop()


if __name__ == "__main__":
    main()
