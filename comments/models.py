#type: ignore

# comments/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Comment(models.Model):
    CONTENT_TYPES = [
        ('STORY', 'Story'),
        ('FILM', 'Film'),
        ('CONTENT', 'Content'),
        ('PODCAST', 'Podcast'),
        ('ANIMATION', 'Animation'),
        ('SNEAK_PEEK', 'Sneak Peek'),
    ]
    
    EMOJI_CHOICES = [
        ('👍', 'Thumbs Up'),
        ('❤️', 'Heart'),
        ('😂', 'Laughing'),
        ('😮', 'Surprised'),
        ('😢', 'Sad'),
        ('😡', 'Angry'),
        ('🔥', 'Fire'),
        ('👏', 'Clapping'),
        ('🤔', 'Thinking'),
        ('💯', 'Hundred'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content_type = models.CharField(max_length=15, choices=CONTENT_TYPES)
    content_id = models.UUIDField(help_text="ID of the content being commented on")
    
    # Comment content
    text = models.TextField(max_length=1000)
    emoji = models.CharField(max_length=10, choices=EMOJI_CHOICES, blank=True)
    
    # Comment threading
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.CharField(max_length=200, blank=True)
    
    # Analytics
    like_count = models.PositiveIntegerField(default=0)
    reply_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'content_id', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.full_name} on {self.content_type} {self.content_id}"
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    def save(self, *args, **kwargs):
        # Update parent's reply count
        if self.parent and not self.pk:  # New reply
            Comment.objects.filter(id=self.parent.id).update(
                reply_count=models.F('reply_count') + 1
            )
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Update parent's reply count
        if self.parent:
            Comment.objects.filter(id=self.parent.id).update(
                reply_count=models.F('reply_count') - 1
            )
        super().delete(*args, **kwargs)


class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
    
    def __str__(self):
        return f"{self.user.full_name} likes comment {self.comment.id}"


class CommentFlag(models.Model):
    FLAG_REASONS = [
        ('SPAM', 'Spam'),
        ('INAPPROPRIATE', 'Inappropriate Content'),
        ('HARASSMENT', 'Harassment'),
        ('HATE_SPEECH', 'Hate Speech'),
        ('VIOLENCE', 'Violence'),
        ('COPYRIGHT', 'Copyright Violation'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_flags')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='flags')
    reason = models.CharField(max_length=20, choices=FLAG_REASONS)
    description = models.TextField(blank=True, help_text="Additional details about the flag")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'comment']
    
    def __str__(self):
        return f"Flag by {self.user.full_name} on comment {self.comment.id} - {self.reason}"


class CommentMention(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='mentions')
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_mentions')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['comment', 'mentioned_user']
    
    def __str__(self):
        return f"{self.mentioned_user.full_name} mentioned in comment {self.comment.id}"