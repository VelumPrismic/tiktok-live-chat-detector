from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/save_config', views.save_config, name='save_config'),
    path('api/connect_obs', views.connect_obs, name='connect_obs'),
    path('api/toggle_monitoring', views.toggle_monitoring, name='toggle_monitoring'),
    path('api/status', views.get_status, name='get_status'),
    path('replays/', views.replays, name='replays'),
    path('video/<str:filename>', views.serve_video, name='serve_video'),
]
