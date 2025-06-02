#type: ignore

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, EmailVerification, UserLibrary, UserFavorites, UserSession

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'full_name', 'username', 'is_verified', 
        'is_admin_user', 'is_active', 'created_at'
    ]
    list_filter = [
        'is_verified', 'is_admin_user', 'is_active', 'is_staff', 
        'gender', 'country', 'created_at'
    ]
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone_number']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('phone_number', 'gender', 'country', 'date_of_birth', 'avatar')
        }),
        ('Account Status', {
            'fields': ('is_verified', 'is_admin_user')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related()

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'created_at', 'expires_at', 'is_used', 'status_badge']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'code']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def status_badge(self, obj):
        if obj.is_used:
            return format_html('<span style="color: green;">✓ Used</span>')
        elif obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    status_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(UserLibrary)
class UserLibraryAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'content_type', 'content_id', 'is_completed', 
        'watch_progress', 'watched_at'
    ]
    list_filter = ['content_type', 'is_completed', 'watched_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering = ['-watched_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(UserFavorites)
class UserFavoritesAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'content_id', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'session_key', 'ip_address', 'is_active', 
        'created_at', 'last_activity'
    ]
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['user__email', 'session_key', 'ip_address']
    readonly_fields = ['session_key', 'created_at', 'last_activity']
    ordering = ['-last_activity']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')