#type: ignore

# media_content/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Film, Content, MediaInteraction, MediaView, MediaCollection, 
    Playlist, PlaylistItem
)

@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'category', 'status', 'is_featured', 'is_trending',
        'is_premium', 'view_count', 'like_count', 'average_rating', 'duration_formatted',
        'video_quality', 'release_year', 'mpaa_rating', 'created_at'
    )
    list_filter = (
        'status', 'category', 'is_featured', 'is_trending', 'is_premium',
        'video_quality', 'mpaa_rating', 'release_year', 'created_at', 'author'
    )
    search_fields = (
        'title', 'description', 'director', 'cast', 'studio', 
        'author__username', 'author__email', 'tags'
    )
    readonly_fields = (
        'id', 'slug', 'view_count', 'like_count', 'comment_count', 'download_count',
        'average_rating', 'rating_count', 'duration_formatted', 'trailer_duration_formatted',
        'file_size_formatted', 'created_at', 'updated_at', 'published_at'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description', 'short_description', 'status')
        }),
        ('Categorization', {
            'fields': ('category', 'tags', 'release_year', 'language', 'mpaa_rating')
        }),
        ('Media Files', {
            'fields': ('thumbnail', 'poster', 'banner', 'video_file', 'trailer_file'),
            'classes': ('wide',)
        }),
        ('Video Metadata', {
            'fields': (
                'duration', 'duration_formatted', 'trailer_duration', 'trailer_duration_formatted',
                'video_quality', 'file_size', 'file_size_formatted', 'subtitles_available'
            )
        }),
        ('Film Details', {
            'fields': ('director', 'cast', 'producer', 'studio', 'budget', 'box_office'),
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
                'average_rating', 'rating_count'
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
    
    actions = [
        'make_featured', 'remove_featured', 'make_trending', 'remove_trending',
        'make_premium', 'remove_premium', 'publish_films', 'draft_films'
    ]
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} films marked as featured.")
    make_featured.short_description = "Mark selected films as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} films removed from featured.")
    remove_featured.short_description = "Remove featured status from selected films"
    
    def make_trending(self, request, queryset):
        queryset.update(is_trending=True)
        self.message_user(request, f"{queryset.count()} films marked as trending.")
    make_trending.short_description = "Mark selected films as trending"
    
    def remove_trending(self, request, queryset):
        queryset.update(is_trending=False)
        self.message_user(request, f"{queryset.count()} films removed from trending.")
    remove_trending.short_description = "Remove trending status from selected films"
    
    def make_premium(self, request, queryset):
        queryset.update(is_premium=True)
        self.message_user(request, f"{queryset.count()} films marked as premium.")
    make_premium.short_description = "Mark selected films as premium"
    
    def remove_premium(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"{queryset.count()} films removed from premium.")
    remove_premium.short_description = "Remove premium status from selected films"
    
    def publish_films(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f"{updated} films published.")
    publish_films.short_description = "Publish selected draft films"
    
    def draft_films(self, request, queryset):
        updated = queryset.filter(status='published').update(status='draft')
        self.message_user(request, f"{updated} films moved to draft.")
    draft_films.short_description = "Move selected films to draft"

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'category', 'content_type', 'status', 'is_featured',
        'is_trending', 'is_premium', 'is_live', 'view_count', 'like_count',
        'average_rating', 'duration_formatted', 'video_quality', 'created_at'
    )
    list_filter = (
        'status', 'category', 'content_type', 'is_featured', 'is_trending',
        'is_premium', 'is_live', 'video_quality', 'difficulty_level',
        'created_at', 'author'
    )
    search_fields = (
        'title', 'description', 'creator', 'series_name',
        'author__username', 'author__email', 'tags'
    )
    readonly_fields = (
        'id', 'slug', 'view_count', 'like_count', 'comment_count', 'download_count',
        'average_rating', 'rating_count', 'duration_formatted', 'trailer_duration_formatted',
        'file_size_formatted', 'created_at', 'updated_at', 'published_at'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description', 'short_description', 'status')
        }),
        ('Categorization', {
            'fields': ('category', 'content_type', 'tags', 'release_year', 'language', 'difficulty_level')
        }),
        ('Media Files', {
            'fields': ('thumbnail', 'poster', 'banner', 'video_file', 'trailer_file'),
            'classes': ('wide',)
        }),
        ('Video Metadata', {
            'fields': (
                'duration', 'duration_formatted', 'trailer_duration', 'trailer_duration_formatted',
                'video_quality', 'file_size', 'file_size_formatted', 'subtitles_available'
            )
        }),
        ('Content Details', {
            'fields': ('creator', 'series_name', 'episode_number'),
            'classes': ('collapse',)
        }),
        ('Live Streaming', {
            'fields': ('is_live', 'scheduled_live_time', 'live_stream_url'),
            'classes': ('collapse',)
        }),
        ('Visibility & Features', {
            'fields': ('is_featured', 'is_trending', 'is_premium')
        }),
        ('Statistics', {
            'fields': (
                'view_count', 'like_count', 'comment_count', 'download_count',
                'average_rating', 'rating_count'
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
    
    actions = [
        'make_featured', 'remove_featured', 'make_trending', 'remove_trending',
        'make_premium', 'remove_premium', 'publish_content', 'draft_content'
    ]
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} content marked as featured.")
    make_featured.short_description = "Mark selected content as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} content removed from featured.")
    remove_featured.short_description = "Remove featured status from selected content"
    
    def make_trending(self, request, queryset):
        queryset.update(is_trending=True)
        self.message_user(request, f"{queryset.count()} content marked as trending.")
    make_trending.short_description = "Mark selected content as trending"
    
    def remove_trending(self, request, queryset):
        queryset.update(is_trending=False)
        self.message_user(request, f"{queryset.count()} content removed from trending.")
    remove_trending.short_description = "Remove trending status from selected content"
    
    def make_premium(self, request, queryset):
        queryset.update(is_premium=True)
        self.message_user(request, f"{queryset.count()} content marked as premium.")
    make_premium.short_description = "Mark selected content as premium"
    
    def remove_premium(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"{queryset.count()} content removed from premium.")
    remove_premium.short_description = "Remove premium status from selected content"
    
    def publish_content(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f"{updated} content published.")
    publish_content.short_description = "Publish selected draft content"
    
    def draft_content(self, request, queryset):
        updated = queryset.filter(status='published').update(status='draft')
        self.message_user(request, f"{updated} content moved to draft.")
    draft_content.short_description = "Move selected content to draft"

@admin.register(MediaInteraction)
class MediaInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'content_type', 'object_id_short', 'interaction_type',
        'watch_progress', 'rating', 'created_at'
    )
    list_filter = ('interaction_type', 'content_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'object_id')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def object_id_short(self, obj):
        return str(obj.object_id)[:8] + '...'
    object_id_short.short_description = 'Object ID'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of interactions

@admin.register(MediaView)
class MediaViewAdmin(admin.ModelAdmin):
    list_display = (
        'content_type', 'object_id_short', 'user_display', 'ip_address',
        'watch_duration_display', 'completion_percentage', 'device_type', 'viewed_at'
    )
    list_filter = ('content_type', 'device_type', 'viewed_at')
    search_fields = ('object_id', 'user__username', 'ip_address')
    readonly_fields = ('viewed_at',)
    ordering = ('-viewed_at',)
    
    def object_id_short(self, obj):
        return str(obj.object_id)[:8] + '...'
    object_id_short.short_description = 'Object ID'
    
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
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of views
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing views

@admin.register(MediaCollection)
class MediaCollectionAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'user_display', 'total_items_display', 'is_public', 'created_at'
    )
    list_filter = ('is_public', 'created_at', 'user')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'total_items_display')
    filter_horizontal = ('films', 'content')
    
    def user_display(self, obj):
        return f"{obj.user.username}"
    user_display.short_description = 'User'
    
    def total_items_display(self, obj):
        return obj.total_items
    total_items_display.short_description = 'Total Items'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('films', 'content')

