#type: ignore
# authapp/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
import uuid
from datetime import datetime, timedelta

class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    # Override email to be unique and required
    email = models.EmailField(unique=True)
    
    # Additional profile fields
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Phone number must be valid')]
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Account status fields
    is_verified = models.BooleanField(default=False)
    is_admin_user = models.BooleanField(default=False)  # For admin dashboard access
    
    # Profile image
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_admin(self):
        return self.is_admin_user or self.is_superuser

class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'email_verifications'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(minutes=15)  # 15 minutes expiry
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return datetime.now() > self.expires_at
    
    def __str__(self):
        return f"Verification code for {self.user.email}"

class UserLibrary(models.Model):
    CONTENT_TYPES = [
        ('story', 'Story'),
        ('film', 'Film'),
        ('content', 'Content'),
        ('podcast', 'Podcast'),
        ('animation', 'Animation'),
        ('sneak_peek', 'Sneak Peek'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.PositiveIntegerField()  # Generic foreign key
    watched_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    watch_progress = models.FloatField(default=0.0)  # Percentage watched (0-100)
    
    class Meta:
        db_table = 'user_library'
        unique_together = ['user', 'content_type', 'content_id']
        ordering = ['-watched_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.content_type} {self.content_id}"

class UserFavorites(models.Model):
    CONTENT_TYPES = [
        ('story', 'Story'),
        ('film', 'Film'),
        ('content', 'Content'),
        ('podcast', 'Podcast'),
        ('animation', 'Animation'),
        ('sneak_peek', 'Sneak Peek'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.PositiveIntegerField()  # Generic foreign key
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_favorites'
        unique_together = ['user', 'content_type', 'content_id']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} favorited {self.content_type} {self.content_id}"

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    device_info = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.email} session"