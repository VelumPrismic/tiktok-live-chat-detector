# Recommendations & Best Practices

This document outlines recommended improvements for the TikTok Live Chat Detector project based on industry best practices.

## 🔴 Critical Issues

### 1. Security Vulnerabilities

#### SECRET_KEY Exposure
**Issue**: Django secret key is hardcoded in `settings.py`
```python
SECRET_KEY = 'django-insecure-fnnz%6#qsb!&(j$)4edr=i0wlhpvww6e^6is+l#&0benvn&fqv'
```

**Solution**: Use environment variables
```python
# settings.py
import os
from pathlib import Path

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-key-for-local-only')
```

Create a `.env` file (add to `.gitignore`):
```bash
DJANGO_SECRET_KEY=your-secure-random-key-here
OBS_PASSWORD=your-obs-password
```

#### CSRF Exemptions
**Issue**: Multiple endpoints use `@csrf_exempt` decorator
**Solution**: 
- Implement proper CSRF token handling in frontend
- Use Django REST Framework for API endpoints with proper authentication
- If keeping simple approach, at least add rate limiting

#### Path Traversal Vulnerability
**Issue**: Video serving has basic protection but could be improved
**Location**: `views.py:43-53`

**Recommendation**: 
```python
from django.core.exceptions import SuspiciousFileOperation
import os

def serve_video(request, filename):
    video_dir = os.path.expanduser("~/Videos")
    
    # Sanitize filename - remove any path components
    filename = os.path.basename(filename)
    path = os.path.join(video_dir, filename)
    
    # Security check
    try:
        real_path = os.path.realpath(path)
        real_dir = os.path.realpath(video_dir)
        if not real_path.startswith(real_dir):
            raise SuspiciousFileOperation("Invalid file path")
    except:
        raise Http404("Invalid file path")
    
    if os.path.exists(path):
        return FileResponse(open(path, 'rb'))
    raise Http404("Video not found")
```

### 2. Configuration Management

#### Passwords Stored in Plain Text
**Issue**: OBS password stored in plain JSON file
**Solution**: 
- Use system keyring (e.g., `keyring` library)
- Encrypt sensitive configuration
- Store in environment variables

```python
import keyring

# Store
keyring.set_password("tiktok-obs", "obs_websocket", obs_password)

# Retrieve
obs_password = keyring.get_password("tiktok-obs", "obs_websocket")
```

### 3. File Resource Management

#### Unclosed File Handle
**Issue**: `views.py:52` - File opened but not properly closed
```python
return FileResponse(open(path, 'rb'))
```

**Solution**:
```python
response = FileResponse(open(path, 'rb'), as_attachment=False)
response['Content-Type'] = 'video/mp4'
return response
```

Or better yet:
```python
from django.http import StreamingHttpResponse
import mimetypes

def serve_video(request, filename):
    video_dir = os.path.expanduser("~/Videos")
    filename = os.path.basename(filename)
    path = os.path.join(video_dir, filename)
    
    if not os.path.exists(path):
        raise Http404("Video not found")
    
    mime_type, _ = mimetypes.guess_type(path)
    
    with open(path, 'rb') as video_file:
        response = StreamingHttpResponse(
            video_file,
            content_type=mime_type or 'application/octet-stream'
        )
        response['Content-Length'] = os.path.getsize(path)
        return response
```

## 🟡 High Priority Improvements

### 4. Dependency Management

#### Missing Requirements File
**Issue**: No `requirements.txt` or `pyproject.toml`

**Create `requirements.txt`**:
```txt
Django>=5.2.8,<6.0
TikTokLive>=5.0.0
obsws-python>=1.5.0
python-dotenv>=1.0.0
```

**Or use `pyproject.toml` (recommended)**:
```toml
[project]
name = "tiktok-live-chat-detector"
version = "1.0.0"
description = "TikTok Live Chat Detector with OBS Integration"
requires-python = ">=3.8"
dependencies = [
    "Django>=5.2.8,<6.0",
    "TikTokLive>=5.0.0",
    "obsws-python>=1.5.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-django>=4.5.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]
```

### 5. Error Handling & Logging

#### Inadequate Error Handling
**Issue**: Many try-except blocks swallow exceptions without proper logging

**Solution**: Implement structured logging
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/tiktok_monitor.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'monitor': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

