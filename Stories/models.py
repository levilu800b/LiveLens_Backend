#type: ignore

# stories/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from tinymce.models import HTMLField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
import uuid

User = get_user_model()


class StoryCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Story Categories"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Story(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(help_text="Brief description of the story")
    content = HTMLField(help_text="Main story content with rich text formatting")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    categories = models.ManyToManyField(StoryCategory, related_name='stories', blank=True)
    tags = models.CharField(max_length=500, help_text="Comma-separated tags", blank=True)
    
    # Media fields
    thumbnail = models.ImageField(upload_to='stories/thumbnails/', help_text="Story thumbnail image")
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
    
    # Story metadata
    estimated_reading_time = models.PositiveIntegerField(help_text="Estimated reading time in minutes", default=5)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    
    # Analytics fields
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['status', 'is_trending']),
            models.Index(fields=['author', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{str(self.id)[:8]}")
        
        # Calculate estimated reading time (average 200 words per minute)
        if self.content:
            word_count = len(self.content.split())
            self.estimated_reading_time = max(1, word_count // 200)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class StoryPage(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='pages')
    page_number = models.PositiveIntegerField()
    content = HTMLField(help_text="Content for this page (300-400 words recommended)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['page_number']
        unique_together = ['story', 'page_number']
    
    def __str__(self):
        return f"{self.story.title} - Page {self.page_number}"


class StoryIllustration(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='illustrations')
    page = models.ForeignKey(StoryPage, on_delete=models.CASCADE, related_name='illustrations', blank=True, null=True)
    image = models.ImageField(upload_to='stories/illustrations/')
    caption = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=200, help_text="Alternative text for accessibility")
    position = models.PositiveIntegerField(default=0, help_text="Position within the story/page")
    
    # Image specifications
    image_small = ImageSpecField(
        source='image',
        processors=[ResizeToFill(400, 300)],
        format='JPEG',
        options={'quality': 80}
    )
    image_medium = ImageSpecField(
        source='image',
        processors=[ResizeToFill(800, 600)],
        format='JPEG',
        options={'quality': 85}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return f"Illustration for {self.story.title}"


class StoryLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_likes')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'story']
    
    def __str__(self):
        return f"{self.user.full_name} likes {self.story.title}"


class StoryView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_views', blank=True, null=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['story', 'created_at']),
            models.Index(fields=['user', 'story']),
        ]
    
    def __str__(self):
        return f"View of {self.story.title}"


class StoryReadingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_progress')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reading_progress')
    current_page = models.PositiveIntegerField(default=1)
    progress_percentage = models.FloatField(default=0.0)
    last_read_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'story']
    
    def __str__(self):
        return f"{self.user.full_name} reading {self.story.title} - {self.progress_percentage}%"