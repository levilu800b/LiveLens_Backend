# Create missing app structures
# ai_service/apps.py
# type: ignore

from django.apps import AppConfig

class AiServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_service'
    verbose_name = 'AI Service'