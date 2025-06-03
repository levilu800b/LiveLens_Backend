#type: ignore

# authapp/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, EmailVerificationCode, UserActivity, UserPreferences

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'username', 'full_name', 'is_verified', 'is_admin_user', 
        'is_active', 'created_at', 'last_login'
    )
    list_filter = (
        'is_verified', 'is_admin_user', 'is_active', 'is_staff', 'is_superuser',
        'gender', 'created_at', 'last_login'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    
    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'phone_number', 'gender', 
                'country', 'date_of_birth', 'avatar'
            )
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'is_verified', 
                'is_admin_user', 'groups', 'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
        ('External Accounts', {
            'fields': ('google_id',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name', 
                'password1', 'password2', 'is_verified'
            ),
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
    
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.avatar.url
            )
        return "No Avatar"
    avatar_preview.short_description = 'Avatar'
    
    actions = ['make_admin', 'remove_admin', 'verify_users', 'deactivate_users']
    
    def make_admin(self, request, queryset):
        queryset.update(is_admin_user=True)
        self.message_user(request, f"{queryset.count()} users marked as admin.")
    make_admin.short_description = "Mark selected users as admin"
    
    def remove_admin(self, request, queryset):
        queryset.update(is_admin_user=False)
        self.message_user(request, f"{queryset.count()} users removed from admin.")
    remove_admin.short_description = "Remove admin privileges from selected users"
    
    def verify_users(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} users verified.")
    verify_users.short_description = "Verify selected users"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} users deactivated.")
    deactivate_users.short_description = "Deactivate selected users"

@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'code', 'code_type', 'is_used', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('code_type', 'is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'code')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def is_expired(self, obj):
        from django.utils import timezone
        expired = timezone.now() > obj.expires_at
        color = 'red' if expired else 'green'
        status = 'Expired' if expired else 'Valid'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            status
        )
    is_expired.short_description = 'Status'
    
    actions = ['mark_as_used']
    
    def mark_as_used(self, request, queryset):
        queryset.update(is_used=True)
        self.message_user(request, f"{queryset.count()} codes marked as used.")
    mark_as_used.short_description = "Mark selected codes as used"

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'activity_type', 'description', 'ip_address', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__email', 'description', 'ip_address')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of activities
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing activities

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 'email_notifications', 'push_notifications', 
        'auto_play_videos', 'preferred_video_quality', 'dark_mode'
    )
    list_filter = (
        'email_notifications', 'push_notifications', 'auto_play_videos',
        'preferred_video_quality', 'dark_mode'
    )
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

# Customize admin site
admin.site.site_header = "Streaming Platform Admin"
admin.site.site_title = "Streaming Platform"
admin.site.index_title = "Welcome to Streaming Platform Administration"