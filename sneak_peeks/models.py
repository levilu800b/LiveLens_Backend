# sneak_peeks/models.py
# type: ignore

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation
from cloudinary.models import CloudinaryField
import uuid

User = get_user_model()

class SneakPeek(models.Model):
    """
    Model for sneak peek content - short teasers of upcoming content
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    CATEGORY_CHOICES = [
        ('upcoming_film', 'Upcoming Film'),
        ('upcoming_content', 'Upcoming Content'),
        ('upcoming_story', 'Upcoming Story'),
        ('upcoming_podcast', 'Upcoming Podcast'),
        ('upcoming_animation', 'Upcoming Animation'),
        ('behind_scenes', 'Behind the Scenes'),
        ('teaser', 'Teaser'),
        ('trailer', 'Trailer'),
        ('announcement', 'Announcement'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    short_description = models.TextField(
        max_length=300, 
        blank=True,
        help_text="Brief description for previews and social media"
    )
    
    # Author and categorization
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sneak_peeks'
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='teaser')
    tags = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Comma-separated tags (e.g., action, comedy, drama)"
    )
    
    # Media files
    video_file = CloudinaryField(
        'video', 
        resource_type='video',
        help_text="Main sneak peek video file"
    )
    thumbnail = CloudinaryField(
        'image', 
        blank=True, 
        null=True,
        help_text="Thumbnail image for the sneak peek"
    )
    poster = CloudinaryField(
        'image', 
        blank=True, 
        null=True,
        help_text="Poster image for displays"
    )
    
    # Video properties
    duration = models.PositiveIntegerField(
        default=0,
        help_text="Duration in seconds"
    )
    video_quality = models.CharField(
        max_length=10,
        choices=[
            ('480p', '480p'),
            ('720p', '720p'),
            ('1080p', '1080p'),
            ('4K', '4K'),
        ],
        default='1080p'
    )
    file_size = models.BigIntegerField(
        default=0,
        help_text="File size in bytes"
    )
    
    # Content information
    release_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Expected release date of the full content"
    )
    content_rating = models.CharField(
        max_length=10,
        choices=[
            ('G', 'General Audiences'),
            ('PG', 'Parental Guidance'),
            ('PG-13', 'Parents Strongly Cautioned'),
            ('R', 'Restricted'),
            ('NC-17', 'Adults Only'),
        ],
        default='PG',
        help_text="Content rating"
    )
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_premium = models.BooleanField(
        default=False,
        help_text="Requires premium subscription to view"
    )
    
    # Interaction tracking
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    dislike_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    # SEO and metadata
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Related content
    related_content_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of content this sneak peek is for (film, story, etc.)"
    )
    related_content_id = models.UUIDField(
        null=True, 
        blank=True,
        help_text="ID of the related content if it exists"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Generic relation for comments
    comments = GenericRelation('comments.Comment')
    
    class Meta:
        db_table = 'sneak_peeks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['is_trending', 'view_count']),
        ]
        verbose_name = 'Sneak Peek'
        verbose_name_plural = 'Sneak Peeks'
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            
            # Ensure unique slug
            original_slug = self.slug
            queryset = SneakPeek.objects.filter(slug=self.slug)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            
            counter = 1
            while queryset.exists():
                self.slug = f"{original_slug}-{counter}"
                queryset = SneakPeek.objects.filter(slug=self.slug)
                if self.pk:
                    queryset = queryset.exclude(pk=self.pk)
                counter += 1
        
        # Auto-publish if status changed to published
        if self.status == 'published' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def duration_formatted(self):
        """Return formatted duration string"""
        if not self.duration:
            return "0:00"
        
        minutes, seconds = divmod(self.duration, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    @property
    def file_size_formatted(self):
        """Return formatted file size"""
        if not self.file_size:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    def get_tags_list(self):
        """Return tags as a list"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def increment_view_count(self):
        """Increment view count"""
        SneakPeek.objects.filter(id=self.id).update(view_count=models.F('view_count') + 1)
    
    def get_related_sneak_peeks(self, limit=5):
        """Get related sneak peeks based on category and tags"""
        related = SneakPeek.objects.filter(
            category=self.category,
            status='published'
        ).exclude(id=self.id)
        
        if self.tags:
            # Simple tag matching - can be improved with more sophisticated algorithms
            tag_list = self.get_tags_list()
            for tag in tag_list:
                related = related.filter(tags__icontains=tag)
        
        return related.order_by('-view_count', '-created_at')[:limit]


