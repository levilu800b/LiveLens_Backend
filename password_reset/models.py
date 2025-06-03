#type: ignore

# password_reset/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string

class PasswordResetRequest(models.Model):
    email = models.EmailField()
    reset_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.reset_code:
            self.reset_code = self.generate_code()
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
        return f"{self.email} - {self.reset_code}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Password Reset Request'
        verbose_name_plural = 'Password Reset Requests'