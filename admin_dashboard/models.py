# admin_dashboard/models.py
# type: ignore

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()

class DashboardStats(models.Model):
    """
    Model to store pre-calculated dashboard statistics for performance
    """
    
    STAT_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('total', 'Total'),
    ]
    
    METRIC_TYPES = [
        ('users', 'Total Users'),
        ('active_users', 'Active Users'),
        ('new_users', 'New Users'),
        ('stories', 'Total Stories'),
        ('films', 'Total Films'),
        ('content', 'Total Content'),
        ('podcasts', 'Total Podcasts'),
        ('animations', 'Total Animations'),
        ('sneak_peeks', 'Total Sneak Peeks'),
        ('comments', 'Total Comments'),
        ('views', 'Total Views'),
        ('likes', 'Total Likes'),
        ('shares', 'Total Shares'),
        ('downloads', 'Total Downloads'),
        ('revenue', 'Revenue'),
        ('subscriptions', 'Subscriptions'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    stat_type = models.CharField(max_length=20, choices=STAT_TYPES)
    value = models.BigIntegerField(default=0)
    percentage_change = models.FloatField(default=0.0)
    
    # Time period
    date = models.DateField()
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_stats'
        unique_together = ['metric_type', 'stat_type', 'date']
        ordering = ['-date', 'metric_type']
        indexes = [
            models.Index(fields=['metric_type', 'stat_type', 'date']),
            models.Index(fields=['date', 'metric_type']),
        ]
        verbose_name = 'Dashboard Statistic'
        verbose_name_plural = 'Dashboard Statistics'
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.get_stat_type_display()} - {self.date}"


class ContentAnalytics(models.Model):
    """
    Model to track detailed analytics for content pieces
    """
    
    CONTENT_TYPES = [
        ('story', 'Story'),
        ('film', 'Film'),
        ('content', 'Content'),
        ('podcast', 'Podcast'),
        ('animation', 'Animation'),
        ('sneak_peek', 'Sneak Peek'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Content reference
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.UUIDField()
    content_title = models.CharField(max_length=200)
    
    # Analytics data
    views_count = models.PositiveIntegerField(default=0)
    unique_views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    downloads_count = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    average_watch_time = models.FloatField(default=0.0)  # in seconds
    completion_rate = models.FloatField(default=0.0)  # percentage
    bounce_rate = models.FloatField(default=0.0)  # percentage
    return_viewer_rate = models.FloatField(default=0.0)  # percentage
    
    # Geographic and demographic data
    top_countries = models.JSONField(default=list, blank=True)
    age_demographics = models.JSONField(default=dict, blank=True)
    device_breakdown = models.JSONField(default=dict, blank=True)
    traffic_sources = models.JSONField(default=dict, blank=True)
    
    # Time-based data
    hourly_views = models.JSONField(default=list, blank=True)
    daily_views = models.JSONField(default=list, blank=True)
    weekly_views = models.JSONField(default=list, blank=True)
    
    # Performance score (calculated)
    performance_score = models.FloatField(default=0.0)
    trending_score = models.FloatField(default=0.0)
    
    # Date tracking
    date = models.DateField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'content_analytics'
        unique_together = ['content_type', 'content_id', 'date']
        ordering = ['-date', '-views_count']
        indexes = [
            models.Index(fields=['content_type', 'date']),
            models.Index(fields=['performance_score', 'date']),
            models.Index(fields=['trending_score', 'date']),
        ]
        verbose_name = 'Content Analytics'
        verbose_name_plural = 'Content Analytics'
    
    def __str__(self):
        return f"{self.content_title} - {self.date}"
    
    def calculate_performance_score(self):
        """Calculate performance score based on various metrics"""
        # Weighted scoring algorithm
        view_score = min(self.views_count / 1000, 10) * 0.3
        engagement_score = (
            (self.likes_count / max(self.views_count, 1)) * 10 * 0.25 +
            (self.comments_count / max(self.views_count, 1)) * 10 * 0.2 +
            (self.completion_rate / 100) * 10 * 0.15
        )
        interaction_score = (
            (self.shares_count / max(self.views_count, 1)) * 10 * 0.1
        )
        
        self.performance_score = min(view_score + engagement_score + interaction_score, 10)
        return self.performance_score


class UserActivity(models.Model):
    """
    Model to track user activities across the platform
    """
    
    ACTIVITY_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('signup', 'User Signup'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        ('content_view', 'Content View'),
        ('content_like', 'Content Like'),
        ('content_dislike', 'Content Dislike'),
        ('content_share', 'Content Share'),
        ('content_download', 'Content Download'),
        ('comment_post', 'Comment Posted'),
        ('comment_like', 'Comment Liked'),
        ('comment_reply', 'Comment Reply'),
        ('playlist_create', 'Playlist Created'),
        ('playlist_update', 'Playlist Updated'),
        ('search', 'Search Performed'),
        ('filter_use', 'Filter Used'),
        ('subscription_start', 'Subscription Started'),
        ('subscription_cancel', 'Subscription Cancelled'),
        ('payment', 'Payment Made'),
        ('error', 'Error Occurred'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='admin_activities',
        null=True, 
        blank=True  # For anonymous users
    )
    
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    
    # Related object (generic foreign key)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    device_type = models.CharField(max_length=20, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    
    # Location data (if available)
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type', 'created_at']),
            models.Index(fields=['activity_type', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
    
    def __str__(self):
        user_display = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_display} - {self.get_activity_type_display()}"


class SystemAlert(models.Model):
    """
    Model for system alerts and notifications for admins
    """
    
    ALERT_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
        ('success', 'Success'),
    ]
    
    ALERT_CATEGORIES = [
        ('system', 'System'),
        ('security', 'Security'),
        ('performance', 'Performance'),
        ('content', 'Content'),
        ('user', 'User'),
        ('payment', 'Payment'),
        ('moderation', 'Moderation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    category = models.CharField(max_length=20, choices=ALERT_CATEGORIES)
    
    # Related object (optional)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Alert status
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Priority and escalation
    priority = models.IntegerField(
        default=1,
        choices=[(i, f"Priority {i}") for i in range(1, 6)]
    )
    requires_action = models.BooleanField(default=False)
    auto_dismiss_after = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Auto-dismiss after X hours"
    )
    
    # Notification settings
    email_sent = models.BooleanField(default=False)
    slack_sent = models.BooleanField(default=False)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'is_resolved', 'created_at']),
            models.Index(fields=['category', 'priority', 'created_at']),
            models.Index(fields=['is_read', 'requires_action']),
        ]
        verbose_name = 'System Alert'
        verbose_name_plural = 'System Alerts'
    
    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.title}"
    
    def mark_as_read(self):
        """Mark alert as read"""
        self.is_read = True
        self.save()
    
    def resolve(self, user, notes=''):
        """Resolve the alert"""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()
    
    def should_auto_dismiss(self):
        """Check if alert should be auto-dismissed"""
        if not self.auto_dismiss_after:
            return False
        
        dismiss_time = self.created_at + timedelta(hours=self.auto_dismiss_after)
        return timezone.now() > dismiss_time


class ReportGeneration(models.Model):
    """
    Model to track generated reports for download
    """
    
    REPORT_TYPES = [
        ('user_analytics', 'User Analytics'),
        ('content_performance', 'Content Performance'),
        ('revenue_report', 'Revenue Report'),
        ('engagement_report', 'Engagement Report'),
        ('traffic_report', 'Traffic Report'),
        ('moderation_report', 'Moderation Report'),
        ('system_health', 'System Health'),
        ('custom', 'Custom Report'),
    ]
    
    REPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    report_format = models.CharField(max_length=10, choices=REPORT_FORMATS)
    
    # Date range
    date_from = models.DateField()
    date_to = models.DateField()
    
    # Generation details
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='requested_reports'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # File details
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    
    # Processing details
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    error_message = models.TextField(blank=True)
    
    # Report parameters
    filters = models.JSONField(default=dict, blank=True)
    include_fields = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()  # Auto-delete after expiration
    
    class Meta:
        db_table = 'report_generations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['requested_by', 'status', 'created_at']),
            models.Index(fields=['report_type', 'created_at']),
            models.Index(fields=['expires_at']),
        ]
        verbose_name = 'Report Generation'
        verbose_name_plural = 'Report Generations'
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    def is_expired(self):
        """Check if report has expired"""
        return timezone.now() > self.expires_at
    
    def increment_download_count(self):
        """Increment download count"""
        ReportGeneration.objects.filter(id=self.id).update(
            download_count=models.F('download_count') + 1
        )