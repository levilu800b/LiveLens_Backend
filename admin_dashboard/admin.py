# ===================================================================
# admin_dashboard/admin.py
# type: ignore

from django.contrib import admin
from .models import AdminActivity, PlatformStatistics, ContentModerationQueue

@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ('admin_username', 'activity_type', 'description_short', 'content_type_name', 'timestamp')
    list_filter = ('activity_type', 'timestamp', 'admin')
    search_fields = ('admin__username', 'description', 'admin__email')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    def admin_username(self, obj):
        return obj.admin.username
    admin_username.short_description = 'Admin'
    
    def description_short(self, obj):
        return obj.description[:50] + ('...' if len(obj.description) > 50 else '')
    description_short.short_description = 'Description'
    
    def content_type_name(self, obj):
        return obj.content_type.name if obj.content_type else 'N/A'
    content_type_name.short_description = 'Content Type'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing


@admin.register(PlatformStatistics)
class PlatformStatisticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_users', 'new_users_today', 'total_all_content', 'total_comments', 'created_at')
    list_filter = ('date', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-date',)
    date_hierarchy = 'date'
    
    def total_all_content(self, obj):
        return (obj.total_stories + obj.total_films + obj.total_content + 
                obj.total_podcasts + obj.total_animations + obj.total_sneak_peeks + 
                obj.total_live_videos)
    total_all_content.short_description = 'Total Content'


@admin.register(ContentModerationQueue)
class ContentModerationQueueAdmin(admin.ModelAdmin):
    list_display = ('content_type_name', 'object_id_short', 'submitted_by_username', 'status', 'priority', 'submitted_at')
    list_filter = ('status', 'priority', 'submitted_at', 'content_type')
    search_fields = ('submitted_by__username', 'reason', 'review_notes')
    readonly_fields = ('submitted_at', 'reviewed_at')
    ordering = ('-priority', '-submitted_at')
    
    def content_type_name(self, obj):
        return obj.content_type.name
    content_type_name.short_description = 'Content Type'
    
    def object_id_short(self, obj):
        return str(obj.object_id)
    object_id_short.short_description = 'Object ID'
    
    def submitted_by_username(self, obj):
        return obj.submitted_by.username
    submitted_by_username.short_description = 'Submitted By'


# Customize admin site headers
admin.site.site_header = "Streaming Platform - Admin Dashboard"
admin.site.site_title = "Admin Dashboard"
admin.site.index_title = "Administrative Dashboard"