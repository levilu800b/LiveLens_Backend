# sneak_peeks/admin.py
# type: ignore

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from .models import (
    SneakPeek, SneakPeekView, SneakPeekInteraction, 
    SneakPeekPlaylist, SneakPeekPlaylistItem
)

@admin.register(SneakPeek)
class SneakPeekAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'category', 'status', 'is_featured', 'is_trending',
        'is_premium', 'view_count', 'like_count', 'duration_formatted',
        'video_quality', 'created_at'
    )
    list_filter = (
        'status', 'category', 'is_featured', 'is_trending', 'is_premium',
        'video_quality', 'content_rating', 'created_at', 'author'
    )
    search_fields = (
        'title', 'description', 'tags', 'author__username', 'author__email'
    )
    readonly_fields = (
        'id', 'slug', 'view_count', 'like_count', 'dislike_count',
        'share_count', 'comment_count', 'created_at', 'updated_at',
        'published_at', 'duration_formatted', 'file_size_formatted'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = ['publish_sneak_peeks', 'feature_sneak_peeks', 'unfeature_sneak_peeks']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description', 'short_description', 'status')
        }),
        ('Categorization', {
            'fields': ('category', 'tags', 'release_date', 'content_rating')
        }),
        ('Media Files', {
            'fields': ('video_file', 'thumbnail', 'poster')
        }),
        ('Video Properties', {
            'fields': ('duration', 'duration_formatted', 'video_quality', 'file_size', 'file_size_formatted')
        }),
        ('Visibility Settings', {
            'fields': ('is_featured', 'is_trending', 'is_premium')
        }),
        ('Interaction Stats', {
            'fields': ('view_count', 'like_count', 'dislike_count', 'share_count', 'comment_count')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Related Content', {
            'fields': ('related_content_type', 'related_content_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')
    
    def publish_sneak_peeks(self, request, queryset):
        updated = queryset.filter(status='draft').update(status='published')
        self.message_user(request, f"{updated} sneak peeks published successfully.")
    publish_sneak_peeks.short_description = "Publish selected sneak peeks"
    
    def feature_sneak_peeks(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} sneak peeks featured successfully.")
    feature_sneak_peeks.short_description = "Feature selected sneak peeks"
    
    def unfeature_sneak_peeks(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} sneak peeks unfeatured successfully.")
    unfeature_sneak_peeks.short_description = "Unfeature selected sneak peeks"


@admin.register(SneakPeekView)
class SneakPeekViewAdmin(admin.ModelAdmin):
    list_display = (
        'sneak_peek_title', 'user_display', 'device_type', 'watch_duration',
        'completion_percentage', 'viewed_at'
    )
    list_filter = ('device_type', 'viewed_at')
    search_fields = (
        'sneak_peek__title', 'user__username', 'ip_address'
    )
    readonly_fields = ('viewed_at',)
    ordering = ('-viewed_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sneak_peek', 'user')
    
    def sneak_peek_title(self, obj):
        return obj.sneak_peek.title
    sneak_peek_title.short_description = 'Sneak Peek'
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username}"
        return f"Anonymous ({obj.ip_address})"
    user_display.short_description = 'User'
    
    def has_add_permission(self, request):
        return False  # Views should only be created programmatically


@admin.register(SneakPeekInteraction)
class SneakPeekInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'sneak_peek_title', 'interaction_type', 'rating', 'created_at'
    )
    list_filter = ('interaction_type', 'created_at')
    search_fields = (
        'user__username', 'sneak_peek__title'
    )
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'sneak_peek')
    
    def user_display(self, obj):
        return f"{obj.user.username}"
    user_display.short_description = 'User'
    
    def sneak_peek_title(self, obj):
        return obj.sneak_peek.title
    sneak_peek_title.short_description = 'Sneak Peek'


@admin.register(SneakPeekPlaylist)
class SneakPeekPlaylistAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'creator_display', 'sneak_peek_count_display', 'is_public',
        'is_auto_play', 'created_at'
    )
    list_filter = ('is_public', 'is_auto_play', 'created_at')
    search_fields = ('name', 'description', 'creator__username')
    readonly_fields = (
        'created_at', 'updated_at', 'sneak_peek_count_display', 'total_duration_display'
    )
    # Removed filter_horizontal because sneak_peeks uses a custom through model
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('creator').annotate(
            sneak_peek_count=Count('sneak_peeks'),
            total_duration=Sum('sneak_peeks__duration')
        )
    
    def creator_display(self, obj):
        return f"{obj.creator.username}"
    creator_display.short_description = 'Creator'
    
    def sneak_peek_count_display(self, obj):
        return obj.sneak_peek_count
    sneak_peek_count_display.short_description = 'Sneak Peeks'
    
    def total_duration_display(self, obj):
        total_seconds = obj.total_duration or 0
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes}:{seconds:02d}"
    total_duration_display.short_description = 'Total Duration'


@admin.register(SneakPeekPlaylistItem)
class SneakPeekPlaylistItemAdmin(admin.ModelAdmin):
    list_display = ('playlist_name', 'sneak_peek_title', 'order', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('playlist__name', 'sneak_peek__title')
    readonly_fields = ('added_at',)
    ordering = ('playlist', 'order')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('playlist', 'sneak_peek')
    
    def playlist_name(self, obj):
        return obj.playlist.name
    playlist_name.short_description = 'Playlist'
    
    def sneak_peek_title(self, obj):
        return obj.sneak_peek.title
    sneak_peek_title.short_description = 'Sneak Peek'