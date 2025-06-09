# sneak_peeks/apps.py
# type: ignore

from django.apps import AppConfig

class SneakPeeksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sneak_peeks'
    verbose_name = 'Sneak Peeks'