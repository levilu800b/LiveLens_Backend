# comments/views.py
# type: ignore

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, F, Count, Prefetch
from django.utils import timezone
from django.core.cache import cache
from .models import Comment, CommentInteraction, CommentNotification
from .serializers import (
    CommentSerializer, CommentCreateSerializer, CommentUpdateSerializer,
    CommentInteractionCreateSerializer, CommentNotificationSerializer
)
from .utils import get_client_ip, log_comment_activity, send_comment_notification

class CommentPagination(PageNumberPagination):
    """Custom pagination for comments"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommentListCreateView(generics.ListCreateAPIView):
    """
    List comments for a specific content or create a new comment
    GET /api/comments/?content_type=story&object_id=uuid
    POST /api/comments/
    """
    
    serializer_class = CommentSerializer
    pagination_class = CommentPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get comments for specific content"""
        content_type_name = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')
        
        if not content_type_name or not object_id:
            return Comment.objects.none()
        
        try:
            content_type = ContentType.objects.get(model=content_type_name)
        except ContentType.DoesNotExist:
            return Comment.objects.none()
        
        # Get only top-level comments (no parent) for the specific content
        queryset = Comment.objects.filter(
            content_type=content_type,
            object_id=object_id,
            parent__isnull=True,
            status='published'
        ).select_related('user').prefetch_related(
            Prefetch(
                'replies',
                queryset=Comment.objects.filter(status='published')
                .select_related('user')
                .order_by('created_at')
            )
        ).annotate(
            reply_count=Count('replies', filter=Q(replies__status='published'))
        ).order_by('-created_at')
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        """Create a new comment"""
        comment = serializer.save(
            user=self.request.user,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Log activity
        log_comment_activity(
            user=self.request.user,
            action='comment_created',
            comment=comment,
            request=self.request
        )
        
        # Send notification if it's a reply
        if comment.parent:
            send_comment_notification(
                recipient=comment.parent.user,
                sender=self.request.user,
                comment=comment,
                notification_type='reply'
            )
        
        # Update parent reply count if it's a reply
        if comment.parent:
            Comment.objects.filter(id=comment.parent.id).update(
                reply_count=F('reply_count') + 1
            )


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific comment
    GET /api/comments/{id}/
    PUT /api/comments/{id}/
    DELETE /api/comments/{id}/
    """
    
    queryset = Comment.objects.select_related('user').prefetch_related('replies')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CommentUpdateSerializer
        return CommentSerializer
    
    def get_object(self):
        """Get comment and check permissions"""
        comment = get_object_or_404(Comment, id=self.kwargs['pk'])
        
        # Check if user can view this comment
        if comment.status != 'published' and not self.request.user.is_admin:
            if not self.request.user.is_authenticated or comment.user != self.request.user:
                from rest_framework.exceptions import NotFound
                raise NotFound("Comment not found")
        
        return comment
    
    def check_object_permissions(self, request, obj):
        """Check if user can modify this comment"""
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            if not request.user.is_authenticated:
                self.permission_denied(request)
            
            # Users can edit/delete their own comments, admins can edit/delete any
            if obj.user != request.user and not request.user.is_admin:
                self.permission_denied(request)
            
            # Check edit time limit for non-admins
            if request.method in ['PUT', 'PATCH'] and not request.user.is_admin:
                from datetime import timedelta
                edit_time_limit = obj.created_at + timedelta(minutes=15)
                if timezone.now() > edit_time_limit:
                    self.permission_denied(request, message="Edit time limit exceeded")
    
    def perform_destroy(self, instance):
        """Soft delete comment"""
        instance.soft_delete()
        
        # Log activity
        log_comment_activity(
            user=self.request.user,
            action='comment_deleted',
            comment=instance,
            request=self.request
        )
        
        # Update parent reply count if it's a reply
        if instance.parent:
            Comment.objects.filter(id=instance.parent.id).update(
                reply_count=F('reply_count') - 1
            )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def comment_interaction(request, comment_id):
    """
    Handle comment interactions (like, dislike, report)
    POST /api/comments/{id}/interact/
    """
    
    comment = get_object_or_404(Comment, id=comment_id, status='published')
    serializer = CommentInteractionCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        interaction_type = serializer.validated_data['interaction_type']
        
        # Check if user already has this interaction
        existing_interaction = CommentInteraction.objects.filter(
            user=request.user,
            comment=comment,
            interaction_type=interaction_type
        ).first()
        
        if existing_interaction:
            # Remove existing interaction (toggle off)
            existing_interaction.delete()
            
            # Update comment counts
            if interaction_type == 'like':
                Comment.objects.filter(id=comment.id).update(
                    like_count=F('like_count') - 1
                )
            elif interaction_type == 'dislike':
                Comment.objects.filter(id=comment.id).update(
                    dislike_count=F('dislike_count') - 1
                )
            
            return Response({
                'message': f'{interaction_type.title()} removed',
                'action': 'removed'
            }, status=status.HTTP_200_OK)
        
        else:
            # Remove opposite interaction if it exists
            if interaction_type in ['like', 'dislike']:
                opposite_type = 'dislike' if interaction_type == 'like' else 'like'
                opposite_interaction = CommentInteraction.objects.filter(
                    user=request.user,
                    comment=comment,
                    interaction_type=opposite_type
                ).first()
                
                if opposite_interaction:
                    opposite_interaction.delete()
                    # Update opposite count
                    if opposite_type == 'like':
                        Comment.objects.filter(id=comment.id).update(
                            like_count=F('like_count') - 1
                        )
                    else:
                        Comment.objects.filter(id=comment.id).update(
                            dislike_count=F('dislike_count') - 1
                        )
            
            # Create new interaction
            interaction = serializer.save(
                user=request.user,
                comment=comment
            )
            
            # Update comment counts
            if interaction_type == 'like':
                Comment.objects.filter(id=comment.id).update(
                    like_count=F('like_count') + 1
                )
                
                # Send notification to comment author
                if comment.user != request.user:
                    send_comment_notification(
                        recipient=comment.user,
                        sender=request.user,
                        comment=comment,
                        notification_type='like'
                    )
                    
            elif interaction_type == 'dislike':
                Comment.objects.filter(id=comment.id).update(
                    dislike_count=F('dislike_count') + 1
                )
                
            elif interaction_type == 'report':
                # Flag comment if it gets multiple reports
                report_count = CommentInteraction.objects.filter(
                    comment=comment,
                    interaction_type='report'
                ).count()
                
                if report_count >= 3:  # Flag after 3 reports
                    Comment.objects.filter(id=comment.id).update(
                        is_flagged=True,
                        flagged_at=timezone.now()
                    )
            
            # Log activity
            log_comment_activity(
                user=request.user,
                action=f'comment_{interaction_type}',
                comment=comment,
                request=request
            )
            
            return Response({
                'message': f'{interaction_type.title()} added',
                'action': 'added'
            }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_comments(request):
    """
    Get current user's comments
    GET /api/comments/my-comments/
    """
    
    comments = Comment.objects.filter(
        user=request.user
    ).exclude(
        status='deleted'
    ).select_related('user').prefetch_related('replies').order_by('-created_at')
    
    paginator = CommentPagination()
    page = paginator.paginate_queryset(comments, request)
    
    if page is not None:
        serializer = CommentSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = CommentSerializer(comments, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def comment_notifications(request):
    """
    Get user's comment notifications
    GET /api/comments/notifications/
    """
    
    notifications = CommentNotification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'comment__user').order_by('-created_at')
    
    # Mark as read if requested
    if request.query_params.get('mark_as_read') == 'true':
        notifications.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    paginator = CommentPagination()
    page = paginator.paginate_queryset(notifications, request)
    
    if page is not None:
        serializer = CommentNotificationSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = CommentNotificationSerializer(notifications, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def comment_moderation(request):
    """
    Get comments that need moderation (admin only)
    GET /api/comments/moderation/
    """
    
    comments = Comment.objects.filter(
        Q(is_flagged=True) | Q(status='pending')
    ).select_related('user').annotate(
        report_count=Count('interactions', filter=Q(interactions__interaction_type='report'))
    ).order_by('-created_at')
    
    paginator = CommentPagination()
    page = paginator.paginate_queryset(comments, request)
    
    if page is not None:
        serializer = CommentSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = CommentSerializer(comments, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def moderate_comment(request, comment_id):
    """
    Moderate a comment (admin only)
    POST /api/comments/{id}/moderate/
    """
    
    comment = get_object_or_404(Comment, id=comment_id)
    action = request.data.get('action')
    reason = request.data.get('reason', '')
    
    if action not in ['approve', 'hide', 'delete']:
        return Response({
            'error': 'Invalid action. Must be approve, hide, or delete.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    old_status = comment.status
    
    if action == 'approve':
        comment.status = 'published'
        comment.is_flagged = False
        comment.flagged_at = None
    elif action == 'hide':
        comment.status = 'hidden'
    elif action == 'delete':
        comment.soft_delete()
    
    comment.moderated_by = request.user
    comment.moderated_at = timezone.now()
    comment.moderation_reason = reason
    comment.save()
    
    # Log moderation action
    from .models import CommentModerationLog
    CommentModerationLog.objects.create(
        comment=comment,
        moderator=request.user,
        action=action,
        reason=reason,
        old_status=old_status,
        new_status=comment.status
    )
    
    # Send notification to comment author
    if action in ['hide', 'delete']:
        send_comment_notification(
            recipient=comment.user,
            sender=request.user,
            comment=comment,
            notification_type='moderation'
        )
    
    return Response({
        'message': f'Comment {action}d successfully',
        'comment': CommentSerializer(comment, context={'request': request}).data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def comment_stats(request):
    """
    Get comment statistics
    GET /api/comments/stats/
    """
    
    content_type_name = request.query_params.get('content_type')
    object_id = request.query_params.get('object_id')
    
    if not content_type_name or not object_id:
        return Response({
            'error': 'content_type and object_id are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        content_type = ContentType.objects.get(model=content_type_name)
    except ContentType.DoesNotExist:
        return Response({
            'error': 'Invalid content type'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check cache first
    cache_key = f"comment_stats_{content_type_name}_{object_id}"
    stats = cache.get(cache_key)
    
    if not stats:
        comments = Comment.objects.filter(
            content_type=content_type,
            object_id=object_id,
            status='published'
        )
        
        stats = {
            'total_comments': comments.count(),
            'top_level_comments': comments.filter(parent__isnull=True).count(),
            'total_likes': comments.aggregate(total_likes=models.Sum('like_count'))['total_likes'] or 0,
            'average_likes': comments.aggregate(avg_likes=models.Avg('like_count'))['avg_likes'] or 0,
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, stats, 300)
    
    return Response(stats)