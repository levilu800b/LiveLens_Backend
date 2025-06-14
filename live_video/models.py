# live_video/models.py
# type: ignore

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField

User = get_user_model()

class LiveVideo(models.Model):
    """Model for live video content"""
    
    LIVE_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live Now'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]
    
    VIDEO_QUALITY_CHOICES = [
        ('360p', '360p'),
        ('480p', '480p'),
        ('720p', '720p HD'),
        ('1080p', '1080p Full HD'),
        ('1440p', '1440p 2K'),
        ('2160p', '2160p 4K'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(max_length=1000, help_text="Detailed description of the live video")
    short_description = models.CharField(max_length=300, blank=True, help_text="Brief description for cards")
    
    # Media Files
    thumbnail = CloudinaryField('image', blank=True, help_text="Thumbnail image for the live video")
    video_file = CloudinaryField('video', blank=True, help_text="Pre-recorded video file (if not truly live)")
    
    # Live Stream Configuration
    live_status = models.CharField(max_length=20, choices=LIVE_STATUS_CHOICES, default='scheduled')
    scheduled_start_time = models.DateTimeField(help_text="When the live stream is scheduled to start")
    scheduled_end_time = models.DateTimeField(blank=True, null=True, help_text="When the live stream is scheduled to end")
    actual_start_time = models.DateTimeField(blank=True, null=True, help_text="When the live stream actually started")
    actual_end_time = models.DateTimeField(blank=True, null=True, help_text="When the live stream actually ended")
    
    # Stream URLs and Configuration
    live_stream_url = models.URLField(blank=True, help_text="Live stream URL (RTMP, HLS, etc.)")
    backup_stream_url = models.URLField(blank=True, help_text="Backup stream URL")
    stream_key = models.CharField(max_length=255, blank=True, help_text="Stream key for broadcasting")
    
    # Technical Details
    video_quality = models.CharField(max_length=10, choices=VIDEO_QUALITY_CHOICES, default='1080p')
    duration = models.PositiveIntegerField(blank=True, null=True, help_text="Expected duration in seconds")
    max_viewers = models.PositiveIntegerField(default=1000, help_text="Maximum concurrent viewers allowed")
    
    # Content Details
    host_name = models.CharField(max_length=200, blank=True, help_text="Name of the live stream host")
    guest_speakers = models.TextField(blank=True, help_text="List of guest speakers (comma-separated)")
    tags = models.CharField(max_length=500, blank=True, help_text="Tags separated by commas")
    
    # Settings
    is_featured = models.BooleanField(default=False, help_text="Show in featured section")
    is_premium = models.BooleanField(default=False, help_text="Requires premium subscription")
    allow_chat = models.BooleanField(default=True, help_text="Allow viewers to chat during live stream")
    allow_recording = models.BooleanField(default=True, help_text="Record the live stream for later viewing")
    auto_start = models.BooleanField(default=False, help_text="Automatically start the stream at scheduled time")
    
    # Engagement Metrics
    current_viewers = models.PositiveIntegerField(default=0, help_text="Current number of viewers")
    peak_viewers = models.PositiveIntegerField(default=0, help_text="Peak number of concurrent viewers")
    total_views = models.PositiveIntegerField(default=0, help_text="Total number of unique views")
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    # Administrative
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='live_videos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Live Video'
        verbose_name_plural = 'Live Videos'
        ordering = ['-scheduled_start_time']
        indexes = [
            models.Index(fields=['live_status', '-scheduled_start_time']),
            models.Index(fields=['is_featured', '-scheduled_start_time']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            self.slug = slugify(self.title)
            
            # Ensure slug uniqueness
            counter = 1
            original_slug = self.slug
            while LiveVideo.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-generate short description if not provided
        if not self.short_description and self.description:
            self.short_description = self.description[:250] + ('...' if len(self.description) > 250 else '')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.get_live_status_display()}"
    
    @property
    def is_live_now(self):
        """Check if the live video is currently live"""
        return self.live_status == 'live'
    
    @property
    def is_upcoming(self):
        """Check if the live video is scheduled for the future"""
        return (
            self.live_status == 'scheduled' and 
            self.scheduled_start_time > timezone.now()
        )
    
    @property
    def is_ended(self):
        """Check if the live video has ended"""
        return self.live_status == 'ended'
    
    @property
    def duration_formatted(self):
        """Return duration in HH:MM:SS format"""
        if not self.duration:
            return "00:00:00"
        
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @property
    def time_until_start(self):
        """Get time until the live stream starts"""
        if self.scheduled_start_time:
            delta = self.scheduled_start_time - timezone.now()
            if delta.total_seconds() > 0:
                return delta
        return None
    
    @property
    def stream_duration(self):
        """Get actual stream duration if it has started"""
        if self.actual_start_time:
            end_time = self.actual_end_time or timezone.now()
            return end_time - self.actual_start_time
        return None
    
    def start_stream(self):
        """Mark the stream as live and set actual start time"""
        self.live_status = 'live'
        self.actual_start_time = timezone.now()
        self.save(update_fields=['live_status', 'actual_start_time'])
    
    def end_stream(self):
        """Mark the stream as ended and set actual end time"""
        self.live_status = 'ended'
        self.actual_end_time = timezone.now()
        self.save(update_fields=['live_status', 'actual_end_time'])
    
    def increment_viewers(self):
        """Increment current viewers count"""
        self.__class__.objects.filter(id=self.id).update(
            current_viewers=models.F('current_viewers') + 1
        )
        # Update peak viewers if necessary
        self.refresh_from_db(fields=['current_viewers'])
        if self.current_viewers > self.peak_viewers:
            self.peak_viewers = self.current_viewers
            self.save(update_fields=['peak_viewers'])
    
    def decrement_viewers(self):
        """Decrement current viewers count"""
        self.__class__.objects.filter(id=self.id).update(
            current_viewers=models.F('current_viewers') - 1
        )
        self.refresh_from_db(fields=['current_viewers'])
    
    def increment_total_views(self):
        """Increment total views count"""
        self.__class__.objects.filter(id=self.id).update(
            total_views=models.F('total_views') + 1
        )
        self.refresh_from_db(fields=['total_views'])
    
    def get_absolute_url(self):
        return reverse('live_video:detail', kwargs={'slug': self.slug})


class LiveVideoInteraction(models.Model):
    """Track user interactions with live videos"""
    
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('watch', 'Watch'),
        ('bookmark', 'Bookmark'),
        ('share', 'Share'),
        ('join', 'Join Stream'),
        ('leave', 'Leave Stream'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    live_video = models.ForeignKey(LiveVideo, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For watch tracking
    watch_duration = models.PositiveIntegerField(default=0, help_text="Time watched in seconds")
    joined_at = models.DateTimeField(blank=True, null=True, help_text="When user joined the live stream")
    left_at = models.DateTimeField(blank=True, null=True, help_text="When user left the live stream")
    
    class Meta:
        unique_together = ['user', 'live_video', 'interaction_type']
        ordering = ['-created_at']
        verbose_name = 'Live Video Interaction'
        verbose_name_plural = 'Live Video Interactions'
        indexes = [
            models.Index(fields=['live_video', 'interaction_type']),
            models.Index(fields=['user', 'interaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.live_video.title}"


class LiveVideoComment(models.Model):
    """Comments for live videos (chat functionality)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    live_video = models.ForeignKey(LiveVideo, on_delete=models.CASCADE, related_name='live_comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_moderator = models.BooleanField(default=False, help_text="Is this a moderator message")
    is_hidden = models.BooleanField(default=False, help_text="Hidden by moderator")
    
    # Stream timing
    stream_time = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        help_text="Time in seconds from stream start when comment was made"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Live Video Comment'
        verbose_name_plural = 'Live Video Comments'
        indexes = [
            models.Index(fields=['live_video', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}..."
    
    def save(self, *args, **kwargs):
        # Calculate stream time if the video is live
        if self.live_video.actual_start_time and not self.stream_time:
            delta = timezone.now() - self.live_video.actual_start_time
            self.stream_time = int(delta.total_seconds())
        
        super().save(*args, **kwargs)
        
        # Update comment count on live video
        if not self.is_hidden:
            self.live_video.comment_count = self.live_video.live_comments.filter(
                is_hidden=False
            ).count()
            self.live_video.save(update_fields=['comment_count'])


class LiveVideoSchedule(models.Model):
    """Recurring schedule for live videos"""
    
    FREQUENCY_CHOICES = [
        ('once', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title_template = models.CharField(max_length=200, help_text="Template for live video titles")
    description_template = models.TextField(max_length=1000, help_text="Template for live video descriptions")
    
    # Schedule Configuration
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='once')
    start_time = models.TimeField(help_text="Time to start the live stream")
    duration_minutes = models.PositiveIntegerField(default=60, help_text="Expected duration in minutes")
    
    # Weekly schedule
    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES, 
        blank=True, 
        null=True, 
        help_text="Day of week for weekly streams"
    )
    
    # Monthly schedule
    day_of_month = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of month for monthly streams"
    )
    
    # Configuration
    is_active = models.BooleanField(default=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='live_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Live Video Schedule'
        verbose_name_plural = 'Live Video Schedules'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title_template} - {self.get_frequency_display()}"
    
    def create_next_live_video(self):
        """Create the next scheduled live video based on this schedule"""
        from datetime import datetime, timedelta
        
        now = timezone.now()
        
        # Calculate next scheduled time based on frequency
        if self.frequency == 'daily':
            next_date = now.date() + timedelta(days=1)
        elif self.frequency == 'weekly' and self.weekday is not None:
            days_ahead = self.weekday - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_date = now.date() + timedelta(days=days_ahead)
        elif self.frequency == 'monthly' and self.day_of_month is not None:
            # Calculate next month occurrence
            if now.day < self.day_of_month:
                next_date = now.date().replace(day=self.day_of_month)
            else:
                # Next month
                if now.month == 12:
                    next_date = now.date().replace(year=now.year + 1, month=1, day=self.day_of_month)
                else:
                    next_date = now.date().replace(month=now.month + 1, day=self.day_of_month)
        else:
            return None
        
        # Combine date and time
        scheduled_start = timezone.make_aware(
            datetime.combine(next_date, self.start_time)
        )
        
        # Create the live video
        live_video = LiveVideo.objects.create(
            title=self.title_template,
            description=self.description_template,
            scheduled_start_time=scheduled_start,
            duration=self.duration_minutes * 60,
            author=self.author,
            live_status='scheduled'
        )
        
        return live_video