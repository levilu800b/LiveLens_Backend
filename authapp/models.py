#type: ignore
# authapp/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
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
    is_verified = models.BooleanField(default=False)
    is_admin_user = models.BooleanField(default=False)  # For admin privileges
    google_id = models.CharField(max_length=100, blank=True, null=True)  # For Google OAuth
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.is_superuser or self.is_admin_user

class EmailVerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    code_type = models.CharField(max_length=20, choices=[
        ('verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)  # 30 minutes expiry
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        self.is_used = True
        self.save()
    
    def __str__(self):
        return f"{self.user.email} - {self.code} ({self.code_type})"

class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('signup', 'Signup'),
        ('profile_update', 'Profile Update'),
        ('password_change', 'Password Change'),
        ('content_view', 'Content View'),
        ('content_like', 'Content Like'),
        ('comment_add', 'Comment Add'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    extra_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'User Activities'
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} at {self.timestamp}"

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    auto_play_videos = models.BooleanField(default=True)
    preferred_video_quality = models.CharField(
        max_length=10,
        choices=[
            ('360p', '360p'),
            ('480p', '480p'),
            ('720p', '720p'),
            ('1080p', '1080p'),
            ('auto', 'Auto'),
        ],
        default='auto'
    )
    preferred_language = models.CharField(max_length=10, default='en')
    dark_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - Preferences"