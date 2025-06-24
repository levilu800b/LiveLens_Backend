# email_notifications/signals.py
# type: ignore

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from .utils import (
    send_welcome_email, 
    send_password_changed_email, 
    send_content_upload_notification,
    send_live_video_notification
)
from .models import NewsletterSubscription
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=User)
def send_welcome_email_on_verification(sender, instance, created, **kwargs):
    """
    Send welcome email when user is verified (after email verification)
    """
    if not created and instance.is_verified:
        # Check if welcome email was already sent by checking if we have a previous state
        try:
            # Get the previous state from database
            previous_user = User.objects.get(pk=instance.pk)
            
            # Only send if user just got verified (wasn't verified before)
            if hasattr(instance, '_state') and instance._state.adding is False:
                # This is an update, check if verification status changed
                from django.core.cache import cache
                cache_key = f"user_verified_{instance.pk}"
                was_verified = cache.get(cache_key, False)
                
                if not was_verified and instance.is_verified:
                    # User just got verified, send welcome email
                    send_welcome_email(instance)
                    logger.info(f"Welcome email triggered for user: {instance.email}")
                
                # Update cache
                cache.set(cache_key, instance.is_verified, 300)  # 5 minutes cache
                
        except Exception as e:
            logger.error(f"Error in welcome email signal: {str(e)}")

# Signal for Stories
try:
    from stories.models import Story
    
    @receiver(post_save, sender=Story)
    def notify_story_upload(sender, instance, created, **kwargs):
        """Send notification when new story is uploaded"""
        if created and instance.status == 'published':
            try:
                send_content_upload_notification(instance, 'story')
                logger.info(f"Story upload notification sent for: {instance.title}")
            except Exception as e:
                logger.error(f"Error sending story notification: {str(e)}")
                
except ImportError:
    logger.warning("Stories app not found, story notifications disabled")

# Signal for Films
try:
    from media_content.models import Film
    
    @receiver(post_save, sender=Film)
    def notify_film_upload(sender, instance, created, **kwargs):
        """Send notification when new film is uploaded"""
        if created and instance.status == 'published':
            try:
                send_content_upload_notification(instance, 'film')
                logger.info(f"Film upload notification sent for: {instance.title}")
            except Exception as e:
                logger.error(f"Error sending film notification: {str(e)}")
                
except ImportError:
    logger.warning("Media content app not found, film notifications disabled")

# Signal for Content
try:
    from media_content.models import Content
    
    @receiver(post_save, sender=Content)
    def notify_content_upload(sender, instance, created, **kwargs):
        """Send notification when new content is uploaded"""
        if created and instance.status == 'published':
            try:
                send_content_upload_notification(instance, 'content')
                logger.info(f"Content upload notification sent for: {instance.title}")
            except Exception as e:
                logger.error(f"Error sending content notification: {str(e)}")
                
except ImportError:
    logger.warning("Media content app not found, content notifications disabled")

# Signal for Podcasts
try:
    from podcasts.models import Podcast
    
    @receiver(post_save, sender=Podcast)
    def notify_podcast_upload(sender, instance, created, **kwargs):
        """Send notification when new podcast is uploaded"""
        if created and instance.status == 'published':
            try:
                send_content_upload_notification(instance, 'podcast')
                logger.info(f"Podcast upload notification sent for: {instance.title}")
            except Exception as e:
                logger.error(f"Error sending podcast notification: {str(e)}")
                
except ImportError:
    logger.warning("Podcasts app not found, podcast notifications disabled")

# Signal for Animations
try:
    from animations.models import Animation
    
    @receiver(post_save, sender=Animation)
    def notify_animation_upload(sender, instance, created, **kwargs):
        """Send notification when new animation is uploaded"""
        if created and instance.status == 'published':
            try:
                send_content_upload_notification(instance, 'animation')
                logger.info(f"Animation upload notification sent for: {instance.title}")
            except Exception as e:
                logger.error(f"Error sending animation notification: {str(e)}")
                
except ImportError:
    logger.warning("Animations app not found, animation notifications disabled")

# Signal for Sneak Peeks
try:
    from sneak_peeks.models import SneakPeek
    
    @receiver(post_save, sender=SneakPeek)
    def notify_sneak_peek_upload(sender, instance, created, **kwargs):
        """Send notification when new sneak peek is uploaded"""
        if created and instance.status == 'published':
            try:
                send_content_upload_notification(instance, 'sneak_peek')
                logger.info(f"Sneak peek upload notification sent for: {instance.title}")
            except Exception as e:
                logger.error(f"Error sending sneak peek notification: {str(e)}")
                
except ImportError:
    logger.warning("Sneak peeks app not found, sneak peek notifications disabled")

# Signal for Live Videos
try:
    from live_video.models import LiveVideo
    
    @receiver(post_save, sender=LiveVideo)
    def notify_live_video_start(sender, instance, created, **kwargs):
        """Send notification when live video starts"""
        if created and instance.is_live:
            try:
                send_live_video_notification()
                logger.info(f"Live video notification sent for: {instance.title}")
            except Exception as e:
                logger.error(f"Error sending live video notification: {str(e)}")
                
except ImportError:
    logger.warning("Live video app not found, live video notifications disabled")

@receiver(post_save, sender=NewsletterSubscription)
def auto_subscribe_verified_users(sender, instance, created, **kwargs):
    """
    Automatically subscribe verified users to newsletter when they create account
    """
    if created and instance.user and not instance.is_verified:
        # If user is already verified, verify the subscription too
        if instance.user.is_verified:
            instance.verify_subscription()

# Custom signal for password changes (to be used in password change view)
def send_password_change_notification(user, request=None):
    """
    Function to be called manually when password is changed
    This should be called from the password change view
    """
    try:
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        send_password_changed_email(user, ip_address)
        logger.info(f"Password change notification sent for user: {user.email}")
        
    except Exception as e:
        logger.error(f"Error sending password change notification: {str(e)}")

# Helper function for triggering live video notifications
def trigger_live_notification():
    """
    Function to be called manually when going live
    This should be called from the admin dashboard when starting a live stream
    """
    try:
        send_live_video_notification()
        logger.info("Live video notification sent to all subscribers")
    except Exception as e:
        logger.error(f"Error sending live video notification: {str(e)}")

# Helper function for triggering content notifications manually
def trigger_content_notification(content_instance, content_type):
    """
    Function to manually trigger content notifications
    Useful for re-sending notifications or bulk notifications
    """
    try:
        send_content_upload_notification(content_instance, content_type)
        logger.info(f"Manual content notification sent for: {content_instance.title}")
    except Exception as e:
        logger.error(f"Error sending manual content notification: {str(e)}")