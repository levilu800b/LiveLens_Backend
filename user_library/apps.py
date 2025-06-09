# user_library/apps.py
# type: ignore

from django.apps import AppConfig

class UserLibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_library'
    verbose_name = 'User Library'