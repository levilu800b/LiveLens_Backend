#type: ignore

from django.apps import AppConfig

class AuthappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authapp'
    verbose_name = 'Authentication'
    
    def ready(self):
        # Import signals here to ensure they are registered when the app is ready
        _ = __import__('authapp.signals')