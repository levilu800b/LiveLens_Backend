# comments/apps.py
# type: ignore

from django.apps import AppConfig

class CommentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comments'
    verbose_name = 'Comments'
    
    def ready(self):
        _ = __import__('comments.signals')