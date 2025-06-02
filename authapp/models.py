#type: ignore
# authapp/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random
import string

class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Verification code for {self.user.email}: {self.code}"


class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('VIEW', 'View'),
        ('LIKE', 'Like'),
        ('UNLIKE', 'Unlike'), 
        ('COMMENT', 'Comment'),
        ('SHARE', 'Share'),
        ('WATCH', 'Watch'),
        ('READ', 'Read'),
    ]
    
    CONTENT_TYPES = [
        ('STORY', 'Story'),
        ('FILM', 'Film'),
        ('CONTENT', 'Content'),
        ('PODCAST', 'Podcast'),
        ('ANIMATION', 'Animation'),
        ('SNEAK_PEEK', 'Sneak Peek'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    content_type = models.CharField(max_length=15, choices=CONTENT_TYPES)
    content_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['content_type', 'content_id']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} {self.activity_type} {self.content_type} {self.content_id}"


class UserLibrary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_items')
    content_type = models.CharField(max_length=15, choices=UserActivity.CONTENT_TYPES)
    content_id = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    progress = models.FloatField(default=0.0)  # For tracking watch/read progress
    
    class Meta:
        unique_together = ['user', 'content_type', 'content_id']
        ordering = ['-last_accessed']
    
    def __str__(self):
        return f"{self.user.full_name}'s {self.content_type} {self.content_id}"


class UserFavorites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.CharField(max_length=15, choices=UserActivity.CONTENT_TYPES)
    content_id = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'content_type', 'content_id']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user.full_name}'s favorite {self.content_type} {self.content_id}"