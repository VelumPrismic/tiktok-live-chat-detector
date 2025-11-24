from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .service import MonitorService

def index(request):
    service = MonitorService.get_instance()
    context = {
        "username": service.username,
        "obs_password": service.obs_password,
        "source_name": service.source_name,
        "keywords": service.keywords,
        "notifications_enabled": service.notifications_enabled,
        "notification_duration": service.notification_duration,
        "is_monitoring": service.is_monitoring,
        "obs_connected": service.obs_client is not None
    }
    return render(request, 'monitor/index.html', context)

@csrf_exempt
def save_config(request):
    if request.method == "POST":
        service = MonitorService.get_instance()
        username = request.POST.get("username")
        obs_password = request.POST.get("obs_password")
        source_name = request.POST.get("source_name")
        keywords = request.POST.get("keywords")
        notifications_enabled = request.POST.get("notifications_enabled") == 'true'
        try:
            notification_duration = int(request.POST.get("notification_duration", 5))
        except ValueError:
            notification_duration = 5
            
        service.save_config(username, obs_password, source_name, keywords, notifications_enabled, notification_duration)
        return JsonResponse({"status": "ok", "message": "Config saved"})
    return JsonResponse({"status": "error"}, status=400)

@csrf_exempt
def connect_obs(request):
    service = MonitorService.get_instance()
    success, msg = service.connect_obs()
    return JsonResponse({"status": "ok" if success else "error", "message": msg})

@csrf_exempt
def toggle_monitoring(request):
    service = MonitorService.get_instance()
    if request.method == "POST":
        # Save config first if provided
        username = request.POST.get("username")
        if username:
            notifications_enabled = request.POST.get("notifications_enabled") == 'true'
            try:
                notification_duration = int(request.POST.get("notification_duration", 5))
            except ValueError:
                notification_duration = 5
                
            service.save_config(
                request.POST.get("username"),
                request.POST.get("obs_password"),
                request.POST.get("source_name"),
                request.POST.get("keywords"),
                notifications_enabled,
                notification_duration
            )
    
    result = service.toggle_monitoring()
    if isinstance(result, bool):
        return JsonResponse({"status": "ok", "is_monitoring": result})
    else:
        return JsonResponse({"status": "error", "message": result[1] if isinstance(result, tuple) else "Error"})

def get_status(request):
    service = MonitorService.get_instance()
    notifications = []
    while service.notification_queue:
        notifications.append(service.notification_queue.popleft())
        
    return JsonResponse({
        "logs": list(service.logs),
        "is_monitoring": service.is_monitoring,
        "obs_connected": service.obs_client is not None,
        "notifications": notifications
    })
