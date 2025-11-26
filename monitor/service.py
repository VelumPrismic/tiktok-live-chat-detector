import threading
import asyncio
import json
import os
import time
import logging
from datetime import datetime, timezone, timedelta
from collections import deque
import obsws_python as obs
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent
from tiktok_live_patch import apply_patch
from .utils import get_config_file_path, sanitize_filename

logger = logging.getLogger('monitor')

# Apply Patch
apply_patch()

CONFIG_FILE = str(get_config_file_path())

class MonitorService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.obs_client = None
        self.obs_events = None
        
        # Active clients: username -> client
        self.tiktok_clients = {}
        
        # Loop management
        self.loop_thread = None
        self.event_loop = None
        
        self.logs = deque(maxlen=100)
        self.notification_queue = deque()
        
        self.usernames = []
        self.obs_password = ""
        self.source_name = "Window Capture"
        self.keywords = ""
        self.notifications_enabled = True
        self.notification_duration = 5
        
        self.last_trigger = None
        
        self._load_config()
        # Start the loop thread immediately
        self._start_loop_thread()

    def _start_loop_thread(self):
        if self.loop_thread and self.loop_thread.is_alive():
            return

        def loop_entry():
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_forever()

        self.loop_thread = threading.Thread(target=loop_entry, name="TikTokLoop", daemon=True)
        self.loop_thread.start()
        
        # Wait for loop to be ready
        while self.event_loop is None:
            time.sleep(0.01)

    @property
    def is_monitoring(self):
        """Global status for backward compatibility"""
        return any(self.is_stream_active(u) for u in self.usernames)

    def log(self, message, tag="info", source_stream=None):
        """Log a message to both in-memory queue and logging system"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {message}" if not source_stream else f"[{timestamp}] [{source_stream}] {message}"
        
        # Add to in-memory queue for UI
        self.logs.append({
            "message": message, 
            "tag": tag, 
            "timestamp": timestamp, 
            "source_stream": source_stream
        })
        
        # Log to file system based on tag
        if tag == "error":
            logger.error(full_msg)
        elif tag == "success":
            logger.info(full_msg)
        elif tag == "trigger":
            logger.warning(full_msg)  # Use warning level for triggers so they stand out
        else:
            logger.info(full_msg)

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    users = data.get("username", "")
                    if isinstance(users, str):
                        self.usernames = [u.strip() for u in users.split(",") if u.strip()]
                    else:
                        self.usernames = users if isinstance(users, list) else []
                        
                    self.obs_password = data.get("obs_password", "")
                    self.source_name = data.get("source_name", "Window Capture")
                    self.keywords = data.get("keywords", "")
                    self.notifications_enabled = data.get("notifications_enabled", True)
                    self.notification_duration = data.get("notification_duration", 5)
                    
                    logger.info(f"Configuration loaded from {CONFIG_FILE}")
            except Exception as e:
                self.log(f"Failed to load config: {e}", "error")
                logger.error(f"Failed to load config: {e}", exc_info=True)

    def save_config(self, usernames, obs_password, source_name, keywords, notifications_enabled=True, notification_duration=5):
        if isinstance(usernames, str):
            self.usernames = [u.strip() for u in usernames.split(",") if u.strip()]
        else:
            self.usernames = usernames if isinstance(usernames, list) else []
            
        self.obs_password = obs_password
        self.source_name = source_name
        self.keywords = keywords
        self.notifications_enabled = notifications_enabled
        self.notification_duration = notification_duration
        
        data = {
            "username": self.usernames,
            "obs_password": obs_password,
            "source_name": source_name,
            "keywords": keywords,
            "notifications_enabled": notifications_enabled,
            "notification_duration": notification_duration
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f)
            logger.info(f"Configuration saved to {CONFIG_FILE}")
        except Exception as e:
            self.log(f"Failed to save config: {e}", "error")
            logger.error(f"Failed to save config: {e}", exc_info=True)

    def connect_obs(self):
        if not self.obs_password:
            return False, "Please enter OBS Password"

        def _run_obs_setup():
            self.log("Connecting to OBS...", "info")
            
            # Cleanup existing connection if any
            if self.obs_events:
                try:
                    self.obs_events.disconnect()
                except:
                    pass
            
            try:
                self.obs_client = obs.ReqClient(host="localhost", port=4455, password=self.obs_password)
                
                # Setup Events
                self.obs_events = obs.EventClient(host="localhost", port=4455, password=self.obs_password)
                self.obs_events.callback.register(self.on_replay_saved)
                
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
                self.log(f"❌ OBS Connection Failed: {e} or maybe you forgot to save the configuration?", "error")
                self.obs_client = None
                self.obs_events = None
        
        threading.Thread(target=_run_obs_setup, daemon=True).start()
        return True, "Connecting to OBS..."

    def on_replay_saved(self, event):
        """Handle ReplayBufferSaved event to rename the file"""
        self.log(f"DEBUG: Replay Saved Event Received!", "info")
        try:
            # Extract path from event (handle snake_case or camelCase)
            saved_path = getattr(event, "saved_replay_path", None)
            if not saved_path:
                saved_path = getattr(event, "savedReplayPath", None)
            
            if not saved_path:
                self.log("⚠️ Replay saved, but path missing in event data.", "error")
                # Try to dump event vars to see what we got
                try:
                    self.log(f"DEBUG Event vars: {vars(event)}", "info")
                except: pass
                return

            if not self.last_trigger:
                self.log(f"ℹ️ Replay saved to {saved_path} (No trigger info)", "info")
                return

            # Get Trigger Info
            user = self.last_trigger.get("user", "unknown")
            trigger = self.last_trigger.get("trigger", "unknown")
            
            # Sanitize filenames using utility function
            user = sanitize_filename(user)
            trigger = sanitize_filename(trigger)

            # Date Format: GMT+8, Non-military (12h)
            gmt8 = timezone(timedelta(hours=8))
            date_str = datetime.now(gmt8).strftime("%Y-%m-%d_%I-%M-%S_%p")
            
            # Construct new filename: username_triggerword_date
            new_filename = f"{user}_{trigger}_{date_str}"
            
            # Get directory and extension
            directory = os.path.dirname(saved_path)
            extension = os.path.splitext(saved_path)[1]
            
            new_path = os.path.join(directory, f"{new_filename}{extension}")
            
            self.log(f"DEBUG: Attempting rename {saved_path} -> {new_path}", "info")
            
            # Rename
            # Retry logic in case OBS is still holding the file
            max_retries = 5
            for i in range(max_retries):
                try:
                    os.rename(saved_path, new_path)
                    self.log(f"✅ Replay renamed to: {new_filename}{extension}", "success")
                    break
                except OSError as e:
                    if i == max_retries - 1:
                        self.log(f"❌ Failed to rename replay: {e}", "error")
                    else:
                        time.sleep(0.5)

        except Exception as e:
            self.log(f"❌ Error processing replay save: {e}", "error")


    def start_stream(self, username):
        from functools import partial
        
        # Ensure loop is running
        self._start_loop_thread()
        
        if username in self.tiktok_clients:
            client = self.tiktok_clients[username]
            # Check if connected or connecting
            if client.connected:
                 self.log(f"Already monitoring @{username}", "info")
                 return True
            else:
                 # If it exists but not connected, might be stale or disconnected
                 self.stop_stream(username)

        self.log(f"Starting monitor for @{username}...", "info")
        client = TikTokLiveClient(unique_id=username)
        
        # Bind events
        client.add_listener(ConnectEvent, partial(self._on_connect, source_stream=username))
        client.add_listener(CommentEvent, partial(self._on_comment, source_stream=username))
        # Add disconnect handler to cleanup?
        
        self.tiktok_clients[username] = client
        
        # Run start in the loop
        async def _start_client():
            try:
                await client.start()
            except Exception as e:
                self.log(f"❌ Connection failed for @{username}: {e}", "error", username)
                # Cleanup on failure
                if username in self.tiktok_clients:
                     del self.tiktok_clients[username]

        asyncio.run_coroutine_threadsafe(_start_client(), self.event_loop)
        return True

    def stop_stream(self, username):
        if username in self.tiktok_clients:
            self.log(f"Stopping monitor for @{username}...", "info")
            client = self.tiktok_clients.pop(username)
            if self.event_loop:
                asyncio.run_coroutine_threadsafe(client.disconnect(), self.event_loop)
        return True
    
    def is_stream_active(self, username):
        return username in self.tiktok_clients and self.tiktok_clients[username].connected

    # --- Event Handlers ---
    async def _on_connect(self, event, source_stream):
        self.log(f"✅ Connected to @{source_stream} LIVE!", "success", source_stream)

    async def _on_comment(self, event, source_stream):
        msg = event.comment
        # Log comment for debugging
        logger.debug(f"Comment from {getattr(event.user, 'unique_id', 'unknown')}: {msg}")
        
        # Triggers
        trigger_list = [k.strip().lower() for k in self.keywords.split(",") if k.strip()]
        if any(t in msg.lower() for t in trigger_list):
            found_trigger = next((t for t in trigger_list if t in msg.lower()), "unknown")
            
            # Use unique_id or nick_name, falling back safely
            user_display = getattr(event.user, "unique_id", getattr(event.user, "nick_name", "unknown"))
            
            self.log(f"🚨 TRIGGER: '{found_trigger}' by {user_display}: {msg}", "trigger", source_stream)
            
            self.notification_queue.append({
                "user": source_stream,
                "message": msg,
                "keyword": found_trigger
            })
            
            if self.obs_client:
                try:
                    # Use chatter's username instead of source_stream
                    chatter_name = getattr(event.user, "unique_id", "unknown_user")
                    self.last_trigger = {"user": chatter_name, "trigger": found_trigger}
                    
                    self.obs_client.save_replay_buffer()
                    self.log("💾 OBS Replay Triggered!", "success", source_stream)
                except Exception as e:
                    self.log(f"❌ OBS Trigger Failed: {e}", "error", source_stream)
        else:
            pass


