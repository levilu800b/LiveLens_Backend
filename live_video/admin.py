# live_video/admin.py
# type: ignore

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages

from .models import LiveVideo, LiveVideoInteraction, LiveVideoComment, LiveVideoSchedule


@admin.register(LiveVideo)
class LiveVideoAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'live_status', 'scheduled_start_time',
        'current_viewers', 'peak_viewers', 'total_views', 'like_count',
        'is_featured', 'is_premium', 'video_quality', 'created_at'
    )
    list_filter = (
        'live_status', 'is_featured', 'is_premium', 'video_quality',
        'allow_chat', 'allow_recording', 'scheduled_start_time',
        'created_at', 'author'
    )
    search_fields = (
        'title', 'description', 'host_name', 'guest_speakers',
        'tags', 'author__username', 'author__email'
    )
    readonly_fields = (
        'id', 'slug', 'actual_start_time', 'actual_end_time',
        'current_viewers', 'peak_viewers', 'total_views',
        'like_count', 'comment_count', 'stream_duration_display',
        'created_at', 'updated_at'
    )
    ordering = ('-scheduled_start_time',)
    date_hierarchy = 'scheduled_start_time'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'thumbnail')
        }),
        ('Live Stream Configuration', {
            'fields': (
                'live_status', 'scheduled_start_time', 'scheduled_end_time',
                'actual_start_time', 'actual_end_time', 'duration', 'video_quality'
            )
        }),
        ('Stream URLs & Technical', {
            'fields': (
                'live_stream_url', 'backup_stream_url', 'stream_key',
                'video_file', 'max_viewers'
            ),
            'classes': ('wide',)
        }),
        ('Content Details', {
            'fields': ('host_name', 'guest_speakers', 'tags')
        }),
        ('Settings', {
            'fields': (
                'is_featured', 'is_premium', 'allow_chat', 'allow_recording', 'auto_start'
            )
        }),
        ('Statistics', {
            'fields': (
                'current_viewers', 'peak_viewers', 'total_views',
                'like_count', 'comment_count', 'stream_duration_display'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Technical', {
            'fields': ('id', 'author'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('author')
    
    def stream_duration_display(self, obj):
        """Display stream duration if available"""
        duration = obj.stream_duration
        if duration:
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "Not available"
    stream_duration_display.short_description = 'Stream Duration'
    
    def save_model(self, request, obj, form, change):
        """Set author when creating new live video"""
        if not change:  # Only when creating
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    actions = [
        'make_featured', 'remove_featured', 'make_premium', 'remove_premium',
        'start_streams', 'end_streams', 'enable_chat', 'disable_chat'
    ]
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} live videos marked as featured.")
    make_featured.short_description = "Mark selected live videos as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} live videos removed from featured.")
    remove_featured.short_description = "Remove featured status from selected live videos"
    
    def make_premium(self, request, queryset):
        queryset.update(is_premium=True)
        self.message_user(request, f"{queryset.count()} live videos marked as premium.")
    make_premium.short_description = "Mark selected live videos as premium"
    
    def remove_premium(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"{queryset.count()} live videos removed from premium.")
    remove_premium.short_description = "Remove premium status from selected live videos"
    
    def start_streams(self, request, queryset):
        updated = 0
        for live_video in queryset.filter(live_status='scheduled'):
            live_video.start_stream()
            updated += 1
        self.message_user(request, f"{updated} live streams started.")
    start_streams.short_description = "Start selected scheduled streams"
    
    def end_streams(self, request, queryset):
        updated = 0
        for live_video in queryset.filter(live_status='live'):
            live_video.end_stream()
            updated += 1
        self.message_user(request, f"{updated} live streams ended.")
    end_streams.short_description = "End selected live streams"
    
    def enable_chat(self, request, queryset):
        queryset.update(allow_chat=True)
        self.message_user(request, f"{queryset.count()} live videos now allow chat.")
    enable_chat.short_description = "Enable chat for selected live videos"
    
    def disable_chat(self, request, queryset):
        queryset.update(allow_chat=False)
        self.message_user(request, f"{queryset.count()} live videos now have chat disabled.")
    disable_chat.short_description = "Disable chat for selected live videos"


@admin.register(LiveVideoInteraction)
class LiveVideoInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'live_video_title', 'interaction_type',
        'watch_duration_display', 'joined_at', 'left_at', 'created_at'
    )
    list_filter = ('interaction_type', 'created_at', 'joined_at')
    search_fields = (
        'user__username', 'user__email', 'live_video__title'
    )
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def live_video_title(self, obj):
        return obj.live_video.title[:50] + ('...' if len(obj.live_video.title) > 50 else '')
    live_video_title.short_description = 'Live Video'
    
    def watch_duration_display(self, obj):
        if obj.watch_duration:
            hours, remainder = divmod(obj.watch_duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "N/A"
    watch_duration_display.short_description = 'Watch Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'live_video')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of interactions


@admin.register(LiveVideoComment)
class LiveVideoCommentAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'live_video_title', 'message_preview',
        'is_moderator', 'is_hidden', 'stream_time_display', 'timestamp'
    )
    list_filter = (
        'is_moderator', 'is_hidden', 'timestamp', 'live_video'
    )
    search_fields = (
        'user__username', 'user__email', 'live_video__title', 'message'
    )
    readonly_fields = ('id', 'timestamp', 'stream_time')
    ordering = ('-timestamp',)
    
    def user_display(self, obj):
        return f"{obj.user.username}"
    user_display.short_description = 'User'
    
    def live_video_title(self, obj):
        return obj.live_video.title[:30] + ('...' if len(obj.live_video.title) > 30 else '')
    live_video_title.short_description = 'Live Video'
    
    def message_preview(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    message_preview.short_description = 'Message'
    
    def stream_time_display(self, obj):
        if obj.stream_time:
            hours, remainder = divmod(obj.stream_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "N/A"
    stream_time_display.short_description = 'Stream Time'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'live_video')
    
    actions = ['hide_comments', 'show_comments', 'make_moderator_comments']
    
    def hide_comments(self, request, queryset):
        queryset.update(is_hidden=True)
        self.message_user(request, f"{queryset.count()} comments hidden.")
    hide_comments.short_description = "Hide selected comments"
    
    def show_comments(self, request, queryset):
        queryset.update(is_hidden=False)
        self.message_user(request, f"{queryset.count()} comments made visible.")
    show_comments.short_description = "Show selected comments"
    
    def make_moderator_comments(self, request, queryset):
        queryset.update(is_moderator=True)
        self.message_user(request, f"{queryset.count()} comments marked as moderator messages.")
    make_moderator_comments.short_description = "Mark as moderator comments"


@admin.register(LiveVideoSchedule)
class LiveVideoScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'title_template', 'author', 'frequency', 'start_time',
        'duration_minutes', 'weekday_display', 'day_of_month',
        'is_active', 'next_scheduled_display', 'created_at'
    )
    list_filter = (
        'frequency', 'is_active', 'weekday', 'created_at', 'author'
    )
    search_fields = (
        'title_template', 'description_template', 'author__username'
    )
    readonly_fields = ('id', 'next_scheduled_display', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title_template', 'description_template')
        }),
        ('Schedule Configuration', {
            'fields': (
                'frequency', 'start_time', 'duration_minutes',
                'weekday', 'day_of_month'
            )
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Information', {
            'fields': ('next_scheduled_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Technical', {
            'fields': ('id', 'author'),
            'classes': ('collapse',)
        }),
    )
    
    def weekday_display(self, obj):
        if obj.weekday is not None:
            return obj.get_weekday_display()
        return "N/A"
    weekday_display.short_description = 'Weekday'
    
    def next_scheduled_display(self, obj):
        """Show when the next live video would be created"""
        from datetime import datetime, timedelta
        
        now = timezone.now()
        
        if obj.frequency == 'daily':
            next_date = now.date() + timedelta(days=1)
        elif obj.frequency == 'weekly' and obj.weekday is not None:
            days_ahead = obj.weekday - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date = now.date() + timedelta(days=days_ahead)
        elif obj.frequency == 'monthly' and obj.day_of_month is not None:
            if now.day < obj.day_of_month:
                next_date = now.date().replace(day=obj.day_of_month)
            else:
                if now.month == 12:
                    next_date = now.date().replace(year=now.year + 1, month=1, day=obj.day_of_month)
                else:
                    next_date = now.date().replace(month=now.month + 1, day=obj.day_of_month)
        else:
            return "N/A"
        
        next_datetime = timezone.make_aware(datetime.combine(next_date, obj.start_time))
        return next_datetime.strftime("%Y-%m-%d %H:%M:%S %Z")
    next_scheduled_display.short_description = 'Next Scheduled'
    
    def save_model(self, request, obj, form, change):
        """Set author when creating new schedule"""
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['create_live_videos', 'activate_schedules', 'deactivate_schedules']
    
    def create_live_videos(self, request, queryset):
        created = 0
        for schedule in queryset.filter(is_active=True):
            live_video = schedule.create_next_live_video()
            if live_video:
                created += 1
        
        self.message_user(request, f"{created} live videos created from schedules.")
    create_live_videos.short_description = "Create live videos from selected schedules"
    
    def activate_schedules(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} schedules activated.")
    activate_schedules.short_description = "Activate selected schedules"
    
    def deactivate_schedules(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} schedules deactivated.")
    deactivate_schedules.short_description = "Deactivate selected schedules"


# Customize admin site for live video
admin.site.site_header = "Streaming Platform Admin - Live Video Management"
admin.site.site_title = "Live Video Admin"
admin.site.index_title = "Live Video Administration"