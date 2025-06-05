#type: ignore

# podcasts/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from django.db.models import Count, Sum
from .models import (
    PodcastSeries, Podcast, PodcastInteraction, PodcastView, 
    PodcastPlaylist, PodcastSubscription
)

@admin.register(PodcastSeries)
class PodcastSeriesAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'host', 'category', 'language', 'is_active',
        'is_featured', 'is_explicit', 'episode_count_display', 'subscriber_count_display',
        'created_at'
    )
    list_filter = (
        'category', 'language', 'is_active', 'is_featured', 'is_explicit',
        'created_at', 'author'
    )
    search_fields = (
        'title', 'description', 'host', 'tags', 'author__username', 'author__email'
    )
    readonly_fields = (
        'id', 'slug', 'episode_count_display', 'subscriber_count_display',
        'total_duration_display', 'created_at', 'updated_at'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'host', 'description', 'short_description')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategory', 'language', 'tags')
        }),
        ('Media', {
            'fields': ('cover_image', 'thumbnail', 'banner'),
            'classes': ('wide',)
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured', 'is_explicit')
        }),
        ('External Links', {
            'fields': ('website', 'rss_feed'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('episode_count_display', 'subscriber_count_display', 'total_duration_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Technical', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('author').annotate(
            episode_count=Count('episodes', filter=models.Q(episodes__status='published')),
            subscriber_count=Count('subscribers')
        )
    
    def episode_count_display(self, obj):
        return getattr(obj, 'episode_count', obj.episode_count)
    episode_count_display.short_description = 'Episodes'
    episode_count_display.admin_order_field = 'episode_count'
    
    def subscriber_count_display(self, obj):
        return getattr(obj, 'subscriber_count', obj.subscribers.count())
    subscriber_count_display.short_description = 'Subscribers'
    subscriber_count_display.admin_order_field = 'subscriber_count'
    
    def total_duration_display(self, obj):
        total_seconds = obj.total_duration
        if total_seconds:
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
    total_duration_display.short_description = 'Total Duration'
    
    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.cover_image.url
            )
        return "No cover"
    cover_image_preview.short_description = 'Cover'
    
    actions = [
        'make_featured', 'remove_featured', 'activate_series', 'deactivate_series'
    ]
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} series marked as featured.")
    make_featured.short_description = "Mark selected series as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} series removed from featured.")
    remove_featured.short_description = "Remove featured status from selected series"
    
    def activate_series(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} series activated.")
    activate_series.short_description = "Activate selected series"
    
    def deactivate_series(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} series deactivated.")
    deactivate_series.short_description = "Deactivate selected series"

@admin.register(Podcast)
class PodcastAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'series', 'season_episode_display', 'author', 'episode_type',
        'status', 'is_featured', 'is_premium', 'is_explicit', 'play_count',
        'like_count', 'average_rating', 'duration_formatted', 'published_at'
    )
    list_filter = (
        'status', 'episode_type', 'is_featured', 'is_premium', 'is_explicit',
        'audio_quality', 'season_number', 'series__category', 'published_at',
        'created_at', 'author'
    )
    search_fields = (
        'title', 'description', 'guest', 'tags', 'series__title',
        'author__username', 'author__email'
    )
    readonly_fields = (
        'id', 'slug', 'play_count', 'like_count', 'comment_count', 'download_count',
        'average_rating', 'rating_count', 'duration_formatted', 'file_size_formatted',
        'created_at', 'updated_at', 'published_at'
    )
    ordering = ('-published_at', '-created_at')
    date_hierarchy = 'published_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'series', 'author', 'description', 'summary', 'status')
        }),
        ('Episode Details', {
            'fields': ('episode_number', 'season_number', 'episode_type', 'guest', 'tags')
        }),
        ('Media Files', {
            'fields': ('audio_file', 'video_file', 'transcript_file', 'cover_image', 'thumbnail'),
            'classes': ('wide',)
        }),
        ('Audio Metadata', {
            'fields': (
                'duration', 'duration_formatted', 'file_size', 'file_size_formatted',
                'audio_quality'
            )
        }),
        ('Visibility & Features', {
            'fields': ('is_featured', 'is_premium', 'is_explicit')
        }),
        ('External', {
            'fields': ('external_url',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'play_count', 'like_count', 'comment_count', 'download_count',
                'average_rating', 'rating_count'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at', 'scheduled_at'),
            'classes': ('collapse',)
        }),
        ('Technical', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('author', 'series')
    
    def season_episode_display(self, obj):
        return f"S{obj.season_number}E{obj.episode_number}"
    season_episode_display.short_description = 'S/E'
    season_episode_display.admin_order_field = 'season_number'
    
    def audio_file_info(self, obj):
        if obj.audio_file:
            return format_html(
                '<a href="{}" target="_blank">Audio File</a><br>Size: {}',
                obj.audio_file.url,
                obj.file_size_formatted
            )
        return "No audio file"
    audio_file_info.short_description = 'Audio'
    
    def video_file_info(self, obj):
        if obj.video_file:
            return format_html(
                '<a href="{}" target="_blank">Video File</a>',
                obj.video_file.url
            )
        return "No video file"
    video_file_info.short_description = 'Video'
    
    actions = [
        'make_featured', 'remove_featured', 'make_premium', 'remove_premium',
        'publish_episodes', 'draft_episodes'
    ]
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} episodes marked as featured.")
    make_featured.short_description = "Mark selected episodes as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} episodes removed from featured.")
    remove_featured.short_description = "Remove featured status from selected episodes"
    
    def make_premium(self, request, queryset):
        queryset.update(is_premium=True)
        self.message_user(request, f"{queryset.count()} episodes marked as premium.")
    make_premium.short_description = "Mark selected episodes as premium"
    
    def remove_premium(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"{queryset.count()} episodes removed from premium.")
    remove_premium.short_description = "Remove premium status from selected episodes"
    
    def publish_episodes(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f"{updated} episodes published.")
    publish_episodes.short_description = "Publish selected draft episodes"
    
    def draft_episodes(self, request, queryset):
        updated = queryset.filter(status='published').update(status='draft')
        self.message_user(request, f"{updated} episodes moved to draft.")
    draft_episodes.short_description = "Move selected episodes to draft"

