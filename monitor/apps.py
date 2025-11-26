from django.apps import AppConfig


class MonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitor'

    def ready(self):
        try:
            from tiktok_live_patch import apply_patch
            apply_patch()
        except ImportError:
            pass
