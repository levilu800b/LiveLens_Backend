#type: ignore

# password_reset/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import PasswordResetRequest

@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = (
        'email', 'reset_code', 'created_at', 'expires_at', 
        'is_used', 'is_expired', 'ip_address'
    )
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'reset_code', 'ip_address')
    readonly_fields = ('created_at', 'reset_code')
    ordering = ('-created_at',)
    
    def is_expired(self, obj):
        expired = timezone.now() > obj.expires_at
        color = 'red' if expired else 'green'
        status = 'Expired' if expired else 'Valid'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    is_expired.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing
    
    actions = ['mark_as_used']
    
    def mark_as_used(self, request, queryset):
        queryset.update(is_used=True)
        self.message_user(request, f"{queryset.count()} reset requests marked as used.")
    mark_as_used.short_description = "Mark selected requests as used"