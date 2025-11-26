# Quick Start Guide

Get up and running with TikTok Live Chat Detector in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] OBS Studio installed
- [ ] OBS WebSocket plugin enabled

## Installation Steps

### 1. Clone & Setup (2 minutes)

```bash
# Navigate to project
cd tiktok-live-chat-detector

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure OBS (1 minute)

1. Open OBS Studio
2. Go to **Tools** → **WebSocket Server Settings**
3. Check "Enable WebSocket server"
4. Port: `4455` (default)
5. Set a password (e.g., "mypassword123")
6. Click "Apply" and "OK"
7. Ensure **Replay Buffer** is configured in OBS Settings

### 3. Run Migrations (30 seconds)

```bash
python manage.py migrate
```

### 4. Start the Server (30 seconds)

```bash
python manage.py runserver
```

Open your browser to: `http://localhost:8000`

### 5. Configure the Application (1 minute)

In the web interface:

1. **OBS Connection**
   - Enter your OBS password
   - Source name: "Window Capture" (or your OBS source name)
   - Click "Connect / Test"
   - Wait for "✅ Connected to OBS WebSocket!" message

2. **Add Trigger Words**
   - Type a keyword (e.g., "amazing")
   - Press Enter
   - Add more keywords as needed

3. **Add a Stream**
   - Enter TikTok username (without @)
   - Click "Add Stream +"
   - Click "Start" on the stream card

4. **Save Configuration**
   - Click "Save Configuration" button

## Testing

To verify everything works:

1. Ensure the TikTok user is currently live
2. Watch for "✅ Connected to @username LIVE!" in logs
3. Wait for someone in chat to use your trigger word
4. Check for "🚨 TRIGGER" in logs
5. Verify replay saved to your Videos folder

## Common Issues

### "Connection Failed"
- Verify OBS is running
- Check OBS WebSocket password
- Ensure port 4455 is not blocked

### "Stream Won't Connect"
- User must be currently live
- Check username spelling (no @ symbol)
- Some accounts may be restricted

### "No Replays Saving"
- Verify Replay Buffer is started in OBS
- Check disk space in Videos folder
- Review OBS output settings

## What's Next?

- Review [README.md](../README.md) for detailed documentation
- Check [RECOMMENDATIONS.md](RECOMMENDATIONS.md) for best practices
- Configure multiple streams
- Customize trigger keywords
- View replays in the Replays Archive

## Default Locations

- **Config File**: `tiktok_obs_config.json`
- **Database**: `db.sqlite3`
- **Replays**: 
  - Windows: `C:\Users\<username>\Videos\`
  - macOS: `~/Movies/`
  - Linux: `~/Videos/`

## CLI Commands

```bash
# Run server
python manage.py runserver

# Run on different port
python manage.py runserver 8080

# Run on all interfaces
python manage.py runserver 0.0.0.0:8000

# Create superuser (for admin panel)
python manage.py createsuperuser

# Check for issues
python manage.py check

# Reset database (WARNING: deletes all data)
rm db.sqlite3
python manage.py migrate
```

## Pro Tips

1. **Multiple Streams**: You can monitor multiple TikTok users simultaneously
2. **Keyword Strategy**: Use specific but common phrases for best results
3. **Replay Buffer**: Set OBS replay buffer to 30-60 seconds
4. **File Organization**: Replays are auto-named with username and timestamp
5. **Log Filtering**: Click stream cards to filter logs by specific stream

## Support

- Issues: [Create GitHub Issue]
- Documentation: See [README.md](../README.md)
- Best Practices: See [RECOMMENDATIONS.md](RECOMMENDATIONS.md)

---

**Ready to start monitoring!** 🚀
