# admin_dashboard/signals.py
# type: ignore

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import UserActivity, SystemAlert
from .utils import create_system_alert, get_client_ip

User = get_user_model()

@receiver(post_save, sender=User)
def user_activity_on_save(sender, instance, created, **kwargs):
    """Track user creation and updates"""
    
    if created:
        # User signup activity
        UserActivity.objects.create(
            user=instance,
            activity_type='signup',
            description=f"User {instance.username} signed up",
            metadata={'email': instance.email}
        )
        
        # Create welcome alert for admin
        create_system_alert(
            title="New User Registration",
            message=f"New user {instance.username} ({instance.email}) has registered",
            alert_type="info",
            category="user",
            priority=1,
            metadata={'user_id': str(instance.id), 'username': instance.username}
        )

@receiver(post_save, sender=SystemAlert)
def alert_post_save(sender, instance, created, **kwargs):
    """Handle alert creation"""
    
    if created and instance.alert_type in ['critical', 'error']:
        # Log critical alerts
        UserActivity.objects.create(
            activity_type='error',
            description=f"System alert: {instance.title}",
            metadata={
                'alert_id': str(instance.id),
                'alert_type': instance.alert_type,
                'category': instance.category
            }
        )

# You can add more signal handlers for other models as needed
# For example, tracking content creation, comments, etc.