#type: ignore

# media_content/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
import uuid

User = get_user_model()


class MediaCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Media Categories"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class BaseMedia(models.Model):
    """Abstract base model for media content (Films and Contents)"""
    
    CONTENT_TYPES = [
        ('FILM', 'Film'),
        ('CONTENT', 'Content'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]
    
    QUALITY_CHOICES = [
        ('360p', '360p'),
        ('480p', '480p'),
        ('720p', '720p HD'),
        ('1080p', '1080p Full HD'),
        ('1440p', '1440p 2K'),
        ('2160p', '2160p 4K'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(help_text="Brief description of the media")
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_authored')
    categories = models.ManyToManyField(MediaCategory, related_name='%(class)s_items', blank=True)
    tags = models.CharField(max_length=500, help_text="Comma-separated tags", blank=True)
    
    # Media files
    video_file = models.FileField(upload_to='media/videos/', help_text="Main video file")
    trailer = models.FileField(upload_to='media/trailers/', blank=True, null=True, help_text="Trailer video")
    thumbnail = models.ImageField(upload_to='media/thumbnails/', help_text="Video thumbnail")
    
    # Thumbnail variations
    thumbnail_small = ImageSpecField(
        source='thumbnail',
        processors=[ResizeToFill(300, 200)],
        format='JPEG',
        options={'quality': 80}
    )
    thumbnail_medium = ImageSpecField(
        source='thumbnail',
        processors=[ResizeToFill(600, 400)],
        format='JPEG',
        options={'quality': 85}
    )
    thumbnail_large = ImageSpecField(
        source='thumbnail',
        processors=[ResizeToFill(1200, 800)],
        format='JPEG',
        options={'quality': 90}
    )
    
    # Media metadata
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='1080p')
    file_size = models.BigIntegerField(help_text="File size in bytes", blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    
    # Analytics fields
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['status', 'is_trending']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['content_type', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{str(self.id)[:8]}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} ({self.content_type})"
    
    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    @property
    def duration_formatted(self):
        """Return duration in HH:MM:SS format"""
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


class Film(BaseMedia):
    """Model for films"""
    
    GENRE_CHOICES = [
        ('ACTION', 'Action'),
        ('COMEDY', 'Comedy'),
        ('DRAMA', 'Drama'),
        ('HORROR', 'Horror'),
        ('ROMANCE', 'Romance'),
        ('THRILLER', 'Thriller'),
        ('DOCUMENTARY', 'Documentary'),
        ('ANIMATION', 'Animation'),
        ('SCIENCE_FICTION', 'Science Fiction'),
        ('FANTASY', 'Fantasy'),
    ]
    
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, blank=True)
    release_year = models.PositiveIntegerField(blank=True, null=True)
    director = models.CharField(max_length=200, blank=True)
    cast = models.TextField(blank=True, help_text="Main cast members")
    language = models.CharField(max_length=50, default='English')
    subtitles_available = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Film"
        verbose_name_plural = "Films"
    
    def save(self, *args, **kwargs):
        self.content_type = 'FILM'
        super().save(*args, **kwargs)


class Content(BaseMedia):
    """Model for general content"""
    
    CONTENT_CATEGORY_CHOICES = [
        ('EDUCATIONAL', 'Educational'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('TUTORIAL', 'Tutorial'),
        ('REVIEW', 'Review'),
        ('INTERVIEW', 'Interview'),
        ('VLOG', 'Vlog'),
        ('NEWS', 'News'),
        ('SPORTS', 'Sports'),
        ('MUSIC', 'Music'),
        ('GAMING', 'Gaming'),
    ]
    
    category = models.CharField(max_length=20, choices=CONTENT_CATEGORY_CHOICES, blank=True)
    series_name = models.CharField(max_length=200, blank=True, help_text="If part of a series")
    episode_number = models.PositiveIntegerField(blank=True, null=True)
    season_number = models.PositiveIntegerField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Content"
        verbose_name_plural = "Contents"
    
    def save(self, *args, **kwargs):
        self.content_type = 'CONTENT'
        super().save(*args, **kwargs)


class MediaLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_likes')
    content_type = models.CharField(max_length=10, choices=BaseMedia.CONTENT_TYPES)
    object_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} likes {self.content_type} {self.object_id}"


class MediaView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_views', blank=True, null=True)
    content_type = models.CharField(max_length=10, choices=BaseMedia.CONTENT_TYPES)
    object_id = models.UUIDField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    watch_duration = models.PositiveIntegerField(default=0, help_text="Duration watched in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'created_at']),
            models.Index(fields=['user', 'content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"View of {self.content_type} {self.object_id}"


class WatchProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_progress')
    content_type = models.CharField(max_length=10, choices=BaseMedia.CONTENT_TYPES)
    object_id = models.UUIDField()
    current_time = models.PositiveIntegerField(default=0, help_text="Current position in seconds")
    total_duration = models.PositiveIntegerField(help_text="Total duration in seconds")
    progress_percentage = models.FloatField(default=0.0)
    last_watched_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['user', 'last_watched_at']),
        ]
    
    def save(self, *args, **kwargs):
        if self.total_duration > 0:
            self.progress_percentage = (self.current_time / self.total_duration) * 100
            self.completed = self.progress_percentage >= 90  # Consider 90% as completed
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.full_name} watching {self.content_type} {self.object_id} - {self.progress_percentage}%"


class MediaSubtitle(models.Model):
    content_type = models.CharField(max_length=10, choices=BaseMedia.CONTENT_TYPES)
    object_id = models.UUIDField()
    language = models.CharField(max_length=50)
    subtitle_file = models.FileField(upload_to='media/subtitles/')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['content_type', 'object_id', 'language']
    
    def __str__(self):
        return f"Subtitles ({self.language}) for {self.content_type} {self.object_id}"