class SneakPeekView(models.Model):
    """Track sneak peek views for analytics"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    sneak_peek = models.ForeignKey(
        SneakPeek, 
        on_delete=models.CASCADE, 
        related_name='views'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='sneak_peek_views'
    )
    
    # View metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
            ('tv', 'Smart TV'),
            ('other', 'Other'),
        ],
        default='other'
    )
    
    # View details
    watch_duration = models.PositiveIntegerField(
        default=0,
        help_text="How long the user watched in seconds"
    )
    completion_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Percentage of video watched"
    )
    
    # Referrer information
    referrer = models.URLField(blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sneak_peek_views'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['sneak_peek', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['ip_address', 'viewed_at']),
        ]
        verbose_name = 'Sneak Peek View'
        verbose_name_plural = 'Sneak Peek Views'
    
    def __str__(self):
        user_display = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_display} viewed {self.sneak_peek.title}"


class SneakPeekInteraction(models.Model):
    """Track user interactions with sneak peeks"""
    
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
        ('share', 'Share'),
        ('download', 'Download'),
        ('favorite', 'Favorite'),
        ('report', 'Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sneak_peek_interactions'
    )
    sneak_peek = models.ForeignKey(
        SneakPeek, 
        on_delete=models.CASCADE, 
        related_name='interactions'
    )
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    
    # Additional data for specific interactions
    share_platform = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Platform where content was shared"
    )
    rating = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1-5 stars"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sneak_peek_interactions'
        unique_together = ['user', 'sneak_peek', 'interaction_type']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sneak_peek', 'interaction_type']),
            models.Index(fields=['user', 'interaction_type']),
        ]
        verbose_name = 'Sneak Peek Interaction'
        verbose_name_plural = 'Sneak Peek Interactions'
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type}d {self.sneak_peek.title}"


class SneakPeekPlaylist(models.Model):
    """User-created playlists of sneak peeks"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sneak_peek_playlists'
    )
    
    sneak_peeks = models.ManyToManyField(
        SneakPeek, 
        through='SneakPeekPlaylistItem',
        related_name='playlists'
    )
    
    is_public = models.BooleanField(default=False)
    is_auto_play = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sneak_peek_playlists'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['creator', 'is_public']),
            models.Index(fields=['is_public', 'updated_at']),
        ]
        verbose_name = 'Sneak Peek Playlist'
        verbose_name_plural = 'Sneak Peek Playlists'
    
    def __str__(self):
        return f"{self.name} by {self.creator.username}"
    
    @property
    def sneak_peek_count(self):
        return self.sneak_peeks.count()
    
    @property
    def total_duration(self):
        return self.sneak_peeks.aggregate(
            total=models.Sum('duration')
        )['total'] or 0


class SneakPeekPlaylistItem(models.Model):
    """Through model for sneak peek playlist items with ordering"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    playlist = models.ForeignKey(SneakPeekPlaylist, on_delete=models.CASCADE)
    sneak_peek = models.ForeignKey(SneakPeek, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sneak_peek_playlist_items'
        unique_together = ['playlist', 'sneak_peek']
        ordering = ['order', 'added_at']
        indexes = [
            models.Index(fields=['playlist', 'order']),
        ]
        verbose_name = 'Sneak Peek Playlist Item'
        verbose_name_plural = 'Sneak Peek Playlist Items'
    
    def __str__(self):
        return f"{self.sneak_peek.title} in {self.playlist.name}"