from django.shortcuts import render
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import SuspiciousFileOperation
from .service import MonitorService
from .utils import get_video_directory
import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('monitor')

def index(request):
    service = MonitorService.get_instance()
    context = {
        "usernames": service.usernames,
        "obs_password": service.obs_password,
        "source_name": service.source_name,
        "keywords": service.keywords,
        "notifications_enabled": service.notifications_enabled,
        "notification_duration": service.notification_duration,
        "is_monitoring": service.is_monitoring,
        "obs_connected": service.obs_client is not None
    }
    return render(request, 'monitor/index.html', context)

def replays(request):
    """Display list of replay videos from the video directory"""
    try:
        video_dir = get_video_directory()
        videos = []
        
        if video_dir.exists():
            # List only video files, sort by creation time desc
            for f in video_dir.iterdir():
                if f.is_file() and f.suffix.lower() in ('.mp4', '.mkv', '.mov', '.avi'):
                    try:
                        stat = f.stat()
                        videos.append({
                            'name': f.name,
                            'size': f"{stat.st_size / (1024*1024):.1f} MB",
                            'date': datetime.fromtimestamp(stat.st_ctime),
                            'path': str(f)
                        })
                    except Exception as e:
                        logger.warning(f"Error reading file {f}: {e}")
                        continue
        
        # Sort by date desc
        videos.sort(key=lambda x: x['date'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error listing replay videos: {e}", exc_info=True)
        videos = []
    
    return render(request, 'monitor/replays.html', {'videos': videos})

def serve_video(request, filename):
    """Serve a video file from the video directory"""
    try:
        video_dir = get_video_directory()
        
        # Sanitize filename - remove any path components
        filename = os.path.basename(filename)
        
        # Construct full path
        file_path = video_dir / filename
        
        # Security check - ensure file is within video directory
        try:
            # Resolve to absolute paths and check
            real_file = file_path.resolve()
            real_dir = video_dir.resolve()
            
            if not str(real_file).startswith(str(real_dir)):
                logger.warning(f"Path traversal attempt: {filename}")
                raise SuspiciousFileOperation("Invalid file path")
        except Exception as e:
            logger.error(f"Security check failed for {filename}: {e}")
            raise Http404("Invalid file path")
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            raise Http404("Video not found")
        
        # Return file response
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Type'] = 'video/mp4'
        return response
        
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error serving video {filename}: {e}", exc_info=True)
        raise Http404("Video not found")

@csrf_exempt
def save_config(request):
    if request.method == "POST":
        service = MonitorService.get_instance()
        usernames_raw = request.POST.get("username")
        
        if not usernames_raw:
            usernames = []
        elif "," in usernames_raw:
            usernames = [u.strip() for u in usernames_raw.split(",") if u.strip()]
        else:
             # Check if it's coming as a JSON string or just a string
            usernames = [usernames_raw.strip()]

        # If the frontend sends it as a JSON array string, we might need to parse it differently,
        # but for now let's assume the frontend sends a comma-separated string for simplicity 
        # or we adapt the frontend to send a list.
        # Actually, better to rely on service to split if passed as string.
        
        obs_password = request.POST.get("obs_password")
        source_name = request.POST.get("source_name")
        keywords = request.POST.get("keywords")
        notifications_enabled = request.POST.get("notifications_enabled") == 'true'
        try:
            notification_duration = int(request.POST.get("notification_duration", 5))
        except ValueError:
            notification_duration = 5
            
        service.save_config(usernames_raw, obs_password, source_name, keywords, notifications_enabled, notification_duration)
        return JsonResponse({"status": "ok", "message": "Config saved"})
    return JsonResponse({"status": "error"}, status=400)

@csrf_exempt
def connect_obs(request):
    service = MonitorService.get_instance()
    success, msg = service.connect_obs()
    return JsonResponse({"status": "ok" if success else "error", "message": msg})

@csrf_exempt
def stream_action(request):
    service = MonitorService.get_instance()
    if request.method == "POST":
        action = request.POST.get("action") # start or stop
        username = request.POST.get("username")
        
        if not username:
            return JsonResponse({"status": "error", "message": "Username required"})
            
        if action == "start":
            service.start_stream(username)
            return JsonResponse({"status": "ok", "message": f"Started monitoring @{username}"})
        elif action == "stop":
            service.stop_stream(username)
            return JsonResponse({"status": "ok", "message": f"Stopped monitoring @{username}"})
            
    return JsonResponse({"status": "error", "message": "Invalid action"})

def get_status(request):
    service = MonitorService.get_instance()
    notifications = []
    while service.notification_queue:
        notifications.append(service.notification_queue.popleft())
        
    # Support filtering logs by source stream
    stream_filter = request.GET.get('stream')
    logs = list(service.logs)
    
    if stream_filter:
        logs = [log for log in logs if log.get('source_stream') == stream_filter]
        
    # Get active streams status
    active_streams = {}
    for user in service.usernames:
        active_streams[user] = service.is_stream_active(user)
        
    return JsonResponse({
        "logs": logs,
        "active_streams": active_streams, # Map of username -> bool (is_monitoring)
        "obs_connected": service.obs_client is not None,
        "notifications": notifications
    })


@csrf_exempt
def clear_logs(request):
    service = MonitorService.get_instance()
    service.logs.clear()
    return JsonResponse({"status": "ok", "message": "Logs cleared"})
