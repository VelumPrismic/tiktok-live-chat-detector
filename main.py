import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import os
import time
import asyncio
from datetime import datetime, timezone, timedelta
import obsws_python as obs
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent
from collections import deque

# --- CONFIGURATION FILE PATH ---
CONFIG_FILE = "tiktok_obs_config.json"

class TikTokOBSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok OBS Auto-Clipper")
        self.root.geometry("650x850")
        self.root.configure(bg="#2d2d2d")
        
        # State Variables
        self.obs_client = None
        self.tiktok_client = None
        self.is_monitoring = False
        self.log_file_path = ""
        self.trigger_file_path = ""
        self.triggers_list = []
        self.current_loop = None
        self.client_thread = None
        
        # Notification State
        self.notification_queue = deque()
        self.is_showing_notification = False

        # Style Configuration
        self._configure_styles()
        self._build_ui()
        self._load_config()

    def _configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors
        bg_color = "#2d2d2d"
        frame_bg = "#363636"
        text_color = "#f0f0f0"
        accent_color = "#00e5ff"
        
        self.style.configure("TLabel", background=frame_bg, foreground=text_color, font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), borderwidth=0, focuscolor="none")
        self.style.configure("Header.TLabel", background=bg_color, font=("Segoe UI", 18, "bold"), foreground=accent_color)
        self.style.configure("TFrame", background=frame_bg)
        self.style.configure("Main.TFrame", background=bg_color)
        
        self.style.configure("TLabelframe", background=frame_bg, foreground=accent_color, borderwidth=0)
        self.style.configure("TLabelframe.Label", background=frame_bg, foreground=accent_color, font=("Segoe UI", 11, "bold"))
        self.style.map("TButton", background=[('active', '#444444')])

    def _build_ui(self):
        # === Main Container ===
        main_container = ttk.Frame(self.root, style="Main.TFrame")
        main_container.pack(fill="both", expand=True, padx=25, pady=25)

        # === Header ===
        header_frame = ttk.Frame(main_container, style="Main.TFrame")
        header_frame.pack(pady=(0, 25), fill="x")
        ttk.Label(header_frame, text="TikTok Live OBS Manager", style="Header.TLabel").pack(side="left")
        
        # === Configuration Section ===
        config_container = ttk.Frame(main_container, style="TFrame")
        config_container.pack(pady=10, fill="x")
        
        config_frame = ttk.LabelFrame(config_container, text=" Configuration ", padding=(20, 20))
        config_frame.pack(fill="x", padx=2, pady=2)

        # Grid Layout
        grid_opts = {'sticky': 'w', 'pady': 10}
        entry_opts = {'sticky': 'ew', 'padx': (15, 0), 'pady': 10}

        ttk.Label(config_frame, text="TikTok Username:").grid(row=0, column=0, **grid_opts)
        self.entry_user = tk.Entry(config_frame, bg="#404040", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 11))
        self.entry_user.grid(row=0, column=1, **entry_opts)
        
        ttk.Label(config_frame, text="OBS Password:").grid(row=1, column=0, **grid_opts)
        self.entry_pass = tk.Entry(config_frame, bg="#404040", fg="white", insertbackground="white", show="*", relief="flat", font=("Segoe UI", 11))
        self.entry_pass.grid(row=1, column=1, **entry_opts)

        ttk.Label(config_frame, text="OBS Source Name:").grid(row=2, column=0, **grid_opts)
        self.entry_source = tk.Entry(config_frame, bg="#404040", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 11))
        self.entry_source.insert(0, "Window Capture")
        self.entry_source.grid(row=2, column=1, **entry_opts)
        
        ttk.Label(config_frame, text="Trigger Keywords:").grid(row=3, column=0, **grid_opts)
        self.entry_keywords = tk.Entry(config_frame, bg="#404040", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 11))
        self.entry_keywords.insert(0, "mine, code, lock, ssd")
        self.entry_keywords.grid(row=3, column=1, **entry_opts)
        
        ttk.Label(config_frame, text="(Comma separated)", font=("Segoe UI", 9), foreground="#aaaaaa").grid(row=4, column=1, sticky="w", padx=15)
        config_frame.columnconfigure(1, weight=1)

        # === Control Buttons ===
        btn_frame = ttk.Frame(main_container, style="Main.TFrame")
        btn_frame.pack(pady=25, fill="x")

        self.btn_obs = tk.Button(btn_frame, text="1. Connect OBS", bg="#3498db", fg="white", 
                                 font=("Segoe UI", 11, "bold"), relief="flat", padx=25, pady=12,
                                 activebackground="#5dade2", activeforeground="white", cursor="hand2",
                                 command=self.setup_obs)
        self.btn_obs.pack(side="left", fill="x", expand=True, padx=(0, 15))

        self.btn_start = tk.Button(btn_frame, text="2. Start Monitor", bg="#2ecc71", fg="white", 
                                   font=("Segoe UI", 11, "bold"), relief="flat", padx=25, pady=12,
                                   activebackground="#58d68d", activeforeground="white", cursor="hand2",
                                   command=self.toggle_monitoring)
        self.btn_start.pack(side="right", fill="x", expand=True, padx=(15, 0))

        # === Logs ===
        log_container = ttk.Frame(main_container, style="TFrame")
        log_container.pack(pady=10, fill="both", expand=True)
        
        log_frame = ttk.LabelFrame(log_container, text=" Live Logs ", padding=(5, 5))
        log_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, bg="#1e1e1e", fg="#e0e0e0", 
                                                  font=("Consolas", 10), state="disabled", borderwidth=0)
        self.log_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_area.tag_config("info", foreground="#dddddd")
        self.log_area.tag_config("success", foreground="#2ecc71")
        self.log_area.tag_config("error", foreground="#e74c3c")
        self.log_area.tag_config("trigger", foreground="#f1c40f", font=("Consolas", 10, "bold"))

    def log(self, message, tag="info"):
        """Thread-safe logging to the text area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}\n"
        def _update():
            self.log_area.configure(state="normal")
            self.log_area.insert("end", full_msg, tag)
            self.log_area.see("end")
            self.log_area.configure(state="disabled")
        self.root.after(0, _update)

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.entry_user.insert(0, data.get("username", ""))
                    self.entry_pass.insert(0, data.get("obs_password", ""))
                    
                    saved_source = data.get("source_name", "")
                    if saved_source:
                        self.entry_source.delete(0, "end")
                        self.entry_source.insert(0, saved_source)
                        
                    saved_keywords = data.get("keywords", "")
                    if saved_keywords:
                        self.entry_keywords.delete(0, "end")
                        self.entry_keywords.insert(0, saved_keywords)
            except Exception as e:
                self.log(f"Failed to load config: {e}", "error")

    def _save_config(self):
        data = {
            "username": self.entry_user.get(),
            "obs_password": self.entry_pass.get(),
            "source_name": self.entry_source.get(),
            "keywords": self.entry_keywords.get()
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            self.log(f"Failed to save config: {e}", "error")

    def setup_obs(self):
        self._save_config()
        password = self.entry_pass.get()
        source_name = self.entry_source.get()

        if not password:
            messagebox.showerror("Error", "Please enter OBS Password")
            return

        def _run_obs_setup():
            self.log("Connecting to OBS...", "info")
            try:
                self.obs_client = obs.ReqClient(host="localhost", port=4455, password=password)
                self.log("✅ Connected to OBS WebSocket!", "success")
                try:
                    status = self.obs_client.get_replay_buffer_status()
                    if not status.output_active:
                        self.obs_client.start_replay_buffer()
                        self.log("✅ Replay Buffer STARTED.", "success")
                    else:
                        self.log("✅ Replay Buffer is already running.", "success")
                except Exception as e:
                    self.log(f"⚠️ Replay Buffer check failed: {e}", "error")
            except Exception as e:
                self.log(f"❌ OBS Connection Failed: {e}", "error")
                self.obs_client = None
        threading.Thread(target=_run_obs_setup, daemon=True).start()

    # === NOTIFICATION SYSTEM ===
    def trigger_notification(self, user, message, keyword):
        self.notification_queue.append((user, message, keyword))
        if not self.is_showing_notification:
            self.process_notification_queue()

    def process_notification_queue(self):
        if not self.notification_queue:
            self.is_showing_notification = False
            return

        self.is_showing_notification = True
        user, message, keyword = self.notification_queue.popleft()
        self.root.after(0, lambda: self.show_popup(user, message, keyword))

    def show_popup(self, user, message, keyword):
        popup = tk.Toplevel(self.root)
        popup.title("Trigger Word Alert!")
        
        # Notification Dimensions
        width = 450
        height = 220
        
        # Position (Center)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_c = int((screen_width/2) - (width/2))
        y_c = int((screen_height/2) - (height/2))
        popup.geometry(f"{width}x{height}+{x_c}+{y_c}")
        
        popup.overrideredirect(True) # Remove title bar
        popup.attributes('-topmost', True)
        popup.configure(bg="#2c3e50")
        
        # --- HEADER (Orange) ---
        header = tk.Frame(popup, bg="#e67e22", height=50)
        header.pack(fill="x", side="top")
        header.pack_propagate(False) # Keep height fixed
        
        # Icon placeholder (Star)
        icon_lbl = tk.Label(header, text="✷", bg="#e67e22", fg="white", font=("Segoe UI", 24))
        icon_lbl.pack(side="left", padx=(10, 5))
        
        # Title Text
        title_frame = tk.Frame(header, bg="#e67e22")
        title_frame.pack(side="left", fill="y", pady=5)
        tk.Label(title_frame, text="Trigger Word Alert!", bg="#e67e22", fg="white", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        
        # Time
        gmt8 = timezone(timedelta(hours=8))
        current_time = datetime.now(gmt8).strftime("%H:%M:%S GMT+8")
        tk.Label(title_frame, text=current_time, bg="#e67e22", fg="#ffe0b2", font=("Segoe UI", 8)).pack(anchor="w")
        
        # Close Button (X)
        close_btn = tk.Label(header, text="✕", bg="#e67e22", fg="white", font=("Segoe UI", 14), cursor="hand2")
        close_btn.pack(side="right", padx=10)
        close_btn.bind("<Button-1>", lambda e: close_popup())
        
        # --- BODY (Dark) ---
        body = tk.Frame(popup, bg="#2c3e50")
        body.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Streamer Info
        target_user = self.entry_user.get()
        tk.Label(body, text=f"Stream: @{target_user}", bg="#2c3e50", fg="white", font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(body, text=f"User: {user}", bg="#2c3e50", fg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Keyword Message
        tk.Label(body, text=f"\"{message}\"", bg="#2c3e50", fg="#f39c12", font=("Segoe UI", 16, "bold"), wraplength=420, justify="left").pack(anchor="w", pady=5)
        
        # Replay Buffer Badge
        badge_frame = tk.Frame(body, bg="#2c3e50")
        badge_frame.pack(anchor="w", pady=5)
        tk.Label(badge_frame, text="✓", bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), width=2).pack(side="left")
        tk.Label(badge_frame, text=" Replay Buffer Saved!", bg="#2c3e50", fg="#27ae60", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        
        # Footer Timer
        footer_lbl = tk.Label(popup, text="Automatically dismisses in 5 seconds...", bg="#2c3e50", fg="#7f8c8d", font=("Segoe UI", 8))
        footer_lbl.pack(side="bottom", pady=5)

        # Animation & Close Logic
        popup.attributes('-alpha', 0.0)
        
        def fade_in(alpha=0):
            if alpha < 1.0:
                alpha += 0.1
                popup.attributes('-alpha', alpha)
                popup.after(20, lambda: fade_in(alpha))
            else:
                start_timer(5)

        def start_timer(seconds):
            if seconds > 0:
                footer_lbl.config(text=f"Automatically dismisses in {seconds} seconds...")
                popup.after(1000, lambda: start_timer(seconds - 1))
            else:
                close_popup()

        def close_popup():
            if popup.winfo_exists():
                popup.destroy()
            self.process_notification_queue()

        fade_in()

    def toggle_monitoring(self):
        if self.is_monitoring:
            self.log("Stopping monitoring...", "info")
            self.is_monitoring = False
            
            # Force disconnect logic
            if self.tiktok_client:
                try:
                    # If we have a loop and client, try to stop safely
                    if self.current_loop and self.current_loop.is_running():
                         asyncio.run_coroutine_threadsafe(self.tiktok_client.disconnect(), self.current_loop)
                except Exception:
                    pass
            
            self.btn_start.configure(text="2. Start Monitor", bg="#2ecc71", state="normal")
            self.entry_user.configure(state="normal")
            self.entry_keywords.configure(state="normal")
            self.log("🛑 Monitoring Stopped.", "info")
            return

        # START MONITORING
        username = self.entry_user.get()
        keywords_raw = self.entry_keywords.get()
        
        if not username:
            messagebox.showerror("Error", "Please enter TikTok Username")
            return
        
        if not keywords_raw:
            messagebox.showerror("Error", "Please enter at least one keyword")
            return

        self.triggers_list = [k.strip().lower() for k in keywords_raw.split(",") if k.strip()]
        self._save_config()
        
        self.is_monitoring = True
        self.btn_start.configure(text="🛑 Stop Monitor", bg="#e74c3c", state="normal")
        self.entry_user.configure(state="disabled")
        self.entry_keywords.configure(state="disabled")
        
        gmt8 = timezone(timedelta(hours=8))
        session_start = datetime.now(gmt8).strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file_path = f"tiktok_chat_{session_start}.txt"
        self.trigger_file_path = f"tiktok_triggers_{session_start}.txt"
        
        self.log(f"Starting monitor for: @{username}", "info")
        self.log(f"Keywords: {', '.join(self.triggers_list)}", "info")
        
        self.client_thread = threading.Thread(target=self._run_tiktok_client, args=(username,), daemon=True)
        self.client_thread.start()

    def _run_tiktok_client(self, username):
        self.current_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.current_loop)
        
        self.tiktok_client = TikTokLiveClient(unique_id=username)

        @self.tiktok_client.on(ConnectEvent)
        async def on_connect(event: ConnectEvent):
            self.log(f"✅ LIVE: Connected to {event.unique_id}!", "success")

        @self.tiktok_client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            if not self.is_monitoring:
                try: self.tiktok_client.disconnect() 
                except: pass
                return

            message = event.comment.lower()
            user = event.user.nickname
            
            gmt8 = timezone(timedelta(hours=8))
            timestamp = datetime.now(gmt8).strftime("%Y-%m-%d %I:%M:%S %p")
            log_line = f"[{timestamp}] {user}: {event.comment}\n"

            # Write to Chat Log (Single write per event)
            try:
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except: pass

            # Check Triggers
            matched_keyword = None
            for trigger in self.triggers_list:
                if trigger in message:
                    matched_keyword = trigger
                    break

            if matched_keyword:
                self.log(f"📸 TRIGGER: {user} says '{event.comment}'", "trigger")
                
                # Notification
                self.trigger_notification(user, event.comment, matched_keyword)

                # Write to Trigger Log (Only once per trigger)
                try:
                    with open(self.trigger_file_path, "a", encoding="utf-8") as f:
                        f.write(log_line)
                except: pass

                if self.obs_client:
                    try:
                        self.obs_client.save_replay_buffer()
                        self.log("💾 Replay Saved to OBS!", "success")
                    except Exception as e:
                        self.log(f"⚠️ Save Failed: {e}", "error")
                else:
                    self.log("⚠️ Trigger matched, but OBS not connected!", "error")

        try:
            self.tiktok_client.run()
        except Exception as e:
            if self.is_monitoring:
                self.log(f"❌ TikTok Connection Error: {e}", "error")
                self.root.after(0, lambda: self.btn_start.configure(text="2. Start Monitor", bg="#2ecc71", state="normal"))
                self.root.after(0, lambda: self.entry_user.configure(state="normal"))
                self.root.after(0, lambda: self.entry_keywords.configure(state="normal"))
                self.is_monitoring = False

if __name__ == "__main__":
    root = tk.Tk()
    app = TikTokOBSApp(root)
    root.mainloop()