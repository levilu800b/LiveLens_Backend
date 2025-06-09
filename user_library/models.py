# user_library/models.py
# type: ignore

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from authapp.models import User
import uuid

class UserLibrary(models.Model):
    """
    User's personal library tracking watched/read content
    """
    
    INTERACTION_TYPES = [
        ('viewed', 'Viewed'),
        ('read', 'Read'),
        ('listened', 'Listened'),
        ('downloaded', 'Downloaded'),
        ('shared', 'Shared'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_items')
    
    # Generic relation to any content type
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Interaction details
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Progress tracking
    progress_percentage = models.FloatField(default=0.0)  # 0-100
    current_position = models.FloatField(default=0.0)  # Current time/page position
    total_duration = models.FloatField(default=0.0)  # Total content duration
    
    # Engagement metrics
    time_spent = models.FloatField(default=0.0)  # Total time spent in seconds
    view_count = models.PositiveIntegerField(default=1)
    last_accessed = models.DateTimeField(auto_now=True)
    
    # User experience
    rating = models.PositiveIntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_library'
        unique_together = ['user', 'content_type', 'object_id', 'interaction_type']
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['user', 'status', 'last_accessed']),
            models.Index(fields=['user', 'interaction_type', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_interaction_type_display()} - {self.content_object}"
    
    @property
    def is_completed(self):
        return self.status == 'completed' or self.progress_percentage >= 95.0
    
    def update_progress(self, current_position, total_duration=None):
        """Update viewing/reading progress"""
        self.current_position = current_position
        if total_duration:
            self.total_duration = total_duration
        
        if self.total_duration > 0:
            self.progress_percentage = min((current_position / self.total_duration) * 100, 100)
            
            # Auto-mark as completed if near the end
            if self.progress_percentage >= 95.0:
                self.status = 'completed'
            elif self.progress_percentage > 0:
                self.status = 'in_progress'
        
        self.save()

class UserFavorites(models.Model):
    """
    User's favorite content items
    """
    
    FAVORITE_TYPES = [
        ('like', 'Like'),
        ('love', 'Love'),
        ('bookmark', 'Bookmark'),
        ('watchlist', 'Watch Later'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    
    # Generic relation to any content type
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    favorite_type = models.CharField(max_length=20, choices=FAVORITE_TYPES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_favorites'
        unique_together = ['user', 'content_type', 'object_id', 'favorite_type']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'favorite_type', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_favorite_type_display()} - {self.content_object}"

class UserPlaylist(models.Model):
    """
    User-created playlists
    """
    
    PRIVACY_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
        ('shared', 'Shared with Friends'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='private')
    
    # Cover image
    cover_image = models.ImageField(upload_to='playlists/covers/', blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_playlists'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'privacy', 'updated_at']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.name}"
    
    @property
    def item_count(self):
        return self.items.count()

class UserPlaylistItem(models.Model):
    """
    Items in user playlists
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playlist = models.ForeignKey(UserPlaylist, on_delete=models.CASCADE, related_name='items')
    
    # Generic relation to any content type
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_playlist_items'
        unique_together = ['playlist', 'content_type', 'object_id']
        ordering = ['order', 'added_at']
        indexes = [
            models.Index(fields=['playlist', 'order']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.playlist.name} - {self.content_object}"

class UserContentRecommendation(models.Model):
    """
    AI-generated content recommendations for users
    """
    
    RECOMMENDATION_TYPES = [
        ('trending', 'Trending'),
        ('similar', 'Similar Content'),
        ('genre_based', 'Based on Genre Preferences'),
        ('collaborative', 'Users Like You Also Enjoyed'),
        ('new_content', 'New Content'),
        ('ai_curated', 'AI Curated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    
    # Generic relation to recommended content
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    reason = models.TextField(blank=True)  # Why this was recommended
    
    # Engagement tracking
    shown_count = models.PositiveIntegerField(default=0)
    clicked = models.BooleanField(default=False)
    dismissed = models.BooleanField(default=False)
    
    # Validity
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_recommendations'
        unique_together = ['user', 'content_type', 'object_id', 'recommendation_type']
        ordering = ['-confidence_score', '-created_at']
        indexes = [
            models.Index(fields=['user', 'expires_at', 'dismissed']),
            models.Index(fields=['recommendation_type', 'confidence_score']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_recommendation_type_display()} - {self.content_object}"

class UserSearchHistory(models.Model):
    """
    Track user search history for better recommendations
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    
    query = models.CharField(max_length=500)
    filters_applied = models.JSONField(default=dict, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    clicked_result = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_search_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['query', 'clicked_result']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.query}"