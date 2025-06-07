# comments/admin.py
# type: ignore

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from .models import Comment, CommentInteraction, CommentModerationLog, CommentNotification
from .utils import bulk_moderate_comments

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_display', 'content_title', 'text_preview', 'status',
        'like_count', 'dislike_count', 'reply_count', 'is_flagged', 
        'is_edited', 'created_at'
    )
    list_filter = (
        'status', 'is_flagged', 'is_edited', 'created_at', 'content_type'
    )
    search_fields = (
        'text', 'user__username', 'user__email', 'user__first_name', 'user__last_name'
    )
    readonly_fields = (
        'id', 'like_count', 'dislike_count', 'reply_count', 'created_at', 
        'updated_at', 'edited_at', 'content_type', 'object_id', 'ip_address',
        'user_agent', 'flagged_at', 'moderated_at'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    actions = ['approve_comments', 'hide_comments', 'delete_comments', 'unflag_comments']
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('id', 'user', 'text', 'parent', 'status')
        }),
        ('Content Reference', {
            'fields': ('content_type', 'object_id')
        }),
        ('Interaction Stats', {
            'fields': ('like_count', 'dislike_count', 'reply_count')
        }),
        ('Moderation', {
            'fields': (
                'is_flagged', 'flagged_at', 'moderated_by', 'moderated_at', 
                'moderation_reason'
            )
        }),
        ('Metadata', {
            'fields': (
                'is_edited', 'edited_at', 'ip_address', 'user_agent',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'content_type', 'parent', 'moderated_by'
        ).annotate(
            interaction_count=Count('interactions')
        )
    
    def user_display(self, obj):
        if obj.user:
            url = reverse('admin:authapp_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "Unknown User"
    user_display.short_description = 'User'
    
    def content_title(self, obj):
        if obj.content_object:
            title = getattr(obj.content_object, 'title', str(obj.content_object))
            return title[:50] + '...' if len(title) > 50 else title
        return "Unknown Content"
    content_title.short_description = 'Content'
    
    def text_preview(self, obj):
        preview = obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
        if obj.status == 'deleted':
            return format_html('<span style="color: red;">[DELETED] {}</span>', preview)
        elif obj.status == 'hidden':
            return format_html('<span style="color: orange;">[HIDDEN] {}</span>', preview)
        elif obj.is_flagged:
            return format_html('<span style="color: red;">[FLAGGED] {}</span>', preview)
        return preview
    text_preview.short_description = 'Text'
    
    def approve_comments(self, request, queryset):
        """Bulk approve comments"""
        comment_ids = list(queryset.values_list('id', flat=True))
        count = bulk_moderate_comments(comment_ids, 'approve', request.user, 'Bulk approved by admin')
        self.message_user(request, f"{count} comments approved successfully.")
    approve_comments.short_description = "Approve selected comments"
    
    def hide_comments(self, request, queryset):
        """Bulk hide comments"""
        comment_ids = list(queryset.values_list('id', flat=True))
        count = bulk_moderate_comments(comment_ids, 'hide', request.user, 'Bulk hidden by admin')
        self.message_user(request, f"{count} comments hidden successfully.")
    hide_comments.short_description = "Hide selected comments"
    
    def delete_comments(self, request, queryset):
        """Bulk delete comments"""
        comment_ids = list(queryset.values_list('id', flat=True))
        count = bulk_moderate_comments(comment_ids, 'delete', request.user, 'Bulk deleted by admin')
        self.message_user(request, f"{count} comments deleted successfully.")
    delete_comments.short_description = "Delete selected comments"
    
    def unflag_comments(self, request, queryset):
        """Bulk unflag comments"""
        count = queryset.filter(is_flagged=True).update(
            is_flagged=False,
            flagged_at=None,
            moderated_by=request.user,
            moderated_at=timezone.now(),
            moderation_reason='Bulk unflagged by admin'
        )
        self.message_user(request, f"{count} comments unflagged successfully.")
    unflag_comments.short_description = "Unflag selected comments"


@admin.register(CommentInteraction)
class CommentInteractionAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'comment_preview', 'interaction_type', 'created_at'
    )
    list_filter = ('interaction_type', 'created_at')
    search_fields = (
        'user__username', 'comment__text', 'report_reason'
    )
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'comment__user')
    
    def user_display(self, obj):
        return f"{obj.user.username} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def comment_preview(self, obj):
        preview = obj.comment.text[:50] + '...' if len(obj.comment.text) > 50 else obj.comment.text
        return format_html(
            '<span title="{}">by {} - {}</span>',
            obj.comment.text,
            obj.comment.user.username,
            preview
        )
    comment_preview.short_description = 'Comment'


@admin.register(CommentModerationLog)
class CommentModerationLogAdmin(admin.ModelAdmin):
    list_display = (
        'moderator_display', 'action', 'comment_preview', 'old_status', 
        'new_status', 'created_at'
    )
    list_filter = ('action', 'created_at', 'old_status', 'new_status')
    search_fields = (
        'moderator__username', 'comment__text', 'reason'
    )
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'moderator', 'comment__user'
        )
    
    def moderator_display(self, obj):
        return f"{obj.moderator.username}"
    moderator_display.short_description = 'Moderator'
    
    def comment_preview(self, obj):
        preview = obj.comment.text[:50] + '...' if len(obj.comment.text) > 50 else obj.comment.text
        return format_html(
            '<span title="{}">by {} - {}</span>',
            obj.comment.text,
            obj.comment.user.username,
            preview
        )
    comment_preview.short_description = 'Comment'
    
    def has_add_permission(self, request):
        return False  # Logs should only be created programmatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should be immutable


@admin.register(CommentNotification)
class CommentNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'recipient_display', 'sender_display', 'notification_type', 
        'comment_preview', 'is_read', 'created_at'
    )
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = (
        'recipient__username', 'sender__username', 'message', 'comment__text'
    )
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)
    actions = ['mark_as_read', 'mark_as_unread']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'recipient', 'sender', 'comment__user'
        )
    
    def recipient_display(self, obj):
        return f"{obj.recipient.username}"
    recipient_display.short_description = 'Recipient'
    
    def sender_display(self, obj):
        return f"{obj.sender.username}"
    sender_display.short_description = 'Sender'
    
    def comment_preview(self, obj):
        preview = obj.comment.text[:50] + '...' if len(obj.comment.text) > 50 else obj.comment.text
        return format_html(
            '<span title="{}">by {} - {}</span>',
            obj.comment.text,
            obj.comment.user.username,
            preview
        )
    comment_preview.short_description = 'Comment'
    
    def mark_as_read(self, request, queryset):
        count = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f"{count} notifications marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        count = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(request, f"{count} notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"