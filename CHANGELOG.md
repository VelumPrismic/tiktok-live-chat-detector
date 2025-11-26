# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-11-26

### 🔒 Security

- **Environment Variables**: Moved SECRET_KEY to environment variables instead of hardcoding
- **CSRF Protection**: Improved CSRF token handling (still uses @csrf_exempt but documented)
- **Path Traversal Protection**: Enhanced file serving security with better path validation
- **Secure Defaults**: Added fallback SECRET_KEY for development only

### 🌍 Cross-Platform Support

- **Automatic OS Detection**: App now detects Windows, Linux, and macOS automatically
- **Platform Override**: Can force specific OS via `PLATFORM_OS` environment variable
- **Smart Video Directories**: 
  - Windows: `~/Videos`
  - macOS: `~/Movies`
  - Linux: `~/Videos` or `$XDG_VIDEOS_DIR`
- **Custom Paths**: Support for custom video directory via `VIDEO_DIRECTORY` env var

### 📝 Logging Improvements

- **Structured Logging**: All logs now saved to `logs/` directory
- **Log Rotation**: Automatic rotation at 10MB with 5 backups
- **Separate Error Logs**: Dedicated `error.log` for error-level messages
- **Configurable Levels**: Set log level via `LOG_LEVEL` environment variable
- **Better Error Context**: Full stack traces in error logs with `exc_info=True`

### 🛠️ New Utilities

- **utils.py Module**: Created centralized utility functions
  - `get_platform()` - Detect current OS
  - `get_video_directory()` - Get platform-appropriate video directory
  - `sanitize_filename()` - Cross-platform filename sanitization
  - `ensure_directory_exists()` - Safe directory creation
  - `get_logs_directory()` - Logging directory management
  - `get_config_file_path()` - Configuration file path resolution

### 📦 Configuration

- **.env Support**: Added python-dotenv for environment variable management
- **.env.example**: Template file with all configuration options
- **Backward Compatible**: Existing configurations continue to work
- **Configurable Options**:
  - `DJANGO_SECRET_KEY` - Django secret key
  - `DEBUG` - Debug mode toggle
  - `ALLOWED_HOSTS` - Comma-separated allowed hosts
  - `PLATFORM_OS` - Force specific OS (windows/linux/darwin)
  - `VIDEO_DIRECTORY` - Custom video directory
  - `LOG_LEVEL` - Logging verbosity (DEBUG/INFO/WARNING/ERROR)
  - `DATABASE_PATH` - Custom database location
  - `CONFIG_FILE` - Custom config file name

### 📚 Documentation

- **MIGRATION_GUIDE.md**: Complete guide for upgrading to v1.1.0
- **INSTALLATION_OPTIONS.md**: Comprehensive deployment strategies guide
- **Enhanced README.md**: Added links to all documentation
- **Code Documentation**: Added docstrings to utility functions

### 🔧 Bug Fixes

- **File Handles**: Fixed unclosed file handles in video serving
- **Path Handling**: Improved cross-platform path resolution
- **Error Messages**: More descriptive error messages throughout

### ⚠️ Breaking Changes

None - this release is fully backward compatible.

### 📖 Upgrade Instructions

See [Migration Guide](docs/MIGRATION_GUIDE.md) for detailed upgrade instructions.

**Quick Upgrade:**
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Generate secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Add key to .env file
# DJANGO_SECRET_KEY=<generated-key>

# Restart application
python manage.py runserver
```

---

## [1.0.0] - 2024-11-26

### Initial Release

- Multi-stream TikTok monitoring
- Keyword detection in live chat
- OBS replay buffer integration
- Automatic file naming with metadata
- Web-based dashboard
- Real-time logs and notifications
- Configuration persistence

---

## Versioning

- **Major version** (X.0.0): Breaking changes
- **Minor version** (1.X.0): New features, backward compatible
- **Patch version** (1.0.X): Bug fixes, backward compatible

---

## Planned Features

### [1.2.0] - Planned

- [ ] WebSocket support for real-time updates (replace polling)
- [ ] Database models for persistent history
- [ ] Stream statistics dashboard
- [ ] Reconnection logic for dropped streams
- [ ] Input validation on frontend

### [1.3.0] - Planned

- [ ] Docker support with docker-compose
- [ ] Multi-user support
- [ ] API authentication
- [ ] Rate limiting
- [ ] Health check endpoint

### [2.0.0] - Planned

- [ ] Complete API redesign
- [ ] Django REST Framework integration
- [ ] Celery for background tasks
- [ ] Redis for caching
- [ ] PostgreSQL support

---

## Contributing

See [RECOMMENDATIONS.md](docs/RECOMMENDATIONS.md) for development guidelines and best practices.

---

**Maintainers**: Development Team  
**License**: [Add License]  
**Repository**: [Add Repository URL]
