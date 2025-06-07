# type: ignore

# animations/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

User = get_user_model()

class Animation(models.Model):
    """Model for Animation content"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('processing', 'Processing'),
        ('generating', 'AI Generating'),
    ]
    
    CATEGORY_CHOICES = [
        ('2d_traditional', '2D Traditional'),
        ('2d_digital', '2D Digital'),
        ('3d_animation', '3D Animation'),
        ('stop_motion', 'Stop Motion'),
        ('motion_graphics', 'Motion Graphics'),
        ('character_animation', 'Character Animation'),
        ('explainer', 'Explainer Video'),
        ('educational', 'Educational'),
        ('entertainment', 'Entertainment'),
        ('commercial', 'Commercial'),
        ('music_video', 'Music Video'),
        ('short_film', 'Short Film'),
        ('series', 'Series'),
        ('experimental', 'Experimental'),
        ('ai_generated', 'AI Generated'),
        ('other', 'Other'),
    ]
    
    ANIMATION_TYPE_CHOICES = [
        ('2d', '2D Animation'),
        ('3d', '3D Animation'),
        ('mixed', 'Mixed Media'),
        ('motion_graphics', 'Motion Graphics'),
        ('stop_motion', 'Stop Motion'),
        ('ai_generated', 'AI Generated'),
    ]
    
    QUALITY_CHOICES = [
        ('360p', '360p'),
        ('480p', '480p'),
        ('720p', '720p HD'),
        ('1080p', '1080p Full HD'),
        ('1440p', '1440p QHD'),
        ('2160p', '4K UHD'),
        ('4320p', '8K UHD'),
    ]
    
    FRAME_RATE_CHOICES = [
        ('12', '12 FPS'),
        ('24', '24 FPS'),
        ('25', '25 FPS'),
        ('30', '30 FPS'),
        ('60', '60 FPS'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(max_length=1000, help_text="Detailed description of the animation")
    short_description = models.CharField(max_length=300, blank=True, help_text="Brief description for cards")
    
    # Categorization
    category = models.CharField(max_length=25, choices=CATEGORY_CHOICES, default='other')
    animation_type = models.CharField(max_length=20, choices=ANIMATION_TYPE_CHOICES, default='2d')
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for the animation")
    
    # Media Files
    thumbnail = models.ImageField(upload_to='animations/thumbnails/', blank=True, null=True)
    poster = models.ImageField(upload_to='animations/posters/', blank=True, null=True)
    banner = models.ImageField(upload_to='animations/banners/', blank=True, null=True)
    video_file = models.FileField(upload_to='animations/videos/', blank=True, null=True, help_text="Main animation video file")
    trailer_file = models.FileField(upload_to='animations/trailers/', blank=True, null=True, help_text="Animation trailer")
    
    # Animation-specific files
    project_file = models.FileField(upload_to='animations/projects/', blank=True, null=True, help_text="Animation project file")
    storyboard = models.FileField(upload_to='animations/storyboards/', blank=True, null=True, help_text="Storyboard file")
    concept_art = models.ImageField(upload_to='animations/concept_art/', blank=True, null=True, help_text="Concept art")
    
    # Technical Metadata
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
    frame_rate = models.CharField(max_length=5, choices=FRAME_RATE_CHOICES, default='24')
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    resolution_width = models.PositiveIntegerField(default=1920, help_text="Video width in pixels")
    resolution_height = models.PositiveIntegerField(default=1080, help_text="Video height in pixels")
    
    # Animation Production Details
    animation_software = models.CharField(max_length=100, blank=True, help_text="Software used for animation")
    render_engine = models.CharField(max_length=100, blank=True, help_text="Rendering engine used")
    production_time = models.PositiveIntegerField(default=0, help_text="Production time in hours")
    
    # Content Metadata
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='animations')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False, help_text="Requires premium subscription")
    
    # Series Information
    is_series = models.BooleanField(default=False)
    series_name = models.CharField(max_length=200, blank=True)
    episode_number = models.PositiveIntegerField(blank=True, null=True)
    season_number = models.PositiveIntegerField(blank=True, null=True)
    
    # AI Generation
    is_ai_generated = models.BooleanField(default=False)
    ai_prompt = models.TextField(blank=True, help_text="AI generation prompt")
    ai_model_used = models.CharField(max_length=100, blank=True, help_text="AI model used for generation")
    generation_parameters = models.JSONField(default=dict, blank=True, help_text="AI generation parameters")
    
    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
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
    
    # Creative Credits
    director = models.CharField(max_length=200, blank=True, help_text="Animation director")
    animator = models.CharField(max_length=200, blank=True, help_text="Lead animator(s)")
    voice_actors = models.JSONField(default=list, blank=True, help_text="List of voice actors")
    music_composer = models.CharField(max_length=200, blank=True, help_text="Music composer")
    sound_designer = models.CharField(max_length=200, blank=True, help_text="Sound designer")
    
    # Production Information
    studio = models.CharField(max_length=100, blank=True, help_text="Animation studio")
    budget = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Production budget")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Animation'
        verbose_name_plural = 'Animations'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['animation_type', '-created_at']),
            models.Index(fields=['is_featured', '-created_at']),
            models.Index(fields=['is_trending', '-created_at']),
            models.Index(fields=['is_ai_generated', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            self.slug = slugify(self.title)
            
            # Ensure slug uniqueness
            counter = 1
            original_slug = self.slug
            while Animation.objects.filter(slug=self.slug).exists():
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
    
    @property
    def resolution_formatted(self):
        """Return resolution in WxH format"""
        return f"{self.resolution_width}x{self.resolution_height}"
    
    def increment_view_count(self):
        """Increment view count atomically"""
        Animation.objects.filter(id=self.id).update(view_count=models.F('view_count') + 1)
        self.refresh_from_db(fields=['view_count'])
    
    def get_absolute_url(self):
        return reverse('animations:detail', kwargs={'slug': self.slug})

class AnimationInteraction(models.Model):
    """Track user interactions with animations"""
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('watch', 'Watch'),
        ('bookmark', 'Bookmark'),
        ('share', 'Share'),
        ('download', 'Download'),
        ('rate', 'Rate'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    animation = models.ForeignKey(Animation, on_delete=models.CASCADE)
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
        unique_together = ['user', 'animation', 'interaction_type']
        ordering = ['-created_at']
        verbose_name = 'Animation Interaction'
        verbose_name_plural = 'Animation Interactions'
        indexes = [
            models.Index(fields=['animation', 'interaction_type']),
            models.Index(fields=['user', 'interaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.animation.title}"

class AnimationView(models.Model):
    """Track animation views for analytics"""
    animation = models.ForeignKey(Animation, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    # Viewing session data
    watch_duration = models.PositiveIntegerField(default=0, help_text="Time watched in seconds")
    completion_percentage = models.FloatField(default=0.0, help_text="Percentage of animation watched")
    quality_watched = models.CharField(max_length=10, choices=Animation.QUALITY_CHOICES, blank=True)
    
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
        verbose_name = 'Animation View'
        verbose_name_plural = 'Animation Views'
        indexes = [
            models.Index(fields=['animation', '-viewed_at']),
            models.Index(fields=['user', '-viewed_at']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_info} viewed {self.animation.title}"

class AnimationCollection(models.Model):
    """User-created collections of animations"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='animation_collections')
    animations = models.ManyToManyField(Animation, related_name='collections', blank=True)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']
        verbose_name = 'Animation Collection'
        verbose_name_plural = 'Animation Collections'
    
    def __str__(self):
        return f"{self.user.username}'s {self.name}"
    
    @property
    def animation_count(self):
        return self.animations.count()

