# live_video/signals.py
# type: ignore

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import os

from .models import LiveVideo, LiveVideoComment, LiveVideoInteraction

User = get_user_model()


@receiver(post_save, sender=LiveVideo)
def live_video_post_save(sender, instance, created, **kwargs):
    """Handle actions after live video is saved"""
    if created:
        # Send notification to subscribers when a new live video is scheduled
        send_live_video_notification(instance, 'scheduled')
    
    # Update hero live video cache when a featured live video is created/updated
    if instance.is_featured and instance.live_status in ['live', 'scheduled']:
        # Here you could invalidate cache or trigger frontend updates
        pass


@receiver(pre_delete, sender=LiveVideo)
def live_video_pre_delete(sender, instance, **kwargs):
    """Clean up files before live video deletion"""
    # Delete thumbnail file if it exists
    if instance.thumbnail:
        try:
            instance.thumbnail.delete(save=False)
        except Exception:
            pass
    
    # Delete video file if it exists
    if instance.video_file:
        try:
            instance.video_file.delete(save=False)
        except Exception:
            pass


@receiver(post_save, sender=LiveVideoComment)
def live_video_comment_post_save(sender, instance, created, **kwargs):
    """Handle actions after live video comment is saved"""
    if created and not instance.is_hidden:
        # Update comment count on live video
        comment_count = instance.live_video.live_comments.filter(is_hidden=False).count()
        LiveVideo.objects.filter(id=instance.live_video.id).update(comment_count=comment_count)
        
        # Send notification to live video owner about new comment
        if instance.user != instance.live_video.author:
            send_comment_notification(instance)


@receiver(post_delete, sender=LiveVideoComment)
def live_video_comment_post_delete(sender, instance, **kwargs):
    """Handle actions after live video comment is deleted"""
    # Update comment count on live video
    try:
        comment_count = instance.live_video.live_comments.filter(is_hidden=False).count()
        LiveVideo.objects.filter(id=instance.live_video.id).update(comment_count=comment_count)
    except Exception:
        pass


@receiver(post_save, sender=LiveVideoInteraction)
def live_video_interaction_post_save(sender, instance, created, **kwargs):
    """Handle actions after live video interaction is saved"""
    if created:
        # Update like count for like interactions
        if instance.interaction_type == 'like':
            like_count = LiveVideoInteraction.objects.filter(
                live_video=instance.live_video,
                interaction_type='like'
            ).count()
            LiveVideo.objects.filter(id=instance.live_video.id).update(like_count=like_count)
        
        # Send notification for new likes (but not too frequently)
        if instance.interaction_type == 'like' and instance.user != instance.live_video.author:
            # Only send notification if it's a significant milestone (every 10 likes)
            if instance.live_video.like_count % 10 == 0:
                send_like_milestone_notification(instance.live_video)


@receiver(post_delete, sender=LiveVideoInteraction)
def live_video_interaction_post_delete(sender, instance, **kwargs):
    """Handle actions after live video interaction is deleted"""
    # Update like count for like interactions
    if instance.interaction_type == 'like':
        try:
            like_count = LiveVideoInteraction.objects.filter(
                live_video=instance.live_video,
                interaction_type='like'
            ).count()
            LiveVideo.objects.filter(id=instance.live_video.id).update(like_count=like_count)
        except Exception:
            pass


