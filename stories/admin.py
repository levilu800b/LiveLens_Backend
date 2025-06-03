#type: ignore

# stories/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import Story, StoryPage, StoryInteraction, StoryView, StoryCollection

class StoryPageInline(admin.TabularInline):
    """Inline admin for story pages"""
    model = StoryPage
    extra = 0
    fields = ('page_number', 'title', 'content_preview', 'page_image', 'word_count')
    readonly_fields = ('word_count', 'content_preview')
    ordering = ['page_number']
    
    def content_preview(self, obj):
        if obj.content:
            return obj.content[:100] + ('...' if len(obj.content) > 100 else '')
        return "No content"
    content_preview.short_description = "Content Preview"

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'category', 'status', 'is_featured', 'is_trending',
        'read_count', 'like_count', 'comment_count', 'estimated_read_time',
        'created_at', 'published_at'
    )
    list_filter = (
        'status', 'category', 'is_featured', 'is_trending', 'created_at', 
        'published_at', 'author'
    )
    search_fields = ('title', 'description', 'content', 'author__username', 'author__email')
    readonly_fields = (
        'id', 'slug', 'read_count', 'like_count', 'comment_count', 
        'excerpt', 'estimated_read_time', 'created_at', 'updated_at', 'published_at'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description', 'status')
        }),
        ('Content', {
            'fields': ('content', 'excerpt', 'estimated_read_time'),
            'classes': ('wide',)
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Media', {
            'fields': ('thumbnail', 'cover_image')
        }),
        ('Visibility & Features', {
            'fields': ('is_featured', 'is_trending')
        }),
        ('Statistics', {
            'fields': ('read_count', 'like_count', 'comment_count'),
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
    
    inlines = [StoryPageInline]
    
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).select_related('author').annotate(
            total_interactions=Count('storyinteraction')
        )
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.thumbnail.url
            )
        return "No thumbnail"
    thumbnail_preview.short_description = 'Thumbnail'
    
    def view_story_link(self, obj):
        if obj.status == 'published':
            url = reverse('stories:story-detail', kwargs={'pk': obj.pk})
            return format_html('<a href="{}" target="_blank">View Story</a>', url)
        return "Not published"
    view_story_link.short_description = 'View'
    
    actions = ['make_featured', 'remove_featured', 'make_trending', 'remove_trending', 'publish_stories', 'draft_stories']
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} stories marked as featured.")
    make_featured.short_description = "Mark selected stories as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} stories removed from featured.")
    remove_featured.short_description = "Remove featured status from selected stories"
    
    def make_trending(self, request, queryset):
        queryset.update(is_trending=True)
        self.message_user(request, f"{queryset.count()} stories marked as trending.")
    make_trending.short_description = "Mark selected stories as trending"
    
    def remove_trending(self, request, queryset):
        queryset.update(is_trending=False)
        self.message_user(request, f"{queryset.count()} stories removed from trending.")
    remove_trending.short_description = "Remove trending status from selected stories"
    
    def publish_stories(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f"{updated} stories published.")
    publish_stories.short_description = "Publish selected draft stories"
    
    def draft_stories(self, request, queryset):
        updated = queryset.filter(status='published').update(status='draft')
        self.message_user(request, f"{updated} stories moved to draft.")
    draft_stories.short_description = "Move selected stories to draft"

@admin.register(StoryPage)
class StoryPageAdmin(admin.ModelAdmin):
    list_display = ('story_title', 'page_number', 'title', 'word_count', 'created_at')
    list_filter = ('story__category', 'story__status', 'created_at')
    search_fields = ('story__title', 'title', 'content')
    ordering = ('story', 'page_number')
    readonly_fields = ('word_count', 'created_at', 'updated_at')
    
    def story_title(self, obj):
        return obj.story.title
    story_title.short_description = 'Story'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('story')

@admin.register(StoryInteraction)
class StoryInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'story_title', 'interaction_type', 
        'reading_progress', 'last_page_read', 'created_at'
    )
    list_filter = ('interaction_type', 'created_at', 'story__category')
    search_fields = ('user__username', 'user__email', 'story__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def story_title(self, obj):
        return obj.story.title
    story_title.short_description = 'Story'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'story')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of interactions

@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = (
        'story_title', 'user_display', 'ip_address', 
        'time_spent_display', 'pages_viewed_count', 'viewed_at'
    )
    list_filter = ('viewed_at', 'story__category')
    search_fields = ('story__title', 'user__username', 'ip_address')
    readonly_fields = ('viewed_at',)
    ordering = ('-viewed_at',)
    
    def story_title(self, obj):
        return obj.story.title
    story_title.short_description = 'Story'
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username}"
        return f"Anonymous ({obj.ip_address})"
    user_display.short_description = 'User'
    
    def time_spent_display(self, obj):
        if obj.time_spent:
            minutes, seconds = divmod(obj.time_spent, 60)
            return f"{minutes}m {seconds}s"
        return "0s"
    time_spent_display.short_description = 'Time Spent'
    
    def pages_viewed_count(self, obj):
        return len(obj.pages_viewed) if obj.pages_viewed else 0
    pages_viewed_count.short_description = 'Pages Viewed'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'story')
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of views
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing views

@admin.register(StoryCollection)
class StoryCollectionAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'user_display', 'story_count_display', 
        'is_public', 'created_at'
    )
    list_filter = ('is_public', 'created_at', 'user')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'story_count_display')
    filter_horizontal = ('stories',)
    
    def user_display(self, obj):
        return f"{obj.user.username}"
    user_display.short_description = 'User'
    
    def story_count_display(self, obj):
        return obj.story_count
    story_count_display.short_description = 'Stories'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('stories')

# Customize admin site headers
admin.site.site_header = "Streaming Platform - Stories Admin"
admin.site.site_title = "Stories Admin"
admin.site.index_title = "Stories Management"