class AnimationPlaylist(models.Model):
    """Curated playlists for continuous watching"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='animation_playlists')
    animations = models.ManyToManyField(Animation, related_name='playlists', blank=True)
    is_public = models.BooleanField(default=True)
    is_auto_play = models.BooleanField(default=True, help_text="Auto-play next animation in playlist")
    
    thumbnail = models.ImageField(upload_to='animations/playlist_thumbnails/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Animation Playlist'
        verbose_name_plural = 'Animation Playlists'
    
    def __str__(self):
        return self.name
    
    @property
    def animation_count(self):
        return self.animations.count()
    
    @property
    def total_duration(self):
        return sum(animation.duration for animation in self.animations.all())

class AIAnimationRequest(models.Model):
    """Track AI animation generation requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_animation_requests')
    animation = models.ForeignKey(Animation, on_delete=models.CASCADE, blank=True, null=True, related_name='ai_requests')
    
    # AI Generation Parameters
    prompt = models.TextField(help_text="User's animation description prompt")
    style = models.CharField(max_length=100, blank=True, help_text="Animation style (e.g., 2D, 3D, cartoon)")
    duration_requested = models.PositiveIntegerField(default=30, help_text="Requested duration in seconds")
    quality_requested = models.CharField(max_length=10, choices=Animation.QUALITY_CHOICES, default='1080p')
    frame_rate_requested = models.CharField(max_length=5, choices=Animation.FRAME_RATE_CHOICES, default='24')
    
    # Processing Information
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    ai_model_used = models.CharField(max_length=100, blank=True)
    processing_time = models.PositiveIntegerField(default=0, help_text="Processing time in seconds")
    error_message = models.TextField(blank=True)
    
    # Additional Parameters
    additional_parameters = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Animation Request'
        verbose_name_plural = 'AI Animation Requests'
    
    def __str__(self):
        return f"AI Request by {self.user.username}: {self.prompt[:50]}..."

# Signals to update counts when interactions change

@receiver(post_save, sender=AnimationInteraction)
def update_animation_counts(sender, instance, created, **kwargs):
    """Update animation counts when interaction is created"""
    if created:
        animation = instance.animation
        
        if instance.interaction_type == 'like':
            animation.like_count = AnimationInteraction.objects.filter(
                animation=animation,
                interaction_type='like'
            ).count()
            animation.save(update_fields=['like_count'])
        
        elif instance.interaction_type == 'rate' and instance.rating:
            # Update average rating
            ratings = AnimationInteraction.objects.filter(
                animation=animation,
                interaction_type='rate',
                rating__isnull=False
            )
            
            if ratings.exists():
                avg_rating = sum(r.rating for r in ratings) / ratings.count()
                animation.average_rating = round(avg_rating, 1)
                animation.rating_count = ratings.count()
                animation.save(update_fields=['average_rating', 'rating_count'])

@receiver(post_delete, sender=AnimationInteraction)
def update_animation_counts_on_delete(sender, instance, **kwargs):
    """Update animation counts when interaction is deleted"""
    animation = instance.animation
    
    if instance.interaction_type == 'like':
        animation.like_count = AnimationInteraction.objects.filter(
            animation=animation,
            interaction_type='like'
        ).count()
        animation.save(update_fields=['like_count'])
    
    elif instance.interaction_type == 'rate':
        # Recalculate average rating
        ratings = AnimationInteraction.objects.filter(
            animation=animation,
            interaction_type='rate',
            rating__isnull=False
        )
        
        if ratings.exists():
            avg_rating = sum(r.rating for r in ratings) / ratings.count()
            animation.average_rating = round(avg_rating, 1)
            animation.rating_count = ratings.count()
        else:
            animation.average_rating = 0.0
            animation.rating_count = 0
        
        animation.save(update_fields=['average_rating', 'rating_count'])