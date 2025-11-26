# TikTok Live Chat Detector & OBS Replay Automation

A Django-based real-time monitoring system that connects to multiple TikTok live streams, detects keyword triggers in chat messages, and automatically saves OBS replay buffer clips with intelligent naming conventions.

## 🎯 Features

- **Multi-Stream Monitoring**: Monitor multiple TikTok live streams simultaneously
- **Keyword Detection**: Configure custom trigger words to detect in live chat
- **OBS Integration**: Automatic replay buffer saving when keywords are detected
- **Smart File Naming**: Replays automatically renamed with `{username}_{trigger}_{timestamp}` format
- **Real-Time Dashboard**: Modern web interface with live logs and notifications
- **Stream Management**: Add/remove streams dynamically without restarting
- **Replay Archive**: Built-in video player to review saved clips
- **Multi-Stream Logs**: Filter logs by specific stream or view all activity

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 5.2.8 (Python web framework)
- **Real-Time Communication**: WebSocket-based live updates
- **TikTok Integration**: TikTokLive Python library
- **OBS Control**: obsws-python (OBS WebSocket client)
- **Frontend**: Tailwind CSS + Vanilla JavaScript
- **Database**: SQLite3 (minimal usage, mostly in-memory state)

### Project Structure
```
tiktok-live-chat-detector/
├── tiktok_obs/              # Django project configuration
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL routing
│   ├── wsgi.py              # WSGI application entry
│   └── asgi.py              # ASGI application entry
├── monitor/                 # Main application
│   ├── service.py           # Core monitoring service (singleton)
│   ├── views.py             # Django views & API endpoints
│   ├── urls.py              # Monitor app URL routing
│   ├── templates/           # HTML templates
│   │   └── monitor/
│   │       ├── index.html   # Main dashboard
│   │       └── replays.html # Replay archive viewer
│   └── models.py            # Database models (currently unused)
├── tiktok_live_patch.py     # Monkey patch for TikTokLive library
├── tiktok_obs_config.json   # Configuration persistence
├── main.py                  # Alternative entry point
├── manage.py                # Django management script
└── db.sqlite3               # SQLite database
```

## 📋 Prerequisites

- Python 3.8+
- OBS Studio with WebSocket server enabled
- Active TikTok account(s) to monitor
- Windows/macOS/Linux environment

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tiktok-live-chat-detector
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install Django>=5.2.8
   pip install TikTokLive
   pip install obsws-python
   ```

4. **Configure OBS WebSocket**
   - Open OBS Studio
   - Go to **Tools** → **WebSocket Server Settings**
   - Enable WebSocket server (port 4455)
   - Set a password and remember it

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

## 🎮 Usage

### Starting the Application

```bash
python manage.py runserver
```

Access the dashboard at: `http://localhost:8000`

### Configuration

1. **OBS Connection**
   - Enter your OBS WebSocket password
   - Set the source name (e.g., "Window Capture")
   - Click "Connect / Test"

2. **Trigger Words**
   - Add keywords that will trigger replay saves
   - Type keyword and press Enter
   - Remove keywords by clicking the × button

3. **Stream Management**
   - Enter TikTok username (without @)
   - Click "Add Stream +"
   - Start/stop individual streams using the dashboard cards

4. **Save Configuration**
   - Click "Save Configuration" to persist settings
   - Configuration stored in `tiktok_obs_config.json`

### Replay Files

Replays are automatically saved to your system's Videos folder with the format:
```
{chatter_username}_{trigger_word}_{YYYY-MM-DD_HH-MM-SS_AM/PM}.mp4
```

Example: `john_doe_amazing_2024-11-26_02-15-30_PM.mp4`

## 🔧 Configuration File

`tiktok_obs_config.json` structure:
```json
{
  "username": ["tiktok_user1", "tiktok_user2"],
  "obs_password": "your_obs_password",
  "source_name": "Window Capture",
  "keywords": "amazing,wow,highlight",
  "notifications_enabled": true,
  "notification_duration": 5
}
```

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/api/save_config` | POST | Save configuration |
| `/api/connect_obs` | POST | Connect to OBS WebSocket |
| `/api/stream_action` | POST | Start/stop stream monitoring |
| `/api/status` | GET | Get logs and stream statuses |
| `/api/clear_logs` | POST | Clear log history |
| `/replays/` | GET | View replay archive |
| `/video/<filename>` | GET | Stream video file |

## 🛠️ Core Components

### MonitorService (Singleton)
The heart of the application, managing:
- OBS WebSocket connection
- TikTok client instances per stream
- Asynchronous event loop for live connections
- Log queue (max 100 entries)
- Notification queue for UI alerts

### Event Handlers
- `_on_connect`: Handles successful TikTok stream connections
- `_on_comment`: Processes incoming chat messages and detects triggers
- `on_replay_saved`: Renames OBS replay files with metadata

### TikTokLive Patch
Applies a monkey patch to fix betterproto serialization issues with user data fields (camelCase → snake_case conversion).

## 🐛 Known Issues

1. **TikTokLive Compatibility**: Requires monkey patch for user data serialization
2. **File System Limitations**: Replay renaming has retry logic due to OBS file locking
3. **Windows Path Handling**: Uses `~\\Videos` path (Windows-specific)
4. **CSRF Protection**: Some endpoints use `@csrf_exempt` for simplicity

## 📚 Additional Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Upgrade guide for environment variables (v1.1.0)
- **[Recommendations](docs/RECOMMENDATIONS.md)** - Best practices and improvement suggestions
- **[Analysis Summary](docs/ANALYSIS_SUMMARY.md)** - Technical assessment and code quality metrics
- **[Installation Options](docs/INSTALLATION_OPTIONS.md)** - Portable bundles and distribution strategies

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📧 Support

[Add support information here]

## 🔍 Troubleshooting

### OBS Connection Fails
- Verify WebSocket server is enabled in OBS
- Check password matches configuration
- Ensure OBS is running before connecting

### TikTok Stream Won't Connect
- Verify username is correct (without @ symbol)
- Check if the user is currently live
- Review logs for specific error messages

### Replays Not Saving
- Verify OBS Replay Buffer is started
- Check OBS WebSocket connection status
- Ensure sufficient disk space in Videos folder

### Keywords Not Triggering
- Keywords are case-insensitive
- Partial matching is used (keyword within message)
- Check logs to verify comments are being received
