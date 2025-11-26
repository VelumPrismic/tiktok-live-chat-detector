from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/save_config', views.save_config, name='save_config'),
    path('api/connect_obs', views.connect_obs, name='connect_obs'),
    path('api/stream_action', views.stream_action, name='stream_action'),
    path('api/status', views.get_status, name='get_status'),
    path('api/clear_logs', views.clear_logs, name='clear_logs'),
    path('replays/', views.replays, name='replays'),
    path('video/<str:filename>', views.serve_video, name='serve_video'),
]
