# notifications/models.py
# type: ignore

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from authapp.models import User
from django.utils import timezone
import uuid

class Notification(models.Model):
    """
    Universal notification model for all types of notifications
    """
    
    NOTIFICATION_TYPES = [
        ('content_like', 'Content Liked'),
        ('content_comment', 'Content Commented'),
        ('content_share', 'Content Shared'),
        ('new_content', 'New Content Available'),
        ('new_follower', 'New Follower'),
        ('mention', 'User Mentioned'),
        ('system_alert', 'System Alert'),
        ('admin_message', 'Admin Message'),
        ('content_published', 'Content Published'),
        ('comment_reply', 'Comment Reply'),
        ('milestone_reached', 'Milestone Reached'),
        ('recommendation', 'Content Recommendation'),
        ('live_event', 'Live Event'),
        ('update_available', 'Update Available'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    DELIVERY_METHODS = [
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('sms', 'SMS'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Sender (optional - can be system notifications)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', 
                              null=True, blank=True)
    
    # Notification details
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    
    # Related object (optional)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Delivery settings
    delivery_methods = models.JSONField(default=list, blank=True)  # ['in_app', 'email', 'push']
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    
    # Timing
    scheduled_for = models.DateTimeField(null=True, blank=True)  # For scheduled notifications
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    action_url = models.URLField(blank=True)  # URL to redirect when clicked
    action_data = models.JSONField(default=dict, blank=True)  # Additional action data
    metadata = models.JSONField(default=dict, blank=True)  # Additional metadata
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'is_delivered']),
            models.Index(fields=['scheduled_for', 'is_delivered']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.recipient.full_name}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_clicked(self):
        """Mark notification as clicked"""
        if not self.is_clicked:
            self.is_clicked = True
            self.clicked_at = timezone.now()
            self.save(update_fields=['is_clicked', 'clicked_at'])
        
        # Also mark as read if not already
        if not self.is_read:
            self.mark_as_read()
    
    def mark_as_delivered(self):
        """Mark notification as delivered"""
        if not self.is_delivered:
            self.is_delivered = True
            self.delivered_at = timezone.now()
            self.save(update_fields=['is_delivered', 'delivered_at'])
    
    @property
    def is_expired(self):
        """Check if notification is expired"""
        return self.expires_at and timezone.now() > self.expires_at

class NotificationSettings(models.Model):
    """
    User notification preferences
    """
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    
    # General settings
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    in_app_notifications = models.BooleanField(default=True)
    
    # Specific notification type preferences
    content_likes = models.BooleanField(default=True)
    content_comments = models.BooleanField(default=True)
    content_shares = models.BooleanField(default=True)
    new_content = models.BooleanField(default=True)
    new_followers = models.BooleanField(default=True)
    mentions = models.BooleanField(default=True)
    system_alerts = models.BooleanField(default=True)
    admin_messages = models.BooleanField(default=True)
    recommendations = models.BooleanField(default=True)
    
    # Frequency settings
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest'),
            ('never', 'Never'),
        ],
        default='immediate'
    )
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)  # e.g., 22:00
    quiet_hours_end = models.TimeField(null=True, blank=True)    # e.g., 08:00
    
    # Advanced settings
    marketing_notifications = models.BooleanField(default=False)
    digest_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_settings'
    
    def __str__(self):
        return f"Notification settings for {self.user.full_name}"

class NotificationTemplate(models.Model):
    """
    Templates for different types of notifications
    """
    
    notification_type = models.CharField(max_length=30, unique=True)
    
    # Template content
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    email_subject_template = models.CharField(max_length=200, blank=True)
    email_body_template = models.TextField(blank=True)
    push_title_template = models.CharField(max_length=100, blank=True)
    push_body_template = models.CharField(max_length=200, blank=True)
    
    # Default settings
    default_priority = models.CharField(max_length=10, default='normal')
    default_delivery_methods = models.JSONField(default=list, blank=True)
    default_expires_hours = models.PositiveIntegerField(default=168)  # 7 days
    
    # Template variables documentation
    available_variables = models.JSONField(default=list, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
    
    def __str__(self):
        return f"Template for {self.notification_type}"

class NotificationQueue(models.Model):
    """
    Queue for processing notifications
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('retry', 'Retry'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='queue_items')
    
    delivery_method = models.CharField(max_length=10)  # email, push, sms
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Retry logic
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Processing details
    error_message = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_queue'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['delivery_method', 'status']),
            models.Index(fields=['next_retry_at']),
        ]
    
    def __str__(self):
        return f"Queue item for {self.notification.title} via {self.delivery_method}"


