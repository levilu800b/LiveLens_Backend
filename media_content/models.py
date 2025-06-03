#type: ignore

# media_content/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


User = get_user_model()

class BaseMediaContent(models.Model):
    """Abstract base model for all media content"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('processing', 'Processing'),
    ]
    
    QUALITY_CHOICES = [
        ('360p', '360p'),
        ('480p', '480p'),
        ('720p', '720p HD'),
        ('1080p', '1080p Full HD'),
        ('1440p', '1440p QHD'),
        ('2160p', '4K UHD'),
    ]
    
    CATEGORY_CHOICES = [
        ('action', 'Action'),
        ('adventure', 'Adventure'),
        ('comedy', 'Comedy'),
        ('drama', 'Drama'),
        ('horror', 'Horror'),
        ('romance', 'Romance'),
        ('sci_fi', 'Science Fiction'),
        ('fantasy', 'Fantasy'),
        ('thriller', 'Thriller'),
        ('documentary', 'Documentary'),
        ('animation', 'Animation'),
        ('mystery', 'Mystery'),
        ('crime', 'Crime'),
        ('biography', 'Biography'),
        ('history', 'History'),
        ('music', 'Music'),
        ('sport', 'Sport'),
        ('family', 'Family'),
        ('educational', 'Educational'),
        ('tech', 'Technology'),
        ('lifestyle', 'Lifestyle'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(max_length=1000, help_text="Detailed description of the content")
    short_description = models.CharField(max_length=300, blank=True, help_text="Brief description for cards")
    
    # Categorization
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for the content")
    
    # Media Files
    thumbnail = models.ImageField(upload_to='media/thumbnails/', blank=True, null=True)
    poster = models.ImageField(upload_to='media/posters/', blank=True, null=True)
    banner = models.ImageField(upload_to='media/banners/', blank=True, null=True, help_text="Large banner image")
    
    # Video Files
    video_file = models.FileField(upload_to='media/videos/', blank=True, null=True, help_text="Main video file")
    trailer_file = models.FileField(upload_to='media/trailers/', blank=True, null=True, help_text="Trailer video file")
    
    # Video Metadata
    duration = models.PositiveIntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        help_text="Duration in seconds"
    )
    trailer_duration = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)], 
        help_text="Trailer duration in seconds"
    )
    video_quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='1080p')
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    
    # Content Metadata
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_authored')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False, help_text="Requires premium subscription")
    
    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    
    # Ratings
    average_rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    rating_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    # Additional Metadata
    release_year = models.PositiveIntegerField(blank=True, null=True)
    language = models.CharField(max_length=50, default='English')
    subtitles_available = models.JSONField(default=list, blank=True, help_text="List of available subtitle languages")
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['is_featured', '-created_at']),
            models.Index(fields=['is_trending', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            self.slug = slugify(self.title)
            
            # Ensure slug uniqueness
            counter = 1
            original_slug = self.slug
            model_class = self.__class__
            while model_class.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-generate short description if not provided
        if not self.short_description and self.description:
            self.short_description = self.description[:250] + ('...' if len(self.description) > 250 else '')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def is_published(self):
        return self.status == 'published'
    
    @property
    def duration_formatted(self):
        """Return duration in HH:MM:SS format"""
        if not self.duration:
            return "00:00:00"
        
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @property
    def trailer_duration_formatted(self):
        """Return trailer duration in MM:SS format"""
        if not self.trailer_duration:
            return "00:00"
        
        minutes, seconds = divmod(self.trailer_duration, 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def file_size_formatted(self):
        """Return file size in human readable format"""
        if not self.file_size:
            return "0 B"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def increment_view_count(self):
        """Increment view count atomically"""
        self.__class__.objects.filter(id=self.id).update(view_count=models.F('view_count') + 1)
        self.refresh_from_db(fields=['view_count'])

class Film(BaseMediaContent):
    """Model for Films - Full length movies"""
    
    # Film-specific fields
    director = models.CharField(max_length=200, blank=True, help_text="Film director(s)")
    cast = models.JSONField(default=list, blank=True, help_text="List of main cast members")
    producer = models.CharField(max_length=200, blank=True, help_text="Film producer(s)")
    studio = models.CharField(max_length=100, blank=True, help_text="Production studio")
    budget = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Production budget")
    box_office = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Box office earnings")
    
    # Film ratings
    mpaa_rating = models.CharField(
        max_length=10,
        choices=[
            ('G', 'G - General Audiences'),
            ('PG', 'PG - Parental Guidance'),
            ('PG-13', 'PG-13 - Parents Strongly Cautioned'),
            ('R', 'R - Restricted'),
            ('NC-17', 'NC-17 - Adults Only'),
            ('NR', 'Not Rated'),
        ],
        default='NR'
    )
    
    # Film series information
    is_series = models.BooleanField(default=False)
    series_name = models.CharField(max_length=200, blank=True)
    episode_number = models.PositiveIntegerField(blank=True, null=True)
    season_number = models.PositiveIntegerField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Film'
        verbose_name_plural = 'Films'
        ordering = ['-created_at']
    
    def get_absolute_url(self):
        return reverse('media_content:film-detail', kwargs={'slug': self.slug})

class Content(BaseMediaContent):
    """Model for General Content - Various video content types"""
    
    CONTENT_TYPE_CHOICES = [
        ('tutorial', 'Tutorial'),
        ('review', 'Review'),
        ('vlog', 'Vlog'),
        ('interview', 'Interview'),
        ('presentation', 'Presentation'),
        ('webinar', 'Webinar'),
        ('course', 'Course'),
        ('entertainment', 'Entertainment'),
        ('news', 'News'),
        ('sports', 'Sports'),
        ('music_video', 'Music Video'),
        ('trailer', 'Trailer'),
        ('commercial', 'Commercial'),
        ('short_film', 'Short Film'),
        ('documentary', 'Documentary'),
        ('other', 'Other'),
    ]
    
    # Content-specific fields
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='other')
    creator = models.CharField(max_length=200, blank=True, help_text="Content creator/host")
    series_name = models.CharField(max_length=200, blank=True, help_text="Series or channel name")
    episode_number = models.PositiveIntegerField(blank=True, null=True)
    
    # Educational content
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        blank=True
    )
    
    # Live streaming
    is_live = models.BooleanField(default=False)
    scheduled_live_time = models.DateTimeField(blank=True, null=True)
    live_stream_url = models.URLField(blank=True, help_text="Live stream URL")
    
    class Meta:
        verbose_name = 'Content'
        verbose_name_plural = 'Content'
        ordering = ['-created_at']
    
    def get_absolute_url(self):
        return reverse('media_content:content-detail', kwargs={'slug': self.slug})

class MediaInteraction(models.Model):
    """Track user interactions with media content"""
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('watch', 'Watch'),
        ('bookmark', 'Bookmark'),
        ('share', 'Share'),
        ('download', 'Download'),
        ('rate', 'Rate'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=20, choices=[('film', 'Film'), ('content', 'Content')])
    object_id = models.UUIDField()
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For watching progress
    watch_progress = models.FloatField(default=0.0, help_text="Percentage watched (0-100)")
    watch_time = models.PositiveIntegerField(default=0, help_text="Time watched in seconds")
    
    # For ratings
    rating = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1-5 stars"
    )
    
    class Meta:
        unique_together = ['user', 'content_type', 'object_id', 'interaction_type']
        ordering = ['-created_at']
        verbose_name = 'Media Interaction'
        verbose_name_plural = 'Media Interactions'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'interaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.content_type} {self.object_id}"

class MediaView(models.Model):
    """Track media views for analytics"""
    content_type = models.CharField(max_length=20, choices=[('film', 'Film'), ('content', 'Content')])
    object_id = models.UUIDField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    # Viewing session data
    watch_duration = models.PositiveIntegerField(default=0, help_text="Time watched in seconds")
    completion_percentage = models.FloatField(default=0.0, help_text="Percentage of content watched")
    quality_watched = models.CharField(max_length=10, choices=BaseMediaContent.QUALITY_CHOICES, blank=True)
    
    # Device information
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
    
    class Meta:
        ordering = ['-viewed_at']
        verbose_name = 'Media View'
        verbose_name_plural = 'Media Views'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['viewed_at']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_info} viewed {self.content_type} {self.object_id}"

class MediaCollection(models.Model):
    """User-created collections of media content"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_collections')
    is_public = models.BooleanField(default=False)
    
    # Collections can contain both films and content
    films = models.ManyToManyField(Film, related_name='collections', blank=True)
    content = models.ManyToManyField(Content, related_name='collections', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']
        verbose_name = 'Media Collection'
        verbose_name_plural = 'Media Collections'
    
    def __str__(self):
        return f"{self.user.username}'s {self.name}"
    
    @property
    def total_items(self):
        return self.films.count() + self.content.count()

class Playlist(models.Model):
    """Curated playlists for continuous watching"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    is_public = models.BooleanField(default=True)
    is_auto_play = models.BooleanField(default=True, help_text="Auto-play next item in playlist")
    
    thumbnail = models.ImageField(upload_to='playlists/thumbnails/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Playlist'
        verbose_name_plural = 'Playlists'
    
    def __str__(self):
        return self.name

class PlaylistItem(models.Model):
    """Items in a playlist with ordering"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='items')
    content_type = models.CharField(max_length=20, choices=[('film', 'Film'), ('content', 'Content')])
    object_id = models.UUIDField()
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['playlist', 'order']
        unique_together = ['playlist', 'content_type', 'object_id']
        verbose_name = 'Playlist Item'
        verbose_name_plural = 'Playlist Items'
    
    def __str__(self):
        return f"{self.playlist.name} - Item {self.order}"

# Signals to update counts when interactions change

@receiver(post_save, sender=MediaInteraction)
def update_media_counts(sender, instance, created, **kwargs):
    """Update media counts when interaction is created"""
    if created:
        # Get the media object
        if instance.content_type == 'film':
            media_obj = Film.objects.filter(id=instance.object_id).first()
        else:
            media_obj = Content.objects.filter(id=instance.object_id).first()
        
        if media_obj:
            if instance.interaction_type == 'like':
                media_obj.like_count = MediaInteraction.objects.filter(
                    content_type=instance.content_type,
                    object_id=instance.object_id,
                    interaction_type='like'
                ).count()
                media_obj.save(update_fields=['like_count'])
            
            elif instance.interaction_type == 'rate' and instance.rating:
                # Update average rating
                ratings = MediaInteraction.objects.filter(
                    content_type=instance.content_type,
                    object_id=instance.object_id,
                    interaction_type='rate',
                    rating__isnull=False
                )
                
                if ratings.exists():
                    avg_rating = sum(r.rating for r in ratings) / ratings.count()
                    media_obj.average_rating = round(avg_rating, 1)
                    media_obj.rating_count = ratings.count()
                    media_obj.save(update_fields=['average_rating', 'rating_count'])

@receiver(post_delete, sender=MediaInteraction)
def update_media_counts_on_delete(sender, instance, **kwargs):
    """Update media counts when interaction is deleted"""
    # Get the media object
    if instance.content_type == 'film':
        media_obj = Film.objects.filter(id=instance.object_id).first()
    else:
        media_obj = Content.objects.filter(id=instance.object_id).first()
    
    if media_obj:
        if instance.interaction_type == 'like':
            media_obj.like_count = MediaInteraction.objects.filter(
                content_type=instance.content_type,
                object_id=instance.object_id,
                interaction_type='like'
            ).count()
            media_obj.save(update_fields=['like_count'])
        
        elif instance.interaction_type == 'rate':
            # Recalculate average rating
            ratings = MediaInteraction.objects.filter(
                content_type=instance.content_type,
                object_id=instance.object_id,
                interaction_type='rate',
                rating__isnull=False
            )
            
            if ratings.exists():
                avg_rating = sum(r.rating for r in ratings) / ratings.count()
                media_obj.average_rating = round(avg_rating, 1)
                media_obj.rating_count = ratings.count()
            else:
                media_obj.average_rating = 0.0
                media_obj.rating_count = 0
            
            media_obj.save(update_fields=['average_rating', 'rating_count'])