def send_live_video_notification(live_video, event_type):
    """Send notification about live video events"""
    if not settings.EMAIL_HOST_USER:
        return
    
    # Get users who might be interested (you can customize this logic)
    # For now, we'll notify all active users, but you could have a subscription system
    interested_users = User.objects.filter(is_active=True, email_notifications=True)[:100]
    
    if event_type == 'scheduled':
        subject = f"New Live Stream Scheduled: {live_video.title}"
        message_template = """
        Hi {user_name},
        
        A new live stream has been scheduled on our platform!
        
        Title: {title}
        Host: {host}
        Scheduled Time: {scheduled_time}
        
        {description}
        
        Don't miss it! Set a reminder and join us live.
        
        Best regards,
        Streaming Platform Team
        """
    elif event_type == 'started':
        subject = f"🔴 LIVE NOW: {live_video.title}"
        message_template = """
        Hi {user_name},
        
        The live stream "{title}" is now LIVE!
        
        Host: {host}
        Join now to participate in the live chat and experience.
        
        Best regards,
        Streaming Platform Team
        """
    else:
        return
    
    # Send emails (consider using a task queue like Celery for production)
    for user in interested_users:
        try:
            formatted_message = message_template.format(
                user_name=user.first_name or user.username,
                title=live_video.title,
                host=live_video.host_name or live_video.author.username,
                scheduled_time=live_video.scheduled_start_time.strftime("%Y-%m-%d %H:%M %Z") if live_video.scheduled_start_time else "TBA",
                description=live_video.short_description or live_video.description[:200] + "..."
            )
            
            send_mail(
                subject,
                formatted_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send notification email to {user.email}: {e}")


def send_comment_notification(comment):
    """Send notification to live video owner about new comment"""
    if not settings.EMAIL_HOST_USER:
        return
    
    live_video_owner = comment.live_video.author
    
    # Only send if owner has email notifications enabled
    if not getattr(live_video_owner, 'email_notifications', True):
        return
    
    subject = f"New comment on your live video: {comment.live_video.title}"
    
    message = f"""
    Hi {live_video_owner.first_name or live_video_owner.username},
    
    {comment.user.username} commented on your live video "{comment.live_video.title}":
    
    "{comment.message}"
    
    Live Video: {comment.live_video.title}
    Comment Time: {comment.timestamp.strftime("%Y-%m-%d %H:%M %Z")}
    
    You can manage comments from your admin dashboard.
    
    Best regards,
    Streaming Platform Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [live_video_owner.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send comment notification to {live_video_owner.email}: {e}")


def send_like_milestone_notification(live_video):
    """Send notification for like milestones"""
    if not settings.EMAIL_HOST_USER:
        return
    
    owner = live_video.author
    
    # Only send if owner has email notifications enabled
    if not getattr(owner, 'email_notifications', True):
        return
    
    subject = f"🎉 Milestone: {live_video.like_count} likes on your live video!"
    
    message = f"""
    Hi {owner.first_name or owner.username},
    
    Congratulations! Your live video "{live_video.title}" has reached {live_video.like_count} likes!
    
    Live Video Stats:
    - Total Views: {live_video.total_views}
    - Likes: {live_video.like_count}
    - Comments: {live_video.comment_count}
    - Peak Viewers: {live_video.peak_viewers}
    
    Keep up the great content!
    
    Best regards,
    Streaming Platform Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [owner.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send milestone notification to {owner.email}: {e}")


# Signal to automatically start scheduled live videos (you could use this with a cron job)
def auto_start_scheduled_streams():
    """Auto-start live streams that are scheduled to start now"""
    now = timezone.now()
    
    # Find streams scheduled to start within the last 5 minutes (to account for delays)
    scheduled_streams = LiveVideo.objects.filter(
        live_status='scheduled',
        auto_start=True,
        scheduled_start_time__lte=now,
        scheduled_start_time__gte=now - timezone.timedelta(minutes=5)
    )
    
    for stream in scheduled_streams:
        try:
            stream.start_stream()
            send_live_video_notification(stream, 'started')
            print(f"Auto-started live stream: {stream.title}")
        except Exception as e:
            print(f"Failed to auto-start stream {stream.title}: {e}")


# Signal to automatically end live streams that have exceeded their duration
def auto_end_expired_streams():
    """Auto-end live streams that have exceeded their scheduled duration"""
    now = timezone.now()
    
    # Find live streams that should have ended
    expired_streams = LiveVideo.objects.filter(
        live_status='live',
        scheduled_end_time__isnull=False,
        scheduled_end_time__lte=now
    )
    
    for stream in expired_streams:
        try:
            stream.end_stream()
            print(f"Auto-ended expired live stream: {stream.title}")
        except Exception as e:
            print(f"Failed to auto-end stream {stream.title}: {e}")