#type: ignore

# media_content/apps.py
from django.apps import AppConfig

class MediaContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'media_content'
    verbose_name = 'Media Content'
    
    def ready(self):
        # Import signals to ensure they are registered
        try:
            import media_content.signals  # noqa: F401
        except ImportError:
            pass