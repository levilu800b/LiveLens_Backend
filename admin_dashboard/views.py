# ===================================================================
# admin_dashboard/views.py
# type: ignore

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, date
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import AdminActivity, PlatformStatistics, ContentModerationQueue
from .serializers import (
    AdminActivitySerializer, PlatformStatisticsSerializer, 
    ContentModerationQueueSerializer, DashboardStatsSerializer,
    ContentManagementSerializer, UserManagementSerializer, UserBasicSerializer
)

User = get_user_model()

class IsAdminPermission(permissions.BasePermission):
    """Custom permission to only allow admin users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


def log_admin_activity(admin, activity_type, description, content_object=None, metadata=None, request=None):
    """Helper function to log admin activities"""
    data = {
        'admin': admin,
        'activity_type': activity_type,
        'description': description,
        'metadata': metadata or {}
    }
    
    if content_object:
        data['content_object'] = content_object
    
    if request:
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            data['ip_address'] = x_forwarded_for.split(',')[0]
        else:
            data['ip_address'] = request.META.get('REMOTE_ADDR')
        
        data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
    
    return AdminActivity.objects.create(**data)


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Get comprehensive dashboard statistics',
    description='Returns all platform statistics including users, content, engagement metrics, and trending data'
)
@api_view(['GET'])
@permission_classes([IsAdminPermission])
def dashboard_stats(request):
    """Get comprehensive dashboard statistics"""
    
    # Current date
    today = timezone.now().date()
    now = timezone.now()
    
    # User Statistics
    total_users = User.objects.count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    active_users_today = User.objects.filter(last_login__date=today).count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    # Content Statistics - Import models dynamically to avoid circular imports
    try:
        from stories.models import Story
        total_stories = Story.objects.count()
        trending_stories_data = Story.objects.filter(is_trending=True).values(
            'id', 'title', 'author__username', 'read_count', 'like_count'
        )[:5]
    except ImportError:
        total_stories = 0
        trending_stories_data = []
    
    try:
        from media_content.models import Film, Content
        total_films = Film.objects.count()
        total_content = Content.objects.count()
        trending_films_data = Film.objects.filter(is_trending=True).values(
            'id', 'title', 'creator__username', 'view_count', 'like_count'
        )[:5]
    except ImportError:
        total_films = 0
        total_content = 0
        trending_films_data = []
    
    try:
        from podcasts.models import Podcast
        total_podcasts = Podcast.objects.count()
        trending_podcasts_data = Podcast.objects.filter(is_trending=True).values(
            'id', 'title', 'creator__username', 'play_count', 'like_count'
        )[:5]
    except ImportError:
        total_podcasts = 0
        trending_podcasts_data = []
    
    try:
        from animations.models import Animation
        total_animations = Animation.objects.count()
        trending_animations_data = Animation.objects.filter(is_trending=True).values(
            'id', 'title', 'creator__username', 'view_count', 'like_count'
        )[:5]
    except ImportError:
        total_animations = 0
        trending_animations_data = []
    
    try:
        from sneak_peeks.models import SneakPeek
        total_sneak_peeks = SneakPeek.objects.count()
    except ImportError:
        total_sneak_peeks = 0
    
    try:
        from live_video.models import LiveVideo
        total_live_videos = LiveVideo.objects.count()
    except ImportError:
        total_live_videos = 0
    
    # Engagement Statistics
    try:
        from comments.models import Comment
        total_comments = Comment.objects.count()
    except ImportError:
        total_comments = 0
    
    # Calculate total likes across all content (this would need to be implemented based on your like system)
    total_likes = 0  # Placeholder
    total_views = 0  # Placeholder
    
    # Most Active Users (by content creation)
    most_active_users = User.objects.annotate(
        content_count=Count('story', distinct=True)  # This would need to be expanded for all content types
    ).order_by('-content_count')[:5].values(
        'id', 'username', 'first_name', 'last_name', 'content_count'
    )
    
    # Recent Admin Activities
    recent_activities = AdminActivity.objects.select_related('admin').order_by('-timestamp')[:10]
    
    # Moderation Queue
    pending_moderation = ContentModerationQueue.objects.filter(status='pending').count()
    
    # Performance Metrics (these would be calculated from actual user session data)
    avg_session_duration = 15.5  # Placeholder
    bounce_rate = 25.3  # Placeholder
    
    stats_data = {
        'total_users': total_users,
        'new_users_today': new_users_today,
        'active_users_today': active_users_today,
        'verified_users': verified_users,
        'total_stories': total_stories,
        'total_films': total_films,
        'total_content': total_content,
        'total_podcasts': total_podcasts,
        'total_animations': total_animations,
        'total_sneak_peeks': total_sneak_peeks,
        'total_live_videos': total_live_videos,
        'total_all_content': total_stories + total_films + total_content + total_podcasts + total_animations + total_sneak_peeks + total_live_videos,
        'total_comments': total_comments,
        'total_likes': total_likes,
        'total_views': total_views,
        'trending_stories': list(trending_stories_data),
        'trending_films': list(trending_films_data),
        'trending_podcasts': list(trending_podcasts_data),
        'trending_animations': list(trending_animations_data),
        'most_active_users': list(most_active_users),
        'recent_activities': AdminActivitySerializer(recent_activities, many=True).data,
        'pending_moderation': pending_moderation,
        'avg_session_duration': avg_session_duration,
        'bounce_rate': bounce_rate,
    }
    
    return Response(stats_data)


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Get all content for management',
    parameters=[
        OpenApiParameter('content_type', OpenApiTypes.STR, description='Filter by content type (stories, films, content, podcasts, animations, sneak_peeks)'),
        OpenApiParameter('status', OpenApiTypes.STR, description='Filter by status'),
        OpenApiParameter('search', OpenApiTypes.STR, description='Search in title or description'),
    ]
)
@api_view(['GET'])
@permission_classes([IsAdminPermission])
def content_management(request):
    """Get all content for admin management"""
    
    content_type = request.GET.get('content_type', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    all_content = []
    
    # Helper function to format content data
    def format_content(content, content_type_name):
        return {
            'content_type': content_type_name,
            'content_id': content.id,
            'title': content.title,
            'author': getattr(content, 'author', getattr(content, 'creator', 'Unknown')),
            'status': getattr(content, 'status', 'published'),
            'views': getattr(content, 'view_count', getattr(content, 'read_count', getattr(content, 'play_count', 0))),
            'likes': getattr(content, 'like_count', 0),
            'comments': getattr(content, 'comment_count', 0),
            'created_at': content.created_at,
            'is_featured': getattr(content, 'is_featured', False),
            'is_trending': getattr(content, 'is_trending', False),
        }
    
    # Get content from each app
    if not content_type or content_type == 'stories':
        try:
            from stories.models import Story
            stories = Story.objects.all()
            if status_filter:
                stories = stories.filter(status=status_filter)
            if search:
                stories = stories.filter(Q(title__icontains=search) | Q(description__icontains=search))
            
            for story in stories:
                all_content.append(format_content(story, 'stories'))
        except ImportError:
            pass
    
    if not content_type or content_type == 'films':
        try:
            from media_content.models import Film
            films = Film.objects.all()
            if status_filter:
                films = films.filter(status=status_filter)
            if search:
                films = films.filter(Q(title__icontains=search) | Q(description__icontains=search))
            
            for film in films:
                all_content.append(format_content(film, 'films'))
        except ImportError:
            pass
    
    if not content_type or content_type == 'content':
        try:
            from media_content.models import Content
            content_items = Content.objects.all()
            if status_filter:
                content_items = content_items.filter(status=status_filter)
            if search:
                content_items = content_items.filter(Q(title__icontains=search) | Q(description__icontains=search))
            
            for item in content_items:
                all_content.append(format_content(item, 'content'))
        except ImportError:
            pass
    
    if not content_type or content_type == 'podcasts':
        try:
            from podcasts.models import Podcast
            podcasts = Podcast.objects.all()
            if status_filter:
                podcasts = podcasts.filter(status=status_filter)
            if search:
                podcasts = podcasts.filter(Q(title__icontains=search) | Q(description__icontains=search))
            
            for podcast in podcasts:
                all_content.append(format_content(podcast, 'podcasts'))
        except ImportError:
            pass
    
    if not content_type or content_type == 'animations':
        try:
            from animations.models import Animation
            animations = Animation.objects.all()
            if status_filter:
                animations = animations.filter(status=status_filter)
            if search:
                animations = animations.filter(Q(title__icontains=search) | Q(description__icontains=search))
            
            for animation in animations:
                all_content.append(format_content(animation, 'animations'))
        except ImportError:
            pass
    
    if not content_type or content_type == 'sneak_peeks':
        try:
            from sneak_peeks.models import SneakPeek
            sneak_peeks = SneakPeek.objects.all()
            if search:
                sneak_peeks = sneak_peeks.filter(Q(title__icontains=search) | Q(description__icontains=search))
            
            for sneak_peek in sneak_peeks:
                all_content.append(format_content(sneak_peek, 'sneak_peeks'))
        except ImportError:
            pass
    
    # Sort by creation date (newest first)
    all_content.sort(key=lambda x: x['created_at'], reverse=True)
    
    return Response({
        'content': all_content,
        'total_count': len(all_content)
    })


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Get all users for management',
    parameters=[
        OpenApiParameter('status', OpenApiTypes.STR, description='Filter by status (active, inactive, staff)'),
        OpenApiParameter('search', OpenApiTypes.STR, description='Search in username, email, or name'),
    ]
)
@api_view(['GET'])
@permission_classes([IsAdminPermission])
def user_management(request):
    """Get all users for admin management"""
    
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    users = User.objects.all()
    
    # Apply filters
    if status_filter == 'active':
        users = users.filter(is_active=True, is_staff=False)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'staff':
        users = users.filter(is_staff=True)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    users = users.order_by('-date_joined')
    
    serializer = UserManagementSerializer(users, many=True)
    
    return Response({
        'users': serializer.data,
        'total_count': users.count()
    })


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Make user an admin',
    description='Grant admin privileges to a user'
)
@api_view(['POST'])
@permission_classes([IsAdminPermission])
def make_user_admin(request, user_id):
    """Make a user an admin"""
    
    user = get_object_or_404(User, id=user_id)
    
    if user.is_staff:
        return Response({
            'message': f'{user.username} is already an admin.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user.is_staff = True
    user.save()
    
    # Log admin activity
    log_admin_activity(
        admin=request.user,
        activity_type='make_admin',
        description=f'Made {user.username} an admin',
        content_object=user,
        request=request
    )
    
    return Response({
        'message': f'{user.username} has been made an admin.',
        'user': UserBasicSerializer(user).data
    })


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Remove admin privileges from user',
    description='Remove admin privileges from a user'
)
@api_view(['POST'])
@permission_classes([IsAdminPermission])
def remove_user_admin(request, user_id):
    """Remove admin privileges from a user"""
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent removing admin from yourself
    if user == request.user:
        return Response({
            'message': 'You cannot remove admin privileges from yourself.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not user.is_staff:
        return Response({
            'message': f'{user.username} is not an admin.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user.is_staff = False
    user.save()
    
    # Log admin activity
    log_admin_activity(
        admin=request.user,
        activity_type='remove_admin',
        description=f'Removed admin privileges from {user.username}',
        content_object=user,
        request=request
    )
    
    return Response({
        'message': f'Admin privileges removed from {user.username}.',
        'user': UserBasicSerializer(user).data
    })


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Delete a user account',
    description='Permanently delete a user account'
)
@api_view(['DELETE'])
@permission_classes([IsAdminPermission])
def delete_user(request, user_id):
    """Delete a user account"""
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting yourself
    if user == request.user:
        return Response({
            'message': 'You cannot delete your own account.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    username = user.username
    
    # Log admin activity before deletion
    log_admin_activity(
        admin=request.user,
        activity_type='delete_user',
        description=f'Deleted user account: {username}',
        metadata={'deleted_user_id': user.id, 'deleted_username': username},
        request=request
    )
    
    user.delete()
    
    return Response({
        'message': f'User {username} has been deleted.'
    })


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Delete content',
    description='Delete any type of content'
)
@api_view(['DELETE'])
@permission_classes([IsAdminPermission])
def delete_content(request, content_type, content_id):
    """Delete content of any type"""
    
    # Map content types to models
    content_models = {
        'stories': 'stories.models.Story',
        'films': 'media_content.models.Film',
        'content': 'media_content.models.Content',
        'podcasts': 'podcasts.models.Podcast',
        'animations': 'animations.models.Animation',
        'sneak_peeks': 'sneak_peeks.models.SneakPeek',
        'live_videos': 'live_video.models.LiveVideo',
    }
    
    if content_type not in content_models:
        return Response({
            'message': 'Invalid content type.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Dynamic import
        module_path, class_name = content_models[content_type].rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        model_class = getattr(module, class_name)
        
        content = get_object_or_404(model_class, id=content_id)
        content_title = content.title
        
        # Log admin activity before deletion
        log_admin_activity(
            admin=request.user,
            activity_type='delete_content',
            description=f'Deleted {content_type[:-1]}: {content_title}',
            metadata={'content_type': content_type, 'content_id': content_id, 'content_title': content_title},
            request=request
        )
        
        content.delete()
        
        return Response({
            'message': f'{content_type[:-1].title()} "{content_title}" has been deleted.'
        })
        
    except ImportError:
        return Response({
            'message': f'Content type {content_type} not available.'
        }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Get admin activities log',
    description='Get paginated list of admin activities'
)
@api_view(['GET'])
@permission_classes([IsAdminPermission])
def admin_activities(request):
    """Get admin activities log"""
    
    activities = AdminActivity.objects.select_related('admin').order_by('-timestamp')
    
    # Filter by admin if specified
    admin_id = request.GET.get('admin_id')
    if admin_id:
        activities = activities.filter(admin_id=admin_id)
    
    # Filter by activity type if specified
    activity_type = request.GET.get('activity_type')
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
    
    # Simple pagination
    page_size = 50
    page = int(request.GET.get('page', 1))
    start = (page - 1) * page_size
    end = start + page_size
    
    paginated_activities = activities[start:end]
    
    serializer = AdminActivitySerializer(paginated_activities, many=True)
    
    return Response({
        'activities': serializer.data,
        'total_count': activities.count(),
        'page': page,
        'page_size': page_size,
        'has_next': activities.count() > end
    })


@extend_schema(
    tags=['Admin Dashboard'],
    summary='Get content moderation queue',
    description='Get content that needs moderation'
)
@api_view(['GET'])
@permission_classes([IsAdminPermission])
def moderation_queue(request):
    """Get content moderation queue"""
    
    queue_items = ContentModerationQueue.objects.select_related(
        'submitted_by', 'reviewed_by'
    ).order_by('-priority', '-submitted_at')
    
    # Filter by status if specified
    status_filter = request.GET.get('status', 'pending')
    if status_filter:
        queue_items = queue_items.filter(status=status_filter)
    
    serializer = ContentModerationQueueSerializer(queue_items, many=True)
    
    return Response({
        'queue_items': serializer.data,
        'total_count': queue_items.count()
    })

