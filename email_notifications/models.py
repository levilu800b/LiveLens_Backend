# email_notifications/models.py
# type: ignore

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import EmailValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

User = get_user_model()

class NewsletterSubscription(models.Model):
    """
    Model for newsletter subscriptions from footer
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='newsletter_subscriptions',
        null=True, 
        blank=True,
        help_text="Linked user account if exists"
    )
    
    # Subscription settings
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    
    # Subscription preferences
    content_uploads = models.BooleanField(default=True, help_text="Notify about new content uploads")
    live_videos = models.BooleanField(default=True, help_text="Notify about live streams")
    weekly_digest = models.BooleanField(default=True, help_text="Weekly digest of content")
    monthly_newsletter = models.BooleanField(default=True, help_text="Monthly newsletter")
    
    # Timestamps
    subscribed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    subscription_source = models.CharField(
        max_length=50,
        choices=[
            ('footer', 'Footer Subscription'),
            ('popup', 'Popup Modal'),
            ('account_creation', 'Account Creation'),
            ('profile_settings', 'Profile Settings'),
        ],
        default='footer'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'newsletter_subscriptions'
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['is_verified', 'is_active']),
            models.Index(fields=['subscribed_at']),
        ]
        verbose_name = 'Newsletter Subscription'
        verbose_name_plural = 'Newsletter Subscriptions'
    
    def __str__(self):
        return f"{self.email} - {'Active' if self.is_active else 'Inactive'}"
    
    def unsubscribe(self):
        """Unsubscribe from newsletter"""
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()
    
    def verify_subscription(self):
        """Verify newsletter subscription"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save()


class EmailNotification(models.Model):
    """
    Model to track all email notifications sent
    """
    NOTIFICATION_TYPES = [
        ('welcome', 'Welcome Email'),
        ('password_changed', 'Password Changed'),
        ('newsletter_confirmation', 'Newsletter Confirmation'),
        ('content_upload', 'Content Upload Notification'),
        ('live_video', 'Live Video Notification'),
        ('weekly_digest', 'Weekly Digest'),
        ('monthly_newsletter', 'Monthly Newsletter'),
        ('password_reset', 'Password Reset'),
        ('account_verification', 'Account Verification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient information
    recipient_email = models.EmailField()
    recipient_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='email_notifications',
        null=True, 
        blank=True
    )
    
    # Email details
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Content reference (for content upload notifications)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    class Meta:
        db_table = 'email_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_email', 'notification_type']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]
        verbose_name = 'Email Notification'
        verbose_name_plural = 'Email Notifications'
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient_email} - {self.status}"
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message=""):
        """Mark notification as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save()
    
    def mark_as_opened(self):
        """Mark notification as opened"""
        self.status = 'opened'
        self.opened_at = timezone.now()
        self.save()
    
    def mark_as_clicked(self):
        """Mark notification as clicked"""
        self.status = 'clicked'
        self.clicked_at = timezone.now()
        self.save()


class EmailTemplate(models.Model):
    """
    Model for email templates
    """
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('password_changed', 'Password Changed'),
        ('newsletter_confirmation', 'Newsletter Confirmation'),
        ('content_upload', 'Content Upload Notification'),
        ('live_video', 'Live Video Notification'),
        ('weekly_digest', 'Weekly Digest'),
        ('monthly_newsletter', 'Monthly Newsletter'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    html_content = models.TextField(help_text="HTML email template")
    text_content = models.TextField(help_text="Plain text email template")
    
    # Template variables documentation
    variables = models.JSONField(
        default=dict,
        help_text="Available template variables and their descriptions"
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_email_templates'
    )
    
    class Meta:
        db_table = 'email_templates'
        ordering = ['-created_at']
        unique_together = ['template_type', 'is_default']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
    
    def __str__(self):
        return f"{self.name} - {self.template_type}"