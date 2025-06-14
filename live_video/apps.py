# live_video/apps.py
# type: ignore

from django.apps import AppConfig


class LiveVideoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'live_video'
    verbose_name = 'Live Video Management'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import live_video.signals  # noqa
        except ImportError:
            pass