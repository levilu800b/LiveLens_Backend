# type: ignore

# animations/apps.py
from django.apps import AppConfig

class AnimationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'animations'
    verbose_name = 'Animations'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import animations.signals  # noqa: F401
        except ImportError:
            pass