#type: ignore

# stories/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.urls import reverse
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

User = get_user_model()

class Story(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    CATEGORY_CHOICES = [
        ('fiction', 'Fiction'),
        ('non_fiction', 'Non-Fiction'),
        ('tech', 'Technology'),
        ('lifestyle', 'Lifestyle'),
        ('adventure', 'Adventure'),
        ('romance', 'Romance'),
        ('mystery', 'Mystery'),
        ('fantasy', 'Fantasy'),
        ('sci_fi', 'Science Fiction'),
        ('biography', 'Biography'),
        ('educational', 'Educational'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    description = models.TextField(max_length=500, help_text="Brief description of the story")
    
    # Content
    content = models.TextField(help_text="Main story content with rich text support")
    excerpt = models.TextField(max_length=300, blank=True, help_text="Auto-generated from content")
    
    # Categorization
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    tags = models.JSONField(default=list, blank=True, help_text="List of tags for the story")
    
    # Media
    thumbnail = models.ImageField(upload_to='stories/thumbnails/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='stories/covers/', blank=True, null=True)
    
    # Metadata
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    
    # Metrics
    read_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    # Timing
    estimated_read_time = models.PositiveIntegerField(
        default=5, 
        validators=[MinValueValidator(1)],
        help_text="Estimated read time in minutes"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Story'
        verbose_name_plural = 'Stories'
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
            while Story.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Auto-generate excerpt from content if not provided
        if not self.excerpt and self.content:
            # Remove HTML tags and get first 250 characters
            import re
            clean_content = re.sub('<[^<]+?>', '', self.content)
            self.excerpt = clean_content[:250] + ('...' if len(clean_content) > 250 else '')
        
        # Calculate estimated read time (average 200 words per minute)
        if self.content:
            word_count = len(self.content.split())
            self.estimated_read_time = max(1, round(word_count / 200))
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('stories:detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        return self.status == 'published'
    
    def increment_read_count(self):
        """Increment read count atomically"""
        Story.objects.filter(id=self.id).update(read_count=models.F('read_count') + 1)
        self.refresh_from_db(fields=['read_count'])

class StoryPage(models.Model):
    """For paginated story content - 300-400 words per page"""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='pages')
    page_number = models.PositiveIntegerField()
    title = models.CharField(max_length=100, blank=True, help_text="Optional page title")
    content = models.TextField(help_text="Page content (300-400 words)")
    
    # Media for this specific page
    page_image = models.ImageField(upload_to='stories/pages/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['story', 'page_number']
        unique_together = ['story', 'page_number']
        verbose_name = 'Story Page'
        verbose_name_plural = 'Story Pages'
    
    def __str__(self):
        return f"{self.story.title} - Page {self.page_number}"
    
    @property
    def word_count(self):
        return len(self.content.split())

class StoryInteraction(models.Model):
    """Track user interactions with stories"""
    INTERACTION_TYPES = [
        ('like', 'Like'),
        ('read', 'Read'),
        ('bookmark', 'Bookmark'),
        ('share', 'Share'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For tracking reading progress
    last_page_read = models.PositiveIntegerField(default=1)
    reading_progress = models.FloatField(default=0.0, help_text="Percentage of story read (0-100)")
    
    class Meta:
        unique_together = ['user', 'story', 'interaction_type']
        ordering = ['-created_at']
        verbose_name = 'Story Interaction'
        verbose_name_plural = 'Story Interactions'
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.story.title}"

class StoryView(models.Model):
    """Track story views for analytics"""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    # Reading session data
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent reading in seconds")
    pages_viewed = models.JSONField(default=list, help_text="List of page numbers viewed")
    
    class Meta:
        ordering = ['-viewed_at']
        verbose_name = 'Story View'
        verbose_name_plural = 'Story Views'
    
    def __str__(self):
        user_info = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_info} viewed {self.story.title}"

class StoryCollection(models.Model):
    """User-created collections of stories"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_collections')
    stories = models.ManyToManyField(Story, related_name='collections', blank=True)
    is_public = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']
        verbose_name = 'Story Collection'
        verbose_name_plural = 'Story Collections'
    
    def __str__(self):
        return f"{self.user.username}'s {self.name}"
    
    @property
    def story_count(self):
        return self.stories.count()

# Signal to update story counts when interactions change


@receiver(post_save, sender=StoryInteraction)
def update_story_like_count(sender, instance, created, **kwargs):
    """Update story like count when interaction is created"""
    if created and instance.interaction_type == 'like':
        story = instance.story
        story.like_count = StoryInteraction.objects.filter(
            story=story, 
            interaction_type='like'
        ).count()
        story.save(update_fields=['like_count'])

@receiver(post_delete, sender=StoryInteraction)
def update_story_like_count_on_delete(sender, instance, **kwargs):
    """Update story like count when interaction is deleted"""
    if instance.interaction_type == 'like':
        story = instance.story
        story.like_count = StoryInteraction.objects.filter(
            story=story, 
            interaction_type='like'
        ).count()
        story.save(update_fields=['like_count'])