**In service.py**:
```python
import logging

logger = logging.getLogger('monitor')

# Instead of print()
logger.info(f"Connected to @{source_stream} LIVE!")
logger.error(f"Connection failed: {e}", exc_info=True)
```

### 6. Database Utilization

#### Unused Database Models
**Issue**: No models defined but SQLite database exists

**Recommendation**: Leverage database for:
- Persistent logs with search/filter capabilities
- Stream history and statistics
- Trigger event history
- Replay metadata

**Example Models**:
```python
# monitor/models.py
from django.db import models
from django.utils import timezone

class Stream(models.Model):
    username = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_connected = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['username', 'is_active']),
        ]

class TriggerEvent(models.Model):
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE)
    chatter_username = models.CharField(max_length=100)
    trigger_word = models.CharField(max_length=100)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    replay_filename = models.CharField(max_length=500, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['trigger_word', '-timestamp']),
        ]
        ordering = ['-timestamp']

class LogEntry(models.Model):
    LOG_LEVELS = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('trigger', 'Trigger'),
    ]
    
    message = models.TextField()
    level = models.CharField(max_length=20, choices=LOG_LEVELS)
    source_stream = models.CharField(max_length=100, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['source_stream', '-timestamp']),
        ]
        ordering = ['-timestamp']
```

### 7. Code Organization & Architecture

#### Singleton Service Pattern
**Issue**: MonitorService uses class-level singleton which can cause issues in testing

**Recommendation**: Use Django's app registry or dependency injection
```python
# monitor/apps.py
from django.apps import AppConfig

class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitor'
    
    def ready(self):
        from .service import MonitorService
        from tiktok_live_patch import apply_patch
        
        apply_patch()
        
        # Initialize service as app singleton
        if not hasattr(self, 'monitor_service'):
            self.monitor_service = MonitorService()
```

#### Thread Safety Concerns
**Issue**: Shared mutable state (logs, notification_queue) accessed from multiple threads

**Solution**: Use thread-safe collections
```python
from queue import Queue
import threading

class MonitorService:
    def __init__(self):
        self.logs = Queue(maxsize=100)  # Thread-safe
        self.notification_queue = Queue()
        self._logs_lock = threading.Lock()
        # ... rest of initialization
```

### 8. Cross-Platform Compatibility

#### Hardcoded Windows Path
**Issue**: `views.py:23` uses Windows-specific path `~\\Videos`

**Solution**:
```python
import platform
from pathlib import Path

def get_video_directory():
    system = platform.system()
    
    if system == "Windows":
        return Path.home() / "Videos"
    elif system == "Darwin":  # macOS
        return Path.home() / "Movies"
    else:  # Linux
        # Check XDG_VIDEOS_DIR or use ~/Videos
        xdg_videos = os.environ.get('XDG_VIDEOS_DIR')
        if xdg_videos:
            return Path(xdg_videos)
        return Path.home() / "Videos"

# In views.py
video_dir = get_video_directory()
```

### 9. API Design

#### Inconsistent Response Format
**Issue**: API responses lack standardization

**Recommendation**: Standardize API responses
```python
# utils/responses.py
from django.http import JsonResponse

def success_response(message="Success", data=None):
    response = {
        "status": "success",
        "message": message
    }
    if data:
        response["data"] = data
    return JsonResponse(response)

def error_response(message="Error", code=400, errors=None):
    response = {
        "status": "error",
        "message": message
    }
    if errors:
        response["errors"] = errors
    return JsonResponse(response, status=code)
```

### 10. Frontend Improvements

#### Missing Input Validation
**Issue**: Client-side validation is minimal

**Recommendations**:
- Add input sanitization for usernames
- Validate configuration before saving
- Add loading states for async operations
- Implement proper error boundaries

```javascript
// Add validation
function isValidTikTokUsername(username) {
    // TikTok usernames: 2-24 chars, alphanumeric + underscore/period
    const regex = /^[a-zA-Z0-9_.]{2,24}$/;
    return regex.test(username);
}

function addStream() {
    const input = document.getElementById('new-stream-input');
    const username = input.value.trim();
    
    if (!username) {
        showError("Please enter a username");
        return;
    }
    
    if (!isValidTikTokUsername(username)) {
        showError("Invalid TikTok username format");
        return;
    }
    
    // ... rest of logic
}
```

## 🟢 Nice-to-Have Enhancements

### 11. Testing Infrastructure