@admin.register(PodcastInteraction)
class PodcastInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'podcast_title', 'series_title', 'interaction_type',
        'listen_progress', 'rating', 'created_at'
    )
    list_filter = ('interaction_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'podcast__title', 'series__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def podcast_title(self, obj):
        return obj.podcast.title if obj.podcast else '-'
    podcast_title.short_description = 'Episode'
    
    def series_title(self, obj):
        return obj.series.title if obj.series else (obj.podcast.series.title if obj.podcast else '-')
    series_title.short_description = 'Series'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'podcast', 'series')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of interactions

@admin.register(PodcastView)
class PodcastViewAdmin(admin.ModelAdmin):
    list_display = (
        'podcast_title', 'user_display', 'ip_address', 'listen_duration_display',
        'completion_percentage', 'device_type', 'listened_at'
    )
    list_filter = ('device_type', 'listened_at')
    search_fields = ('podcast__title', 'user__username', 'ip_address')
    readonly_fields = ('listened_at',)
    ordering = ('-listened_at',)
    
    def podcast_title(self, obj):
        return obj.podcast.title
    podcast_title.short_description = 'Episode'
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username}"
        return f"Anonymous ({obj.ip_address})"
    user_display.short_description = 'User'
    
    def listen_duration_display(self, obj):
        if obj.listen_duration:
            minutes, seconds = divmod(obj.listen_duration, 60)
            return f"{minutes}m {seconds}s"
        return "0s"
    listen_duration_display.short_description = 'Listen Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'podcast')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of views
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing views

@admin.register(PodcastPlaylist)
class PodcastPlaylistAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'user_display', 'episode_count_display', 'is_public',
        'auto_play', 'shuffle', 'created_at'
    )
    list_filter = ('is_public', 'auto_play', 'shuffle', 'created_at', 'user')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'episode_count_display')
    filter_horizontal = ('episodes',)
    
    def user_display(self, obj):
        return f"{obj.user.username}"
    user_display.short_description = 'User'
    
    def episode_count_display(self, obj):
        return obj.episode_count
    episode_count_display.short_description = 'Episodes'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('episodes')

@admin.register(PodcastSubscription)
class PodcastSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'series_title', 'notifications_enabled',
        'auto_download', 'created_at'
    )
    list_filter = ('notifications_enabled', 'auto_download', 'created_at', 'series__category')
    search_fields = ('user__username', 'user__email', 'series__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def series_title(self, obj):
        return obj.series.title
    series_title.short_description = 'Series'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'series')

# Customize admin site headers
admin.site.site_header = "Streaming Platform - Podcasts Admin"
admin.site.site_title = "Podcasts Admin"
admin.site.index_title = "Podcasts Management"