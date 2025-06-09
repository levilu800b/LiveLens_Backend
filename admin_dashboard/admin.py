# admin_dashboard/admin.py
# type: ignore

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Avg
from .models import (
    DashboardStats, ContentAnalytics, UserActivity, 
    SystemAlert, ReportGeneration
)

@admin.register(DashboardStats)
class DashboardStatsAdmin(admin.ModelAdmin):
    list_display = (
        'metric_type', 'stat_type', 'value', 'percentage_change', 'date', 'created_at'
    )
    list_filter = ('metric_type', 'stat_type', 'date', 'created_at')
    search_fields = ('metric_type',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-date', 'metric_type')
    list_per_page = 50
    
    fieldsets = (
        ('Metric Information', {
            'fields': ('metric_type', 'stat_type', 'value', 'percentage_change')
        }),
        ('Time Period', {
            'fields': ('date', 'period_start', 'period_end')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContentAnalytics)
class ContentAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'content_title', 'content_type', 'views_count', 'likes_count',
        'comments_count', 'performance_score', 'trending_score', 'date'
    )
    list_filter = ('content_type', 'date', 'created_at')
    search_fields = ('content_title', 'content_id')
    readonly_fields = ('created_at', 'updated_at', 'performance_score')
    ordering = ('-date', '-performance_score')
    list_per_page = 25
    
    fieldsets = (
        ('Content Information', {
            'fields': ('content_type', 'content_id', 'content_title')
        }),
        ('View Metrics', {
            'fields': ('views_count', 'unique_views_count', 'average_watch_time', 'completion_rate')
        }),
        ('Engagement Metrics', {
            'fields': ('likes_count', 'dislikes_count', 'comments_count', 'shares_count', 'downloads_count')
        }),
        ('Performance', {
            'fields': ('performance_score', 'trending_score', 'bounce_rate', 'return_viewer_rate')
        }),
        ('Demographics', {
            'fields': ('top_countries', 'age_demographics', 'device_breakdown', 'traffic_sources'),
            'classes': ('collapse',)
        }),
        ('Time-based Data', {
            'fields': ('hourly_views', 'daily_views', 'weekly_views'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'activity_type', 'description_preview', 'device_type',
        'country', 'created_at'
    )
    list_filter = (
        'activity_type', 'device_type', 'browser', 'os', 'country', 'created_at'
    )
    search_fields = (
        'user__username', 'user__email', 'description', 'ip_address'
    )
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 50
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'activity_type', 'description')
        }),
        ('Content Reference', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Request Metadata', {
            'fields': ('ip_address', 'user_agent', 'referrer', 'device_type', 'browser', 'os')
        }),
        ('Location', {
            'fields': ('country', 'city'),
            'classes': ('collapse',)
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username}"
        return f"Anonymous ({obj.ip_address})"
    user_display.short_description = 'User'
    
    def description_preview(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_preview.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False  # Activities should only be created programmatically


@admin.register(SystemAlert)
class SystemAlertAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'alert_type', 'category', 'priority', 'is_read',
        'is_resolved', 'requires_action', 'created_at'
    )
    list_filter = (
        'alert_type', 'category', 'priority', 'is_read', 'is_resolved',
        'requires_action', 'created_at'
    )
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 25
    actions = ['mark_as_read', 'mark_as_resolved']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('title', 'message', 'alert_type', 'category')
        }),
        ('Status', {
            'fields': ('is_read', 'is_resolved', 'priority', 'requires_action')
        }),
        ('Resolution', {
            'fields': ('resolved_by', 'resolved_at', 'resolution_notes'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('email_sent', 'slack_sent', 'auto_dismiss_after'),
            'classes': ('collapse',)
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('resolved_by', 'content_type')
    
    def mark_as_read(self, request, queryset):
        count = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(request, f"{count} alerts marked as read.")
    mark_as_read.short_description = "Mark selected alerts as read"
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f"{count} alerts marked as resolved.")
    mark_as_resolved.short_description = "Mark selected alerts as resolved"


@admin.register(ReportGeneration)
class ReportGenerationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'report_type', 'report_format', 'requested_by_display',
        'status', 'file_size_display', 'download_count', 'created_at'
    )
    list_filter = ('report_type', 'report_format', 'status', 'created_at')
    search_fields = ('name', 'requested_by__username')
    readonly_fields = (
        'created_at', 'updated_at', 'processing_started_at',
        'processing_completed_at', 'processing_time', 'file_size',
        'download_count'
    )
    ordering = ('-created_at',)
    list_per_page = 25
    
    fieldsets = (
        ('Report Information', {
            'fields': ('name', 'report_type', 'report_format', 'requested_by')
        }),
        ('Date Range', {
            'fields': ('date_from', 'date_to')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('File Details', {
            'fields': ('file_path', 'file_size', 'download_count'),
            'classes': ('collapse',)
        }),
        ('Processing', {
            'fields': (
                'processing_started_at', 'processing_completed_at', 'processing_time'
            ),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('filters', 'include_fields'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('requested_by')
    
    def requested_by_display(self, obj):
        return obj.requested_by.username
    requested_by_display.short_description = 'Requested By'
    
    def file_size_display(self, obj):
        if not obj.file_size:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if obj.file_size < 1024.0:
                return f"{obj.file_size:.1f} {unit}"
            obj.file_size /= 1024.0
        return f"{obj.file_size:.1f} TB"
    file_size_display.short_description = 'File Size'
    
    def has_add_permission(self, request):
        return False  # Reports should only be created through API
