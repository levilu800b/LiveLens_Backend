# ===================================================================
# ADMIN DASHBOARD APP - COMPLETE IMPLEMENTATION
# ===================================================================

# admin_dashboard/models.py
# type: ignore

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
import json

User = get_user_model()

class AdminActivity(models.Model):
    """Track admin activities for audit purposes"""
    ACTIVITY_TYPES = [
        ('create_content', 'Create Content'),
        ('update_content', 'Update Content'),
        ('delete_content', 'Delete Content'),
        ('manage_user', 'Manage User'),
        ('delete_comment', 'Delete Comment'),
        ('feature_content', 'Feature Content'),
        ('ban_user', 'Ban User'),
        ('unban_user', 'Unban User'),
        ('make_admin', 'Make Admin'),
        ('remove_admin', 'Remove Admin'),
        ('bulk_action', 'Bulk Action'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    # Generic foreign key to track what was affected
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    metadata = models.JSONField(default=dict, blank=True)  # Store additional data
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.admin.username} - {self.activity_type} - {self.timestamp}"


class PlatformStatistics(models.Model):
    """Store aggregated platform statistics for performance"""
    date = models.DateField(unique=True)
    
    # User Statistics
    total_users = models.PositiveIntegerField(default=0)
    new_users_today = models.PositiveIntegerField(default=0)
    active_users_today = models.PositiveIntegerField(default=0)
    verified_users = models.PositiveIntegerField(default=0)
    
    # Content Statistics
    total_stories = models.PositiveIntegerField(default=0)
    total_films = models.PositiveIntegerField(default=0)
    total_content = models.PositiveIntegerField(default=0)
    total_podcasts = models.PositiveIntegerField(default=0)
    total_animations = models.PositiveIntegerField(default=0)
    total_sneak_peeks = models.PositiveIntegerField(default=0)
    total_live_videos = models.PositiveIntegerField(default=0)
    
    # Engagement Statistics
    total_comments = models.PositiveIntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)
    total_reading_time = models.PositiveIntegerField(default=0)  # in minutes
    
    # Performance Statistics
    avg_session_duration = models.FloatField(default=0.0)  # in minutes
    bounce_rate = models.FloatField(default=0.0)  # percentage
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"Platform Stats - {self.date}"


class ContentModerationQueue(models.Model):
    """Queue for content that needs moderation"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
    ]
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_content')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_content')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(default=1)  # 1=low, 5=high
    reason = models.TextField(blank=True)  # Reason for rejection/flagging
    review_notes = models.TextField(blank=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-submitted_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f"Moderation: {self.content_type.name} - {self.status}"