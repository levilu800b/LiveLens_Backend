#type: ignore

# podcasts/apps.py
from django.apps import AppConfig

class PodcastsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'podcasts'
    verbose_name = 'Podcasts'
    
    def ready(self):
        """Import signals when app is ready"""
        _signals = __import__('podcasts.signals')