class PlaylistItemInline(admin.TabularInline):
    """Inline admin for playlist items"""
    model = PlaylistItem
    extra = 0
    fields = ('content_type', 'object_id', 'order')
    ordering = ['order']

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'creator_display', 'total_items_display', 'is_public', 
        'is_auto_play', 'created_at'
    )
    list_filter = ('is_public', 'is_auto_play', 'created_at', 'creator')
    search_fields = ('name', 'description', 'creator__username')
    readonly_fields = ('created_at', 'updated_at', 'total_items_display')
    inlines = [PlaylistItemInline]
    
    def creator_display(self, obj):
        return f"{obj.creator.username}"
    creator_display.short_description = 'Creator'
    
    def total_items_display(self, obj):
        return obj.items.count()
    total_items_display.short_description = 'Items'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('creator').prefetch_related('items')

@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = (
        'playlist_name', 'content_type', 'object_id_short', 'order', 'created_at'
    )
    list_filter = ('content_type', 'created_at', 'playlist')
    search_fields = ('playlist__name', 'object_id')
    readonly_fields = ('created_at',)
    ordering = ('playlist', 'order')
    
    def playlist_name(self, obj):
        return obj.playlist.name
    playlist_name.short_description = 'Playlist'
    
    def object_id_short(self, obj):
        return str(obj.object_id)[:8] + '...'
    object_id_short.short_description = 'Object ID'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('playlist')

# Customize admin site headers
admin.site.site_header = "Streaming Platform - Media Admin"
admin.site.site_title = "Media Admin"
admin.site.index_title = "Media Management"