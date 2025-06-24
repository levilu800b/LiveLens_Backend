# email_notifications/admin.py
# type: ignore

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from .models import NewsletterSubscription, EmailNotification, EmailTemplate

@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'user_display', 'is_active', 'is_verified', 
        'subscription_source', 'subscribed_at', 'preferences_display'
    ]
    list_filter = [
        'is_active', 'is_verified', 'subscription_source',
        'content_uploads', 'live_videos', 'weekly_digest', 'monthly_newsletter',
        'subscribed_at'
    ]
    search_fields = ['email', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'subscribed_at', 'updated_at', 'verified_at', 'unsubscribed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'email', 'user', 'is_active', 'is_verified')
        }),
        ('Subscription Preferences', {
            'fields': ('content_uploads', 'live_videos', 'weekly_digest', 'monthly_newsletter')
        }),
        ('Metadata', {
            'fields': ('subscription_source', 'verification_token', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'updated_at', 'verified_at', 'unsubscribed_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_display(self, obj):
        if obj.user:
            try:
                return format_html(
                    '<a href="{}">{}</a>',
                    reverse('admin:authapp_user_change', args=[obj.user.id]),
                    obj.user.get_full_name() or obj.user.username
                )
            except:
                return obj.user.get_full_name() or obj.user.username
        return 'No user linked'
    user_display.short_description = 'User'
    
    def preferences_display(self, obj):
        prefs = []
        if obj.content_uploads:
            prefs.append('📱 Content')
        if obj.live_videos:
            prefs.append('🔴 Live')
        if obj.weekly_digest:
            prefs.append('📬 Weekly')
        if obj.monthly_newsletter:
            prefs.append('📧 Monthly')
        return ' | '.join(prefs) if prefs else 'None'
    preferences_display.short_description = 'Preferences'
    
    actions = ['mark_as_verified', 'mark_as_unverified', 'unsubscribe_selected']
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True, verified_at=timezone.now())
        self.message_user(request, f'{updated} subscriptions marked as verified.')
    mark_as_verified.short_description = 'Mark selected as verified'
    
    def mark_as_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False, verified_at=None)
        self.message_user(request, f'{updated} subscriptions marked as unverified.')
    mark_as_unverified.short_description = 'Mark selected as unverified'
    
    def unsubscribe_selected(self, request, queryset):
        updated = 0
        for subscription in queryset:
            subscription.unsubscribe()
            updated += 1
        self.message_user(request, f'{updated} subscriptions unsubscribed.')
    unsubscribe_selected.short_description = 'Unsubscribe selected'

@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'notification_type', 'recipient_email', 'recipient_user_display',
        'status', 'created_at', 'sent_at', 'retry_count'
    ]
    list_filter = [
        'notification_type', 'status', 'created_at', 'sent_at',
        'retry_count'
    ]
    search_fields = [
        'recipient_email', 'recipient_user__username', 
        'recipient_user__first_name', 'recipient_user__last_name',
        'subject'
    ]
    readonly_fields = [
        'id', 'created_at', 'sent_at', 'opened_at', 'clicked_at',
        'content_object_display'
    ]
    
    fieldsets = (
        ('Email Details', {
            'fields': ('notification_type', 'recipient_email', 'recipient_user', 'subject', 'status')
        }),
        ('Content Reference', {
            'fields': ('content_type', 'object_id', 'content_object_display'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('created_at', 'sent_at', 'opened_at', 'clicked_at'),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        })
    )
    
    def recipient_user_display(self, obj):
        if obj.recipient_user:
            try:
                return format_html(
                    '<a href="{}">{}</a>',
                    reverse('admin:authapp_user_change', args=[obj.recipient_user.id]),
                    obj.recipient_user.get_full_name() or obj.recipient_user.username
                )
            except:
                return obj.recipient_user.get_full_name() or obj.recipient_user.username
        return 'No user'
    recipient_user_display.short_description = 'User'
    
    def content_object_display(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return 'No content linked'
    content_object_display.short_description = 'Content'
    
    actions = ['mark_as_sent', 'mark_as_failed', 'retry_failed']
    
    def mark_as_sent(self, request, queryset):
        updated = 0
        for notification in queryset:
            notification.mark_as_sent()
            updated += 1
        self.message_user(request, f'{updated} notifications marked as sent.')
    mark_as_sent.short_description = 'Mark selected as sent'
    
    def mark_as_failed(self, request, queryset):
        updated = 0
        for notification in queryset:
            notification.mark_as_failed("Manually marked as failed")
            updated += 1
        self.message_user(request, f'{updated} notifications marked as failed.')
    mark_as_failed.short_description = 'Mark selected as failed'
    
    def retry_failed(self, request, queryset):
        failed_notifications = queryset.filter(status='failed')
        updated = failed_notifications.update(status='pending', error_message='')
        self.message_user(request, f'{updated} failed notifications queued for retry.')
    retry_failed.short_description = 'Retry failed notifications'

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'is_active', 'is_default',
        'created_at', 'created_by_display', 'variables_count'
    ]
    list_filter = ['template_type', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'subject', 'template_type']
    readonly_fields = ['id', 'created_at', 'updated_at', 'variables_count']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'subject', 'is_active', 'is_default')
        }),
        ('Template Content', {
            'fields': ('html_content', 'text_content')
        }),
        ('Variables', {
            'fields': ('variables', 'variables_count'),
            'description': 'Available template variables for dynamic content'
        }),
        ('Metadata', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def created_by_display(self, obj):
        if obj.created_by:
            try:
                return format_html(
                    '<a href="{}">{}</a>',
                    reverse('admin:authapp_user_change', args=[obj.created_by.id]),
                    obj.created_by.get_full_name() or obj.created_by.username
                )
            except:
                return obj.created_by.get_full_name() or obj.created_by.username
        return 'System'
    created_by_display.short_description = 'Created By'
    
    def variables_count(self, obj):
        return len(obj.variables) if obj.variables else 0
    variables_count.short_description = 'Variables Count'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)