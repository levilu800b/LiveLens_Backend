# admin_content/apps.py
# type: ignore

from django.apps import AppConfig

class AdminContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_content'
    verbose_name = 'Admin Content Management'