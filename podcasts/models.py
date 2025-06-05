#type: ignore

# podcasts/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


User = get_user_model()

class PodcastSeries(models.Model):
    """Model for Podcast Series/Shows"""
    
    CATEGORY_CHOICES = [
        ('arts', 'Arts'),
        ('business', 'Business'),
        ('comedy', 'Comedy'),
        ('education', 'Education'),
        ('fiction', 'Fiction'),
        ('government', 'Government'),
        ('health_fitness', 'Health & Fitness'),
        ('history', 'History'),
        ('kids_family', 'Kids & Family'),
        ('leisure', 'Leisure'),
        ('music', 'Music'),
        ('news', 'News'),
        ('religion_spirituality', 'Religion & Spirituality'),
        ('science', 'Science'),
        ('society_culture', 'Society & Culture'),
        ('sports', 'Sports'),
        ('technology', 'Technology'),
        ('true_crime', 'True Crime'),
        ('tv_film', 'TV & Film'),
        ('other', 'Other'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('pt', 'Portuguese'),
        ('ru', 'Russian'),
        ('ja', 'Japanese'),
        ('ko', 'Korean'),
        ('zh', 'Chinese'),
        ('ar', 'Arabic'),
        ('hi', 'Hindi'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(max_length=1000, help_text="Detailed description of the podcast series")
    short_description = models.CharField(max_length=300, blank=True, help_text="Brief description for cards")
    
    # Categorization
    category = models.CharField(max_length=25, choices=CATEGORY_CHOICES, default='other')
    subcategory = models.CharField(max_length=100, blank=True, help_text="Subcategory within main category")
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for the series")
    
    # Media
    cover_image = models.ImageField(upload_to='podcasts/covers/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='podcasts/thumbnails/', blank=True, null=True)
    banner = models.ImageField(upload_to='podcasts/banners/', blank=True, null=True)
    
    # Series Metadata
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='podcast_series')
    host = models.CharField(max_length=200, help_text="Podcast host name(s)")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_explicit = models.BooleanField(default=False, help_text="Contains explicit content")
    
    # External Links
    website = models.URLField(blank=True, help_text="Podcast website")
    rss_feed = models.URLField(blank=True, help_text="RSS feed URL")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Podcast Series'
        verbose_name_plural = 'Podcast Series'
        indexes = [
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['is_featured', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            self.slug = slugify(self.title)
            
            # Ensure slug uniqueness
            counter = 1
            original_slug = self.slug
            while PodcastSeries.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-generate short description if not provided
        if not self.short_description and self.description:
            self.short_description = self.description[:250] + ('...' if len(self.description) > 250 else '')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def episode_count(self):
        return self.episodes.filter(status='published').count()
    
    @property
    def total_duration(self):
        """Total duration of all published episodes"""
        episodes = self.episodes.filter(status='published')
        return sum(episode.duration for episode in episodes)
    
    @property
    def latest_episode(self):
        return self.episodes.filter(status='published').order_by('-published_at').first()
    
    def get_absolute_url(self):
        return reverse('podcasts:series-detail', kwargs={'slug': self.slug})

class Podcast(models.Model):
    """Model for individual Podcast Episodes"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('scheduled', 'Scheduled'),
    ]
    
    EPISODE_TYPE_CHOICES = [
        ('full', 'Full Episode'),
        ('trailer', 'Trailer'),
        ('bonus', 'Bonus Content'),
        ('interview', 'Interview'),
        ('recap', 'Recap'),
        ('special', 'Special Episode'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True)
    description = models.TextField(max_length=1000, help_text="Detailed episode description")
    summary = models.CharField(max_length=300, blank=True, help_text="Brief episode summary")
    
    # Series Relationship
    series = models.ForeignKey(PodcastSeries, on_delete=models.CASCADE, related_name='episodes')
    episode_number = models.PositiveIntegerField(help_text="Episode number within series")
    season_number = models.PositiveIntegerField(default=1, help_text="Season number")
    episode_type = models.CharField(max_length=10, choices=EPISODE_TYPE_CHOICES, default='full')
    
    # Media Files
    audio_file = models.FileField(upload_to='podcasts/audio/', blank=True, null=True, help_text="Main audio file")
    video_file = models.FileField(upload_to='podcasts/video/', blank=True, null=True, help_text="Video podcast file")
    transcript_file = models.FileField(upload_to='podcasts/transcripts/', blank=True, null=True, help_text="Episode transcript")
    
    # Episode Images
    cover_image = models.ImageField(upload_to='podcasts/episodes/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='podcasts/episode_thumbs/', blank=True, null=True)
    
    # Audio Metadata
    duration = models.PositiveIntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        help_text="Duration in seconds"
    )
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    audio_quality = models.CharField(
        max_length=20,
        choices=[
            ('64kbps', '64 kbps'),
            ('128kbps', '128 kbps'),
            ('192kbps', '192 kbps'),
            ('256kbps', '256 kbps'),
            ('320kbps', '320 kbps'),
        ],
        default='128kbps'
    )
    
    # Content Metadata
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='podcast_episodes')
    guest = models.CharField(max_length=200, blank=True, help_text="Episode guest(s)")
    tags = models.JSONField(default=list, blank=True, help_text="Episode-specific tags")
    
    # Status and Visibility
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False, help_text="Requires premium subscription")
    is_explicit = models.BooleanField(default=False, help_text="Contains explicit content")
    
    # Engagement Metrics
    play_count = models.PositiveIntegerField(default=0)
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
    scheduled_at = models.DateTimeField(blank=True, null=True, help_text="Scheduled publish time")
    
    # External Links
    external_url = models.URLField(blank=True, help_text="External hosting URL")
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        unique_together = ['series', 'season_number', 'episode_number']
        verbose_name = 'Podcast Episode'
        verbose_name_plural = 'Podcast Episodes'
        indexes = [
            models.Index(fields=['series', '-published_at']),
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['is_featured', '-published_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title and episode number
        if not self.slug:
            base_slug = slugify(f"{self.title}-episode-{self.episode_number}")
            self.slug = base_slug
            
            # Ensure slug uniqueness within series
            counter = 1
            while Podcast.objects.filter(series=self.series, slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        # Auto-generate summary if not provided
        if not self.summary and self.description:
            self.summary = self.description[:250] + ('...' if len(self.description) > 250 else '')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.series.title} - S{self.season_number}E{self.episode_number}: {self.title}"
    
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
    def file_size_formatted(self):
        """Return file size in human readable format"""
        if not self.file_size:
            return "0 B"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def increment_play_count(self):
        """Increment play count atomically"""
        Podcast.objects.filter(id=self.id).update(play_count=models.F('play_count') + 1)
        self.refresh_from_db(fields=['play_count'])
    
    def get_absolute_url(self):
        return reverse('podcasts:episode-detail', kwargs={
            'series_slug': self.series.slug,
            'slug': self.slug
        })

class PodcastInteraction(models.Model):
    """Track user interactions with podcasts"""
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('listen', 'Listen'),
        ('bookmark', 'Bookmark'),
        ('share', 'Share'),
        ('download', 'Download'),
        ('rate', 'Rate'),
        ('subscribe', 'Subscribe'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE, blank=True, null=True)
    series = models.ForeignKey(PodcastSeries, on_delete=models.CASCADE, blank=True, null=True)
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For listening progress
    listen_progress = models.FloatField(default=0.0, help_text="Percentage listened (0-100)")
    listen_time = models.PositiveIntegerField(default=0, help_text="Time listened in seconds")
    
    # For ratings
    rating = models.PositiveIntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1-5 stars"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Podcast Interaction'
        verbose_name_plural = 'Podcast Interactions'
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['podcast', 'interaction_type']),
            models.Index(fields=['series', 'interaction_type']),
        ]
    
    def __str__(self):
        target = self.podcast or self.series
        return f"{self.user.username} {self.interaction_type} {target}"

class PodcastPlaylist(models.Model):
    """User-created podcast playlists"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='podcast_playlists')
    episodes = models.ManyToManyField(Podcast, related_name='playlists', blank=True)
    is_public = models.BooleanField(default=False)
    
    # Playlist settings
    auto_play = models.BooleanField(default=True, help_text="Auto-play next episode")
    shuffle = models.BooleanField(default=False, help_text="Shuffle playback order")
    
    # Images
    cover_image = models.ImageField(upload_to='podcasts/playlist_covers/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']
        verbose_name = 'Podcast Playlist'
        verbose_name_plural = 'Podcast Playlists'
    
    def __str__(self):
        return f"{self.user.username}'s {self.name}"
    
    @property
    def episode_count(self):
        return self.episodes.count()
    
    @property
    def total_duration(self):
        return sum(episode.duration for episode in self.episodes.all())

class PodcastSubscription(models.Model):
    """User subscriptions to podcast series"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='podcast_subscriptions')
    series = models.ForeignKey(PodcastSeries, on_delete=models.CASCADE, related_name='subscribers')
    
    # Subscription settings
    notifications_enabled = models.BooleanField(default=True, help_text="Get notifications for new episodes")
    auto_download = models.BooleanField(default=False, help_text="Auto-download new episodes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'series']
        ordering = ['-created_at']
        verbose_name = 'Podcast Subscription'
        verbose_name_plural = 'Podcast Subscriptions'
    
    def __str__(self):
        return f"{self.user.username} subscribed to {self.series.title}"

class PodcastView(models.Model):
    """Track podcast listening for analytics"""
    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    listened_at = models.DateTimeField(auto_now_add=True)
    
    # Listening session data
    listen_duration = models.PositiveIntegerField(default=0, help_text="Time listened in seconds")
    completion_percentage = models.FloatField(default=0.0, help_text="Percentage of episode listened")
    
    # Device information
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
            ('smart_speaker', 'Smart Speaker'),
            ('car', 'Car Audio'),
            ('other', 'Other'),
        ],
        default='other'
    )
    
    class Meta:
        ordering = ['-listened_at']
        verbose_name = 'Podcast View'
        verbose_name_plural = 'Podcast Views'
        indexes = [
            models.Index(fields=['podcast', '-listened_at']),
            models.Index(fields=['user', '-listened_at']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_info} listened to {self.podcast.title}"

# Signals to update counts when interactions change

@receiver(post_save, sender=PodcastInteraction)
def update_podcast_counts(sender, instance, created, **kwargs):
    """Update podcast counts when interaction is created"""
    if created and instance.podcast:
        podcast = instance.podcast
        
        if instance.interaction_type == 'like':
            podcast.like_count = PodcastInteraction.objects.filter(
                podcast=podcast,
                interaction_type='like'
            ).count()
            podcast.save(update_fields=['like_count'])
        
        elif instance.interaction_type == 'rate' and instance.rating:
            # Update average rating
            ratings = PodcastInteraction.objects.filter(
                podcast=podcast,
                interaction_type='rate',
                rating__isnull=False
            )
            
            if ratings.exists():
                avg_rating = sum(r.rating for r in ratings) / ratings.count()
                podcast.average_rating = round(avg_rating, 1)
                podcast.rating_count = ratings.count()
                podcast.save(update_fields=['average_rating', 'rating_count'])

@receiver(post_delete, sender=PodcastInteraction)
def update_podcast_counts_on_delete(sender, instance, **kwargs):
    """Update podcast counts when interaction is deleted"""
    if instance.podcast:
        podcast = instance.podcast
        
        if instance.interaction_type == 'like':
            podcast.like_count = PodcastInteraction.objects.filter(
                podcast=podcast,
                interaction_type='like'
            ).count()
            podcast.save(update_fields=['like_count'])
        
        elif instance.interaction_type == 'rate':
            # Recalculate average rating
            ratings = PodcastInteraction.objects.filter(
                podcast=podcast,
                interaction_type='rate',
                rating__isnull=False
            )
            
            if ratings.exists():
                avg_rating = sum(r.rating for r in ratings) / ratings.count()
                podcast.average_rating = round(avg_rating, 1)
                podcast.rating_count = ratings.count()
            else:
                podcast.average_rating = 0.0
                podcast.rating_count = 0
            
            podcast.save(update_fields=['average_rating', 'rating_count'])