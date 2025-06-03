#type: ignore

# stories/apps.py
from django.apps import AppConfig

class StoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stories'
    verbose_name = 'Stories'
    
    def ready(self):
        """Import signals when app is ready"""
        _ = __import__('stories.signals')