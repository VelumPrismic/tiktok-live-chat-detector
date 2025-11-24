import threading
import asyncio
import json
import os
import time
from datetime import datetime, timezone, timedelta
from collections import deque
import obsws_python as obs
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent

CONFIG_FILE = "tiktok_obs_config.json"

class MonitorService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.obs_client = None
        self.tiktok_client = None
        self.is_monitoring = False
        self.log_file_path = ""
        self.trigger_file_path = ""
        self.triggers_list = []
        self.current_loop = None
        self.client_thread = None
        
        self.notification_queue = deque()
        self.logs = deque(maxlen=100)
        
        self.username = ""
        self.obs_password = ""
        self.source_name = "Window Capture"
        self.keywords = "mine, code, lock, ssd"
        self.notifications_enabled = True
        self.notification_duration = 5
        
        self._load_config()

    def log(self, message, tag="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}"
        self.logs.append({"message": full_msg, "tag": tag, "timestamp": timestamp})
        # print(full_msg) # Optional: print to console

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.username = data.get("username", "")
                    self.obs_password = data.get("obs_password", "")
                    self.source_name = data.get("source_name", "Window Capture")
                    self.keywords = data.get("keywords", "mine, code, lock, ssd")
                    self.notifications_enabled = data.get("notifications_enabled", True)
                    self.notification_duration = data.get("notification_duration", 5)
            except Exception as e:
                self.log(f"Failed to load config: {e}", "error")

    def save_config(self, username, obs_password, source_name, keywords, notifications_enabled=True, notification_duration=5):
        self.username = username
        self.obs_password = obs_password
        self.source_name = source_name
        self.keywords = keywords
        self.notifications_enabled = notifications_enabled
        self.notification_duration = notification_duration
        
        data = {
            "username": username,
            "obs_password": obs_password,
            "source_name": source_name,
            "keywords": keywords,
            "notifications_enabled": notifications_enabled,
            "notification_duration": notification_duration
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            self.log(f"Failed to save config: {e}", "error")

    def connect_obs(self):
        if not self.obs_password:
            return False, "Please enter OBS Password"

        def _run_obs_setup():
            self.log("Connecting to OBS...", "info")
            try:
                self.obs_client = obs.ReqClient(host="localhost", port=4455, password=self.obs_password)
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
        return True, "Connecting to OBS..."

    def toggle_monitoring(self):
        if self.is_monitoring:
            self.log("Stopping monitoring...", "info")
            self.is_monitoring = False
            
            if self.tiktok_client:
                try:
                    if self.current_loop and self.current_loop.is_running():
                        # Try to disconnect gracefully
                        asyncio.run_coroutine_threadsafe(self.tiktok_client.disconnect(), self.current_loop)
                    
                    # Force loop stop schedule
                    if self.current_loop:
                        self.current_loop.call_soon_threadsafe(self.current_loop.stop)
                except Exception as e:
                    self.log(f"Warning during stop: {e}", "info")
            
            self.log("🛑 Monitoring Stopped.", "info")
            return False

        # START
        if not self.username:
            return False, "Please enter TikTok Username"
        
        if not self.keywords:
            return False, "Please enter at least one keyword"

        self.triggers_list = [k.strip().lower() for k in self.keywords.split(",") if k.strip()]
        
        # Prevent duplicates or handle restart
        for t in threading.enumerate():
            if t.name == "TikTokMonitor":
                if self.is_monitoring:
                    self.log("⚠️ Monitor is already running.", "info")
                    return True
                else:
                    self.log("⚠️ Waiting for previous session to close...", "info")
                    t.join(timeout=2.0)
                    if t.is_alive():
                        self.log("⚠️ Previous session stuck. Forcing new session...", "error")
                        # Rename the zombie thread so we can start a new one
                        t.name = f"TikTokMonitor_Zombie_{int(time.time())}"

        self.is_monitoring = True
        
        gmt8 = timezone(timedelta(hours=8))
        session_start = datetime.now(gmt8).strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file_path = f"tiktok_chat_{session_start}.txt"
        self.trigger_file_path = f"tiktok_triggers_{session_start}.txt"
        
        self.log(f"Starting monitor for: @{self.username}", "info")
        self.log(f"Keywords: {', '.join(self.triggers_list)}", "info")
        
        self.client_thread = threading.Thread(target=self._run_tiktok_client, args=(self.username,), name="TikTokMonitor", daemon=True)
        self.client_thread.start()
        return True

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

            try:
                with open(self.log_file_path, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except: pass

            matched_keyword = None
            for trigger in self.triggers_list:
                if trigger in message:
                    matched_keyword = trigger
                    break

            if matched_keyword:
                self.log(f"📸 TRIGGER: {user} says '{event.comment}'", "trigger")
                
                # Notification
                if self.notifications_enabled:
                    self.notification_queue.append({
                        "user": user,
                        "message": event.comment,
                        "keyword": matched_keyword,
                        "time": datetime.now(gmt8).strftime("%H:%M:%S")
                    })

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
                self.is_monitoring = False
