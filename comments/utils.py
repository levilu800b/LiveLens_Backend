# comments/utils.py
# type: ignore

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from .models import CommentNotification
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_comment_activity(user, action, comment, request=None):
    """Log comment-related user activity"""
    try:
        # You can expand this to save to a UserActivity model if needed
        logger.info(f"User {user.username} performed {action} on comment {comment.id}")
        
        # Additional logging can be added here
        # For example, save to database, send to analytics service, etc.
        
    except Exception as e:
        logger.error(f"Failed to log comment activity: {e}")

def send_comment_notification(recipient, sender, comment, notification_type):
    """Send notification for comment-related activities"""
    
    # Don't send notification to self
    if recipient == sender:
        return
    
    # Create notification record
    try:
        notification_messages = {
            'reply': f"{sender.username} replied to your comment",
            'like': f"{sender.username} liked your comment",
            'mention': f"{sender.username} mentioned you in a comment",
            'moderation': f"Your comment has been moderated by {sender.username}"
        }
        
        message = notification_messages.get(notification_type, "You have a new comment notification")
        
        notification = CommentNotification.objects.create(
            recipient=recipient,
            sender=sender,
            comment=comment,
            notification_type=notification_type,
            message=message
        )
        
        # Send email notification if user has email notifications enabled
        if hasattr(recipient, 'preferences') and recipient.preferences.email_notifications:
            send_comment_email_notification(notification)
            
    except Exception as e:
        logger.error(f"Failed to create comment notification: {e}")

def send_comment_email_notification(notification):
    """Send email notification for comment activity"""
    
    try:
        subject_templates = {
            'reply': f"Someone replied to your comment",
            'like': f"Someone liked your comment",
            'mention': f"You were mentioned in a comment",
            'moderation': f"Your comment has been moderated"
        }
        
        subject = subject_templates.get(
            notification.notification_type, 
            "New comment notification"
        )
        
        # Get content title
        content_title = "Unknown Content"
        if notification.comment.content_object:
            content_title = getattr(
                notification.comment.content_object, 
                'title', 
                str(notification.comment.content_object)
            )
        
        context = {
            'recipient': notification.recipient,
            'sender': notification.sender,
            'comment': notification.comment,
            'content_title': content_title,
            'notification_type': notification.notification_type,
            'notification': notification,
            'platform_name': 'Streaming Platform',
            'site_url': settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'
        }
        
        # Render email templates
        html_message = render_to_string('emails/comment_notification.html', context)
        plain_message = render_to_string('emails/comment_notification.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            html_message=html_message,
            fail_silently=True
        )
        
    except Exception as e:
        logger.error(f"Failed to send comment email notification: {e}")

def clean_comment_text(text):
    """Clean and sanitize comment text"""
    import bleach
    
    # Allow basic formatting tags
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'br']
    allowed_attributes = {}
    
    # Clean the text
    cleaned_text = bleach.clean(
        text, 
        tags=allowed_tags, 
        attributes=allowed_attributes, 
        strip=True
    )
    
    return cleaned_text.strip()

def detect_mentions(text):
    """Detect @mentions in comment text"""
    import re
    
    # Find all @username mentions
    mention_pattern = r'@(\w+)'
    mentions = re.findall(mention_pattern, text)
    
    # Get valid users from mentions
    mentioned_users = []
    for username in mentions:
        try:
            user = User.objects.get(username=username)
            mentioned_users.append(user)
        except User.DoesNotExist:
            continue
    
    return mentioned_users

def process_comment_mentions(comment, sender):
    """Process mentions in a comment and send notifications"""
    
    mentioned_users = detect_mentions(comment.text)
    
    for user in mentioned_users:
        if user != sender:  # Don't notify self
            send_comment_notification(
                recipient=user,
                sender=sender,
                comment=comment,
                notification_type='mention'
            )

def calculate_comment_score(comment):
    """Calculate a score for comment ranking/sorting"""
    
    # Simple scoring algorithm based on likes, recency, and replies
    like_score = comment.like_count * 2
    dislike_penalty = comment.dislike_count * -1
    reply_bonus = comment.reply_count * 0.5
    
    # Time decay factor (newer comments get higher score)
    from django.utils import timezone
    import math
    
    hours_since_creation = (timezone.now() - comment.created_at).total_seconds() / 3600
    time_decay = math.exp(-hours_since_creation / 24)  # Decay over 24 hours
    
    score = (like_score + dislike_penalty + reply_bonus) * time_decay
    
    return max(score, 0)  # Ensure non-negative score

