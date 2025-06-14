# type: ignore

# animations/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from .models import (
    Animation, AnimationInteraction, AnimationView, AnimationCollection,
    AnimationPlaylist
)

@admin.register(Animation)
class AnimationAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'category', 'animation_type', 'status', 'is_featured',
        'is_trending', 'is_premium', 'view_count', 'like_count',
        'average_rating', 'duration_formatted', 'video_quality', 'frame_rate',
        'created_at'
    )
    list_filter = (
        'status', 'category', 'animation_type', 'is_featured', 'is_trending',
        'is_premium', 'video_quality', 'frame_rate',
        'is_series', 'created_at', 'author'
    )
    search_fields = (
        'title', 'description', 'director', 'animator', 'studio',
        'author__username', 'author__email', 'tags', 'series_name'
    )
    readonly_fields = (
        'id', 'slug', 'view_count', 'like_count', 'comment_count', 'download_count',
        'share_count', 'average_rating', 'rating_count', 'duration_formatted',
        'trailer_duration_formatted', 'file_size_formatted', 'resolution_formatted',
        'created_at', 'updated_at', 'published_at'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description', 'short_description', 'status')
        }),
        ('Categorization', {
            'fields': ('category', 'animation_type', 'tags', 'release_year', 'language')
        }),
        ('Media Files', {
            'fields': ('thumbnail', 'poster', 'banner', 'video_file', 'trailer_file'),
            'classes': ('wide',)
        }),
        ('Animation Files', {
            'fields': ('project_file', 'storyboard', 'concept_art'),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': (
                'duration', 'duration_formatted', 'trailer_duration', 'trailer_duration_formatted',
                'video_quality', 'frame_rate', 'file_size', 'file_size_formatted',
                'resolution_width', 'resolution_height', 'resolution_formatted',
                'subtitles_available'
            )
        }),
        ('Production Information', {
            'fields': (
                'animation_software', 'render_engine', 'production_time', 'director',
                'animator', 'voice_actors', 'music_composer', 'sound_designer', 'studio', 'budget'
            ),
            'classes': ('collapse',)
        }),
        ('Series Information', {
            'fields': ('is_series', 'series_name', 'episode_number', 'season_number'),
            'classes': ('collapse',)
        }),
        ('Visibility & Features', {
            'fields': ('is_featured', 'is_trending', 'is_premium')
        }),
        ('Statistics', {
            'fields': (
                'view_count', 'like_count', 'comment_count', 'download_count',
                'share_count', 'average_rating', 'rating_count'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
        ('Technical', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('author')
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.thumbnail.url
            )
        return "No thumbnail"
    thumbnail_preview.short_description = 'Thumbnail'
    
    def video_file_info(self, obj):
        if obj.video_file:
            return format_html(
                '<a href="{}" target="_blank">Video File</a><br>Size: {}',
                obj.video_file.url,
                obj.file_size_formatted
            )
        return "No video file"
    video_file_info.short_description = 'Video'
    
    def trailer_file_info(self, obj):
        if obj.trailer_file:
            return format_html(
                '<a href="{}" target="_blank">Trailer File</a><br>Duration: {}',
                obj.trailer_file.url,
                obj.trailer_duration_formatted
            )
        return "No trailer"
    trailer_file_info.short_description = 'Trailer'
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} animations marked as featured.")
    make_featured.short_description = "Mark selected animations as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} animations removed from featured.")
    remove_featured.short_description = "Remove featured status from selected animations"
    
    def make_trending(self, request, queryset):
        queryset.update(is_trending=True)
        self.message_user(request, f"{queryset.count()} animations marked as trending.")
    make_trending.short_description = "Mark selected animations as trending"
    
    def remove_trending(self, request, queryset):
        queryset.update(is_trending=False)
        self.message_user(request, f"{queryset.count()} animations removed from trending.")
    remove_trending.short_description = "Remove trending status from selected animations"
    
    def make_premium(self, request, queryset):
        queryset.update(is_premium=True)
        self.message_user(request, f"{queryset.count()} animations marked as premium.")
    make_premium.short_description = "Mark selected animations as premium"
    
    def remove_premium(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"{queryset.count()} animations removed from premium.")
    remove_premium.short_description = "Remove premium status from selected animations"
    
    def publish_animations(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f"{updated} animations published.")
    publish_animations.short_description = "Publish selected draft animations"
    
    def draft_animations(self, request, queryset):
        updated = queryset.filter(status='published').update(status='draft')
        self.message_user(request, f"{updated} animations moved to draft.")
    draft_animations.short_description = "Move selected animations to draft"

@admin.register(AnimationInteraction)
class AnimationInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'animation_title', 'interaction_type',
        'watch_progress', 'rating', 'created_at'
    )
    list_filter = ('interaction_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'animation__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def animation_title(self, obj):
        return obj.animation.title
    animation_title.short_description = 'Animation'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'animation')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of interactions

@admin.register(AnimationView)
class AnimationViewAdmin(admin.ModelAdmin):
    list_display = (
        'animation_title', 'user_display', 'ip_address',
        'watch_duration_display', 'completion_percentage', 'device_type', 'viewed_at'
    )
    list_filter = ('device_type', 'viewed_at')
    search_fields = ('animation__title', 'user__username', 'ip_address')
    readonly_fields = ('viewed_at',)
    ordering = ('-viewed_at',)
    
    def animation_title(self, obj):
        return obj.animation.title
    animation_title.short_description = 'Animation'
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username}"
        return f"Anonymous ({obj.ip_address})"
    user_display.short_description = 'User'
    
    def watch_duration_display(self, obj):
        if obj.watch_duration:
            minutes, seconds = divmod(obj.watch_duration, 60)
            return f"{minutes}m {seconds}s"
        return "0s"
    watch_duration_display.short_description = 'Watch Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'animation')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of views
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing views

@admin.register(AnimationCollection)
class AnimationCollectionAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'user_display', 'animation_count_display', 'is_public', 'created_at'
    )
    list_filter = ('is_public', 'created_at', 'user')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'animation_count_display')
    filter_horizontal = ('animations',)
    
    def user_display(self, obj):
        return f"{obj.user.username}"
    user_display.short_description = 'User'
    
    def animation_count_display(self, obj):
        return obj.animation_count
    animation_count_display.short_description = 'Animations'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('animations')

@admin.register(AnimationPlaylist)
class AnimationPlaylistAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'creator_display', 'animation_count_display', 'is_public',
        'is_auto_play', 'created_at'
    )
    list_filter = ('is_public', 'is_auto_play', 'created_at', 'creator')
    search_fields = ('name', 'description', 'creator__username')
    readonly_fields = ('created_at', 'updated_at', 'animation_count_display', 'total_duration_display')
    filter_horizontal = ('animations',)
    
    def creator_display(self, obj):
        return f"{obj.creator.username}"
    creator_display.short_description = 'Creator'
    
    def animation_count_display(self, obj):
        return obj.animation_count
    animation_count_display.short_description = 'Animations'
    
    def total_duration_display(self, obj):
        total_seconds = obj.total_duration
        if total_seconds:
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
    total_duration_display.short_description = 'Total Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('creator').prefetch_related('animations')

# Customize admin site headers
admin.site.site_header = "Streaming Platform - Animations Admin"
admin.site.site_title = "Animations Admin"
admin.site.index_title = "Animations Management"