**Create test structure**:
```
tests/
├── __init__.py
├── test_service.py
├── test_views.py
├── test_integration.py
└── fixtures/
    └── sample_config.json
```

**Example test**:
```python
# tests/test_service.py
import pytest
from monitor.service import MonitorService

@pytest.fixture
def service():
    return MonitorService()

def test_keyword_detection(service):
    service.keywords = "test,demo"
    # Add test logic
    pass

def test_obs_connection_failure(service):
    service.obs_password = "wrong_password"
    success, msg = service.connect_obs()
    assert not success
```

### 12. Performance Optimizations

#### WebSocket Instead of Polling
**Issue**: Frontend polls `/api/status` endpoint repeatedly

**Recommendation**: Implement Django Channels for WebSocket support
```python
# Install: pip install channels channels-redis

# settings.py
INSTALLED_APPS = [
    # ...
    'channels',
]

ASGI_APPLICATION = 'tiktok_obs.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### 13. Monitoring & Metrics

**Add metrics collection**:
- Number of streams monitored
- Triggers detected per hour
- OBS replay success rate
- Connection uptime per stream

**Use Django Admin for monitoring**:
```python
# monitor/admin.py
from django.contrib import admin
from .models import Stream, TriggerEvent, LogEntry

@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ['username', 'is_active', 'last_connected']
    list_filter = ['is_active']
    search_fields = ['username']

@admin.register(TriggerEvent)
class TriggerEventAdmin(admin.ModelAdmin):
    list_display = ['stream', 'chatter_username', 'trigger_word', 'timestamp']
    list_filter = ['trigger_word', 'timestamp']
    search_fields = ['chatter_username', 'message']
    date_hierarchy = 'timestamp'
```

### 14. Documentation

**Add docstrings**:
```python
class MonitorService:
    """
    Singleton service managing TikTok stream monitoring and OBS integration.
    
    This service handles:
    - Multiple concurrent TikTok live stream connections
    - Real-time chat message processing
    - Keyword trigger detection
    - OBS WebSocket communication
    - Replay buffer management and file naming
    
    Attributes:
        tiktok_clients (dict): Map of username to TikTokLiveClient instances
        obs_client: OBS WebSocket client for replay control
        logs (deque): Circular buffer of log messages (max 100)
        notification_queue (deque): Queue of trigger notifications for UI
    """
    
    def start_stream(self, username: str) -> bool:
        """
        Start monitoring a TikTok live stream.
        
        Args:
            username: TikTok username without @ symbol
            
        Returns:
            bool: True if start initiated successfully, False otherwise
            
        Raises:
            ConnectionError: If TikTok connection fails
        """
        pass
```

### 15. Deployment Readiness

**Create deployment configuration**:

**Docker Support**:
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p logs

# Run migrations and start server
CMD python manage.py migrate && \
    python manage.py runserver 0.0.0.0:8000
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ~/Videos:/videos
    environment:
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - OBS_PASSWORD=${OBS_PASSWORD}
      - DEBUG=False
    restart: unless-stopped
```

### 16. Feature Enhancements

- **Multi-language Support**: Detect keywords in multiple languages
- **Custom Replay Duration**: Configure replay buffer length per trigger
- **Statistics Dashboard**: Visualize triggers over time with charts
- **Webhook Support**: Send notifications to Discord/Slack when triggers occur
- **Regex Pattern Support**: Advanced pattern matching for triggers
- **Stream Health Monitoring**: Track connection stability and reconnection logic
- **User Management**: Multiple user profiles with different configurations
- **Cloud Storage Integration**: Automatically upload replays to S3/Google Cloud Storage

## 📊 Code Quality Tools

### Setup Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
```

## 🎯 Priority Implementation Order

1. **Security fixes** (SECRET_KEY, CSRF, file handling)
2. **Requirements.txt** and proper dependency management
3. **Logging infrastructure** 
4. **Cross-platform compatibility**
5. **Database models** for persistence
6. **Error handling** improvements
7. **Testing framework**
8. **WebSocket implementation**
9. **Docker deployment**
10. **Feature enhancements**

## 📚 Additional Resources

- [Django Security Best Practices](https://docs.djangoproject.com/en/5.0/topics/security/)
- [Django Channels Documentation](https://channels.readthedocs.io/)
- [Python Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [The Twelve-Factor App](https://12factor.net/)