def get_trending_comments(content_type, object_id, limit=5):
    """Get trending comments for a piece of content"""
    
    from .models import Comment
    from django.db.models import F
    
    comments = Comment.objects.filter(
        content_type=content_type,
        object_id=object_id,
        status='published',
        parent__isnull=True  # Only top-level comments
    ).annotate(
        score=F('like_count') * 2 - F('dislike_count') + F('reply_count')
    ).order_by('-score', '-created_at')[:limit]
    
    return comments

def get_comment_statistics(content_type=None, object_id=None, user=None):
    """Get comment statistics"""
    
    from .models import Comment
    from django.db.models import Count, Sum, Avg
    
    queryset = Comment.objects.filter(status='published')
    
    if content_type and object_id:
        queryset = queryset.filter(content_type=content_type, object_id=object_id)
    
    if user:
        queryset = queryset.filter(user=user)
    
    stats = queryset.aggregate(
        total_comments=Count('id'),
        total_likes=Sum('like_count'),
        total_replies=Sum('reply_count'),
        average_likes=Avg('like_count'),
        average_replies=Avg('reply_count')
    )
    
    return stats

def moderate_comment_content(text):
    """Basic content moderation for comments"""
    
    # List of inappropriate words/phrases
    inappropriate_words = [
        'spam', 'scam', 'fraud', 'hate', 'abuse'
        # Add more words as needed
    ]
    
    text_lower = text.lower()
    
    for word in inappropriate_words:
        if word in text_lower:
            return False, f"Comment contains inappropriate content: {word}"
    
    # Check for excessive caps (more than 50% uppercase)
    if len(text) > 10:
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
        if caps_ratio > 0.5:
            return False, "Comment contains excessive uppercase text"
    
    # Check for excessive special characters
    special_char_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
    if special_char_count > len(text) * 0.3:
        return False, "Comment contains too many special characters"
    
    return True, "Comment is appropriate"

def check_comment_rate_limit(user, time_window_minutes=5, max_comments=10):
    """Check if user is posting comments too frequently"""
    
    from .models import Comment
    from django.utils import timezone
    from datetime import timedelta
    
    time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
    
    recent_comment_count = Comment.objects.filter(
        user=user,
        created_at__gte=time_threshold
    ).count()
    
    return recent_comment_count < max_comments

def export_comments_to_csv(content_type=None, object_id=None):
    """Export comments to CSV format"""
    
    import csv
    import io
    from .models import Comment
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'User', 'Text', 'Content Type', 'Content ID', 
        'Likes', 'Dislikes', 'Replies', 'Status', 'Created At'
    ])
    
    # Filter comments
    queryset = Comment.objects.select_related('user', 'content_type')
    
    if content_type and object_id:
        queryset = queryset.filter(content_type=content_type, object_id=object_id)
    
    # Write data
    for comment in queryset:
        writer.writerow([
            str(comment.id),
            comment.user.username,
            comment.text[:100] + '...' if len(comment.text) > 100 else comment.text,
            comment.content_type.model,
            str(comment.object_id),
            comment.like_count,
            comment.dislike_count,
            comment.reply_count,
            comment.status,
            comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    return output.getvalue()

def bulk_moderate_comments(comment_ids, action, moderator, reason=''):
    """Bulk moderate multiple comments"""
    
    from .models import Comment, CommentModerationLog
    from django.utils import timezone
    
    comments = Comment.objects.filter(id__in=comment_ids)
    moderated_count = 0
    
    for comment in comments:
        old_status = comment.status
        
        if action == 'approve':
            comment.status = 'published'
            comment.is_flagged = False
            comment.flagged_at = None
        elif action == 'hide':
            comment.status = 'hidden'
        elif action == 'delete':
            comment.soft_delete()
        
        comment.moderated_by = moderator
        comment.moderated_at = timezone.now()
        comment.moderation_reason = reason
        comment.save()
        
        # Log moderation action
        CommentModerationLog.objects.create(
            comment=comment,
            moderator=moderator,
            action=action,
            reason=reason,
            old_status=old_status,
            new_status=comment.status
        )
        
        moderated_count += 1
    
    return moderated_count