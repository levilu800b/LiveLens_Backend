# email_notifications/apps.py
# type: ignore

from django.apps import AppConfig

class EmailNotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'email_notifications'
    verbose_name = 'Email Notifications'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        try:
            import email_notifications.signals
        except ImportError:
            pass