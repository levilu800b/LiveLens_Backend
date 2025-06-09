# analytics/models.py
# type: ignore

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from authapp.models import User
from django.utils import timezone
import uuid
import json

class ContentView(models.Model):
    """
    Track individual content views with detailed analytics
    """
    
    DEVICE_TYPES = [
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('tv', 'Smart TV'),
        ('unknown', 'Unknown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User information (can be null for anonymous views)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='content_views')
    session_id = models.CharField(max_length=40, blank=True)  # For anonymous tracking
    
    # Content reference
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # View details
    view_duration = models.FloatField(default=0.0, help_text='Duration in seconds')
    completion_percentage = models.FloatField(default=0.0, help_text='Percentage of content consumed')
    is_unique_view = models.BooleanField(default=True)
    
    # Device and location information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='unknown')
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    screen_resolution = models.CharField(max_length=20, blank=True)
    
    # Geographic data
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, blank=True)
    
    # Referrer information
    referrer = models.URLField(blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    
    # Quality metrics
    video_quality = models.CharField(max_length=10, blank=True)  # 480p, 720p, 1080p, etc.
    audio_quality = models.CharField(max_length=10, blank=True)
    buffering_events = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    likes_during_view = models.PositiveIntegerField(default=0)
    comments_during_view = models.PositiveIntegerField(default=0)
    shares_during_view = models.PositiveIntegerField(default=0)
    pauses_count = models.PositiveIntegerField(default=0)
    seeks_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'content_views'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['content_type', 'object_id', 'started_at']),
            models.Index(fields=['is_unique_view', 'started_at']),
            models.Index(fields=['country', 'started_at']),
            models.Index(fields=['device_type', 'started_at']),
        ]
    
    def __str__(self):
        return f"View of {self.content_object} by {self.user or 'Anonymous'} at {self.started_at}"
    
    @property
    def duration_display(self):
        """Human readable duration"""
        if self.view_duration < 60:
            return f"{self.view_duration:.0f}s"
        elif self.view_duration < 3600:
            return f"{self.view_duration/60:.1f}m"
        else:
            return f"{self.view_duration/3600:.1f}h"

class UserEngagement(models.Model):
    """
    Track user engagement patterns and behavior
    """
    
    ENGAGEMENT_TYPES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('download', 'Download'),
        ('bookmark', 'Bookmark'),
        ('report', 'Report'),
        ('subscribe', 'Subscribe'),
        ('rating', 'Rating'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagements')
    
    # Content reference
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    engagement_type = models.CharField(max_length=20, choices=ENGAGEMENT_TYPES)
    engagement_value = models.FloatField(null=True, blank=True)  # For ratings, duration, etc.
    engagement_data = models.JSONField(default=dict, blank=True)  # Additional metadata
    
    # Context
    session_id = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_engagements'
        unique_together = ['user', 'content_type', 'object_id', 'engagement_type']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'engagement_type', 'created_at']),
            models.Index(fields=['content_type', 'object_id', 'engagement_type']),
            models.Index(fields=['engagement_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} {self.engagement_type} {self.content_object}"

class ContentPerformanceMetrics(models.Model):
    """
    Aggregated performance metrics for content
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Content reference
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Time period
    date = models.DateField()
    hour = models.PositiveIntegerField(null=True, blank=True)  # For hourly metrics
    
    # View metrics
    total_views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    returning_views = models.PositiveIntegerField(default=0)
    
    # Engagement metrics
    total_likes = models.PositiveIntegerField(default=0)
    total_dislikes = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    total_downloads = models.PositiveIntegerField(default=0)
    
    # Quality metrics
    average_view_duration = models.FloatField(default=0.0)
    average_completion_rate = models.FloatField(default=0.0)
    bounce_rate = models.FloatField(default=0.0)  # Percentage who left quickly
    
    # Technical metrics
    average_buffering_events = models.FloatField(default=0.0)
    most_popular_quality = models.CharField(max_length=10, blank=True)
    
    # Geographic distribution
    top_countries = models.JSONField(default=list, blank=True)
    top_cities = models.JSONField(default=list, blank=True)
    
    # Device distribution
    device_breakdown = models.JSONField(default=dict, blank=True)
    browser_breakdown = models.JSONField(default=dict, blank=True)
    
    # Traffic sources
    referrer_breakdown = models.JSONField(default=dict, blank=True)
    utm_sources = models.JSONField(default=dict, blank=True)
    
    # Performance score (calculated)
    performance_score = models.FloatField(default=0.0)
    trending_score = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'content_performance_metrics'
        unique_together = ['content_type', 'object_id', 'date', 'hour']
        ordering = ['-date', '-hour']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'date']),
            models.Index(fields=['date', 'performance_score']),
            models.Index(fields=['trending_score', 'date']),
        ]
    
    def __str__(self):
        period = f"{self.date}"
        if self.hour is not None:
            period += f" {self.hour}:00"
        return f"Metrics for {self.content_object} - {period}"

class UserBehaviorPattern(models.Model):
    """
    Track user behavior patterns for personalization
    """
    
    BEHAVIOR_TYPES = [
        ('viewing_time', 'Preferred Viewing Time'),
        ('content_preference', 'Content Type Preference'),
        ('genre_preference', 'Genre Preference'),
        ('device_preference', 'Device Preference'),
        ('session_duration', 'Average Session Duration'),
        ('engagement_level', 'Engagement Level'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behavior_patterns')
    
    behavior_type = models.CharField(max_length=30, choices=BEHAVIOR_TYPES)
    pattern_data = models.JSONField(default=dict)
    confidence_score = models.FloatField(default=0.0)  # How confident we are in this pattern
    
    # Time period this pattern represents
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_behavior_patterns'
        unique_together = ['user', 'behavior_type', 'period_start']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'behavior_type']),
            models.Index(fields=['confidence_score', 'updated_at']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_behavior_type_display()}"


