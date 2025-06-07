# comments/models.py
# type: ignore

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils import timezone
import uuid

User = get_user_model()

class Comment(models.Model):
    """
    Universal comment model that can be attached to any content type
    (Stories, Films, Content, Podcasts, Animations, Sneak Peeks)
    """
    
    COMMENT_STATUS_CHOICES = [
        ('published', 'Published'),
        ('pending', 'Pending Moderation'),
        ('hidden', 'Hidden'),
        ('deleted', 'Deleted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User who made the comment
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    
    # Generic relationship to any content model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Comment content
    text = models.TextField(
        validators=[
            MinLengthValidator(1, "Comment cannot be empty"),
            MaxLengthValidator(1000, "Comment cannot exceed 1000 characters")
        ],
        help_text="Maximum 1000 characters"
    )
    
    # Parent comment for threading/replies
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name='replies'
    )
    
    # Comment status and moderation
    status = models.CharField(
        max_length=20, 
        choices=COMMENT_STATUS_CHOICES, 
        default='published'
    )
    
    # Interaction tracking
    like_count = models.PositiveIntegerField(default=0)
    dislike_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Moderation fields
    is_flagged = models.BooleanField(default=False)
    flagged_by = models.ManyToManyField(
        User, 
        related_name='flagged_comments', 
        blank=True
    )
    flagged_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='moderated_comments'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderation_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['parent']),
        ]
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
    
    def __str__(self):
        content_name = str(self.content_object) if self.content_object else "Unknown Content"
        return f"Comment by {self.user.username} on {content_name}"
    
    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent is not None
    
    @property
    def thread_level(self):
        """Get the nesting level of this comment"""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level
    
    def get_replies(self):
        """Get all direct replies to this comment"""
        return self.replies.filter(status='published').order_by('created_at')
    
    def get_all_replies(self):
        """Get all nested replies to this comment"""
        replies = []
        for reply in self.get_replies():
            replies.append(reply)
            replies.extend(reply.get_all_replies())
        return replies
    
    def soft_delete(self):
        """Soft delete the comment"""
        self.status = 'deleted'
        self.text = "[Comment deleted]"
        self.save()
    
    def mark_as_edited(self):
        """Mark comment as edited"""
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save()


class CommentInteraction(models.Model):
    """
    Track user interactions with comments (likes, dislikes, reports)
    """
    
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('report', 'Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comment_interactions'
    )
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.CASCADE, 
        related_name='interactions'
    )
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    
    # Report specific fields
    report_reason = models.CharField(max_length=100, blank=True)
    report_description = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_interactions'
        unique_together = ['user', 'comment', 'interaction_type']
        indexes = [
            models.Index(fields=['comment', 'interaction_type']),
            models.Index(fields=['user', 'interaction_type']),
        ]
        verbose_name = 'Comment Interaction'
        verbose_name_plural = 'Comment Interactions'
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type}d comment by {self.comment.user.username}"


class CommentModerationLog(models.Model):
    """
    Log all moderation actions on comments
    """
    
    MODERATION_ACTIONS = [
        ('approve', 'Approved'),
        ('hide', 'Hidden'),
        ('delete', 'Deleted'),
        ('flag', 'Flagged'),
        ('unflag', 'Unflagged'),
        ('edit', 'Edited'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.CASCADE, 
        related_name='moderation_logs'
    )
    moderator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='moderation_actions'
    )
    
    action = models.CharField(max_length=20, choices=MODERATION_ACTIONS)
    reason = models.TextField(blank=True)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_moderation_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['comment', 'created_at']),
            models.Index(fields=['moderator', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
        verbose_name = 'Comment Moderation Log'
        verbose_name_plural = 'Comment Moderation Logs'
    
    def __str__(self):
        return f"{self.moderator.username} {self.action} comment by {self.comment.user.username}"


class CommentNotification(models.Model):
    """
    Notifications for comment-related activities
    """
    
    NOTIFICATION_TYPES = [
        ('reply', 'Reply to Comment'),
        ('like', 'Comment Liked'),
        ('mention', 'Mentioned in Comment'),
        ('moderation', 'Comment Moderated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comment_notifications'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_comment_notifications'
    )
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['comment', 'notification_type']),
        ]
        verbose_name = 'Comment Notification'
        verbose_name_plural = 'Comment Notifications'
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.notification_type}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()