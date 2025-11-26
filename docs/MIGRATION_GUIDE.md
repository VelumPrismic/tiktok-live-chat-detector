# Migration Guide - Environment Variables & Security Updates

This guide helps you upgrade to the new version with environment variable configuration and improved security.

## 🚨 Important Changes

### Version 1.1.0 (Current)

This version introduces several important security and stability improvements:

1. **Environment Variables**: Configuration moved from hardcoded values to `.env` file
2. **Cross-Platform Support**: Automatic OS detection for video directories
3. **Structured Logging**: All events logged to files with rotation
4. **Improved Security**: Better path validation and SECRET_KEY protection

---

## 📋 Migration Steps

### Step 1: Install Updated Dependencies

```bash
# Activate your virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install/update python-dotenv
pip install -r requirements.txt
```

### Step 2: Create .env File

Copy the example file and customize it:

```bash
cp .env.example .env
```

Or create `.env` manually with these contents:

```bash
# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Platform Configuration
# Options: windows, linux, darwin (macOS)
PLATFORM_OS=darwin

# OBS Configuration
OBS_PASSWORD=
OBS_HOST=localhost
OBS_PORT=4455

# Application Settings
VIDEO_DIRECTORY=
LOG_LEVEL=INFO

# Database
DATABASE_PATH=db.sqlite3

# TikTok Configuration
CONFIG_FILE=tiktok_obs_config.json
```

### Step 3: Generate a Secure SECRET_KEY

**Option A: Using Python**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Option B: Using OpenSSL**
```bash
openssl rand -base64 50
```

Copy the generated key and paste it into your `.env` file:
```bash
DJANGO_SECRET_KEY=your-generated-key-here
```

### Step 4: Configure Platform

Set your platform in `.env`:

**For macOS:**
```bash
PLATFORM_OS=darwin
```

**For Linux:**
```bash
PLATFORM_OS=linux
```

**For Windows:**
```bash
PLATFORM_OS=windows
```

> **Note:** If you don't set this, the system will auto-detect your platform.

### Step 5: Set Video Directory (Optional)

If you want to use a custom directory for replays:

```bash
VIDEO_DIRECTORY=/path/to/your/videos
```

**Default directories:**
- **Windows**: `C:\Users\YourName\Videos`
- **macOS**: `/Users/YourName/Movies`
- **Linux**: `/home/yourname/Videos` (or `$XDG_VIDEOS_DIR`)

### Step 6: Restart the Application

```bash
python manage.py runserver
```

---

## 🔍 Verification

### Check Configuration Loaded

Look for this log message when starting:
```
INFO Configuration loaded from tiktok_obs_config.json
```

### Check Logs Directory

A new `logs/` directory should be created with:
- `app.log` - General application logs
- `error.log` - Error-specific logs

### Test Video Directory

1. Go to the replays page
2. Verify it shows videos from the correct directory

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'dotenv'"

**Solution:**
```bash
pip install python-dotenv
```

### Issue: "SECRET_KEY is not defined"

**Solution:**
1. Ensure `.env` file exists in project root
2. Check that `DJANGO_SECRET_KEY` is set in `.env`
3. Restart the server

### Issue: Videos Not Showing

**Solution:**
1. Check your `PLATFORM_OS` setting in `.env`
2. Manually set `VIDEO_DIRECTORY` if needed
3. Check logs in `logs/app.log` for errors

### Issue: Log Files Not Created

**Solution:**
1. Ensure the application has write permissions
2. The `logs/` directory will be created automatically
3. Check `logs/app.log` and `logs/error.log`

---

## 📝 Configuration Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key for sessions | `your-secret-key-here` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `PLATFORM_OS` | Force platform | Auto-detected |
| `VIDEO_DIRECTORY` | Custom video dir | Platform default |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DATABASE_PATH` | Database file | `db.sqlite3` |
| `CONFIG_FILE` | Config file name | `tiktok_obs_config.json` |

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages only

---

## 🔒 Security Best Practices

### 1. Never Commit .env File

The `.env` file is already in `.gitignore`. Verify it's not tracked:

```bash
git status
```

If `.env` appears, remove it:
```bash
git rm --cached .env
```

### 2. Use Different Keys for Different Environments

- **Development**: Use `.env` with `DEBUG=True`
- **Production**: Use environment variables or secrets manager

### 3. Rotate Secret Keys Periodically

Generate a new secret key every few months and update `.env`.

---

## 🆕 New Features

### 1. Cross-Platform Path Support

The application now automatically detects your OS and uses the appropriate video directory:

```python
# Old (Windows only)
video_dir = os.path.expanduser("~\\Videos")

# New (Cross-platform)
from monitor.utils import get_video_directory
video_dir = get_video_directory()  # Works on Windows, macOS, Linux
```

### 2. Structured Logging

All logs are now saved to files with automatic rotation:

- **Location**: `logs/` directory
- **Rotation**: 10MB per file, 5 backups
- **Formats**: 
  - Console: Simple format
  - File: Detailed format with timestamps

Example log entry:
```
INFO 2024-11-26 15:30:45 service 12345 67890 Configuration loaded from tiktok_obs_config.json
```

### 3. Improved Error Handling

Better error messages and logging throughout the application.

---

## 📚 Additional Resources

- [README.md](../README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [RECOMMENDATIONS.md](RECOMMENDATIONS.md) - Best practices

---

## ❓ FAQ

### Q: Do I need to migrate my existing configuration?

**A:** Your existing `tiktok_obs_config.json` file will continue to work. The new `.env` file is for system-level configuration.

### Q: Can I still use the application without creating a .env file?

**A:** Yes, but you'll use the default (insecure) SECRET_KEY. This is fine for development but NOT recommended for production.

### Q: What happens to my old SECRET_KEY?

**A:** It's still in `settings.py` as a fallback, but you should move to environment variables for security.

### Q: Will this break my existing setup?

**A:** No. The changes are backward compatible. Without a `.env` file, the application uses sensible defaults.

### Q: How do I deploy this to production?

**A:** 
1. Set `DEBUG=False` in `.env`
2. Use a secure SECRET_KEY
3. Set `ALLOWED_HOSTS` to your domain
4. Use a production WSGI server (Gunicorn, uWSGI)
5. Consider using environment variables instead of `.env`

---

## 🔄 Rollback

If you encounter issues and need to rollback:

1. Delete the `.env` file
2. Reinstall old version: `git checkout <old-version-tag>`
3. The application will use hardcoded values

**Note:** This is not recommended for security reasons.

---

**Version:** 1.1.0  
**Last Updated:** November 26, 2024  
**Compatibility:** Python 3.8+, Django 5.2+
