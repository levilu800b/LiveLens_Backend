# live_video/views.py
# type: ignore

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, Max, Sum
from django.contrib.auth import get_user_model
from django.http import JsonResponse

from .models import LiveVideo, LiveVideoInteraction, LiveVideoComment, LiveVideoSchedule
from .serializers import (
    LiveVideoListSerializer,
    LiveVideoDetailSerializer,
    LiveVideoCreateUpdateSerializer,
    LiveVideoInteractionSerializer,
    LiveVideoCommentSerializer,
    LiveVideoScheduleSerializer,
    LiveVideoStatsSerializer
)

User = get_user_model()


class LiveVideoPagination(PageNumberPagination):
    """Custom pagination for live videos"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class LiveVideoViewSet(viewsets.ModelViewSet):
    """ViewSet for managing live videos"""
    
    queryset = LiveVideo.objects.all()
    pagination_class = LiveVideoPagination
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return LiveVideoListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return LiveVideoCreateUpdateSerializer
        else:
            return LiveVideoDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on parameters"""
        queryset = LiveVideo.objects.select_related('author').all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(live_status=status_filter)
        
        # Filter by featured
        featured = self.request.query_params.get('featured', None)
        if featured is not None:
            queryset = queryset.filter(is_featured=featured.lower() == 'true')
        
        # Filter by premium
        premium = self.request.query_params.get('premium', None)
        if premium is not None:
            queryset = queryset.filter(is_premium=premium.lower() == 'true')
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(host_name__icontains=search) |
                Q(tags__icontains=search)
            )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(scheduled_start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_start_time__lte=end_date)
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-scheduled_start_time')
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve live video and increment view count"""
        instance = self.get_object()
        
        # Increment total views
        instance.increment_total_views()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def live_now(self, request):
        """Get currently live videos"""
        live_videos = self.get_queryset().filter(live_status='live').order_by('-current_viewers')
        
        page = self.paginate_queryset(live_videos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(live_videos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming scheduled live videos"""
        upcoming_videos = self.get_queryset().filter(
            live_status='scheduled',
            scheduled_start_time__gt=timezone.now()
        ).order_by('scheduled_start_time')
        
        page = self.paginate_queryset(upcoming_videos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(upcoming_videos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured live videos"""
        featured_videos = self.get_queryset().filter(is_featured=True).order_by('-scheduled_start_time')
        
        page = self.paginate_queryset(featured_videos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(featured_videos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def hero_live(self, request):
        """Get live video for hero section on landing page"""
        # Priority: 1. Currently live, 2. Upcoming featured, 3. Most recent
        hero_video = None
        
        # First try to get currently live video
        hero_video = self.get_queryset().filter(
            live_status='live',
            is_featured=True
        ).order_by('-current_viewers').first()
        
        if not hero_video:
            # Then try upcoming featured video
            hero_video = self.get_queryset().filter(
                live_status='scheduled',
                is_featured=True,
                scheduled_start_time__gt=timezone.now()
            ).order_by('scheduled_start_time').first()
        
        if not hero_video:
            # Finally, get most recent live video
            hero_video = self.get_queryset().filter(
                live_status__in=['live', 'scheduled']
            ).order_by('-scheduled_start_time').first()
        
        if hero_video:
            serializer = self.get_serializer(hero_video)
            return Response(serializer.data)
        
        return Response({'detail': 'No live video available for hero section'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def interact(self, request, slug=None):
        """Handle live video interactions (like, bookmark, join, leave)"""
        live_video = self.get_object()
        serializer = LiveVideoInteractionSerializer(
            data=request.data,
            context={'request': request, 'live_video_id': live_video.id}
        )
        
        if serializer.is_valid():
            interaction = serializer.save()
            
            if interaction is None:
                # Interaction was toggled off (deleted)
                return Response({
                    'message': f'{request.data.get("interaction_type")} removed successfully.'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'message': f'{interaction.interaction_type.title()} added successfully.',
                'interaction': LiveVideoInteractionSerializer(interaction).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def watch_stream(self, request, slug=None):
        """Get live stream information for watching"""
        live_video = self.get_object()
        
        # Check if user has access (premium content)
        if live_video.is_premium and not request.user.is_premium:
            return Response({
                'detail': 'Premium subscription required to watch this live stream.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if stream is live or has a video file
        if not live_video.is_live_now and not live_video.video_file:
            return Response({
                'detail': 'This live stream is not currently available.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Automatically join the stream if live
        if live_video.is_live_now:
            LiveVideoInteraction.objects.get_or_create(
                user=request.user,
                live_video=live_video,
                interaction_type='join',
                defaults={'joined_at': timezone.now()}
            )
        
        return Response({
            'live_stream_url': live_video.live_stream_url if live_video.is_live_now else None,
            'backup_stream_url': live_video.backup_stream_url if live_video.is_live_now else None,
            'video_file_url': live_video.video_file.url if live_video.video_file else None,
            'is_live': live_video.is_live_now,
            'allow_chat': live_video.allow_chat,
            'current_viewers': live_video.current_viewers,
            'quality': live_video.video_quality,
            'duration': live_video.duration,
            'duration_formatted': live_video.duration_formatted,
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def start_stream(self, request, slug=None):
        """Start a live stream (admin only)"""
        live_video = self.get_object()
        
        # Check if user is the author or admin
        if live_video.author != request.user and not request.user.is_staff:
            return Response({
                'detail': 'You do not have permission to start this stream.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if live_video.live_status != 'scheduled':
            return Response({
                'detail': 'Stream can only be started if it is scheduled.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        live_video.start_stream()
        
        return Response({
            'message': 'Live stream started successfully.',
            'live_video': self.get_serializer(live_video).data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def end_stream(self, request, slug=None):
        """End a live stream (admin only)"""
        live_video = self.get_object()
        
        # Check if user is the author or admin
        if live_video.author != request.user and not request.user.is_staff:
            return Response({
                'detail': 'You do not have permission to end this stream.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if live_video.live_status != 'live':
            return Response({
                'detail': 'Stream can only be ended if it is currently live.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        live_video.end_stream()
        
        return Response({
            'message': 'Live stream ended successfully.',
            'live_video': self.get_serializer(live_video).data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_live_videos(self, request):
        """Get current user's live videos"""
        user_videos = self.get_queryset().filter(author=request.user)
        
        page = self.paginate_queryset(user_videos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(user_videos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_watched(self, request):
        """Get live videos watched by current user"""
        watched_ids = LiveVideoInteraction.objects.filter(
            user=request.user,
            interaction_type='watch'
        ).values_list('live_video_id', flat=True)
        
        watched_videos = self.get_queryset().filter(id__in=watched_ids)
        
        page = self.paginate_queryset(watched_videos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(watched_videos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_bookmarks(self, request):
        """Get live videos bookmarked by current user"""
        bookmarked_ids = LiveVideoInteraction.objects.filter(
            user=request.user,
            interaction_type='bookmark'
        ).values_list('live_video_id', flat=True)
        
        bookmarked_videos = self.get_queryset().filter(id__in=bookmarked_ids)
        
        page = self.paginate_queryset(bookmarked_videos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(bookmarked_videos, many=True)
        return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def live_video_comments(request, slug):
    """Get or create comments for a live video"""
    live_video = get_object_or_404(LiveVideo, slug=slug)
    
    if request.method == 'GET':
        # Get comments for the live video
        comments = LiveVideoComment.objects.filter(
            live_video=live_video,
            is_hidden=False
        ).select_related('user').order_by('-timestamp')
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 50))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_comments = comments[start:end]
        
        serializer = LiveVideoCommentSerializer(paginated_comments, many=True)
        
        return Response({
            'results': serializer.data,
            'count': comments.count(),
            'has_next': end < comments.count(),
            'has_previous': page > 1
        })
    
    elif request.method == 'POST':
        # Create a new comment
        if not live_video.allow_chat:
            return Response({
                'detail': 'Chat is disabled for this live video.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = LiveVideoCommentSerializer(
            data=request.data,
            context={'request': request, 'live_video_id': live_video.id}
        )
        
        if serializer.is_valid():
            comment = serializer.save()
            return Response(
                LiveVideoCommentSerializer(comment).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def live_video_stats(request):
    """Get live video statistics"""
    # Basic counts
    total_live_videos = LiveVideo.objects.count()
    live_now_count = LiveVideo.objects.filter(live_status='live').count()
    scheduled_count = LiveVideo.objects.filter(live_status='scheduled').count()
    ended_count = LiveVideo.objects.filter(live_status='ended').count()
    
    # Viewer statistics
    total_viewers = LiveVideo.objects.aggregate(
        total=Sum('current_viewers')
    )['total'] or 0
    
    total_views = LiveVideo.objects.aggregate(
        total=Sum('total_views')
    )['total'] or 0
    
    # Average duration
    average_duration = LiveVideo.objects.filter(
        actual_start_time__isnull=False,
        actual_end_time__isnull=False
    ).extra(
        select={'duration_seconds': 'EXTRACT(EPOCH FROM (actual_end_time - actual_start_time))'}
    ).aggregate(
        avg_duration=Avg('duration_seconds')
    )['avg_duration'] or 0
    
    # Peak concurrent viewers
    peak_concurrent_viewers = LiveVideo.objects.aggregate(
        peak=Max('peak_viewers')
    )['peak'] or 0
    
    # Most viewed live video
    most_viewed_live_video = LiveVideo.objects.order_by('-total_views').first()
    
    # Recent live videos
    recent_live_videos = LiveVideo.objects.order_by('-created_at')[:5]
    
    # Prepare data
    stats_data = {
        'total_live_videos': total_live_videos,
        'live_now_count': live_now_count,
        'scheduled_count': scheduled_count,
        'ended_count': ended_count,
        'total_viewers': total_viewers,
        'total_views': total_views,
        'average_duration': average_duration,
        'peak_concurrent_viewers': peak_concurrent_viewers,
        'most_viewed_live_video': most_viewed_live_video,
        'recent_live_videos': recent_live_videos
    }
    
    serializer = LiveVideoStatsSerializer(stats_data)
    return Response(serializer.data)


class LiveVideoScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing live video schedules"""
    
    queryset = LiveVideoSchedule.objects.all()
    serializer_class = LiveVideoScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter schedules by current user if not admin"""
        if self.request.user.is_staff:
            return LiveVideoSchedule.objects.all()
        return LiveVideoSchedule.objects.filter(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def create_live_video(self, request, pk=None):
        """Create a live video from this schedule"""
        schedule = self.get_object()
        
        live_video = schedule.create_next_live_video()
        
        if live_video:
            serializer = LiveVideoDetailSerializer(live_video)
            return Response({
                'message': 'Live video created successfully from schedule.',
                'live_video': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'detail': 'Could not create live video from this schedule.'
        }, status=status.HTTP_400_BAD_REQUEST)


# Admin API endpoints
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_live_video_upload(request):
    """Create a live video by uploading a video file (Admin Dashboard)"""
    if not request.user.is_staff:
        return Response({
            'detail': 'Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # This is the "Create Live Video" functionality mentioned in your requirements
    # It creates a live video that will appear on the hero section
    
    data = request.data.copy()
    
    # Set default values for hero live video
    data['is_featured'] = True
    data['live_status'] = 'live'  # Mark as live immediately
    data['scheduled_start_time'] = timezone.now()
    
    # If no live stream URL is provided, use the video file
    if 'video_file' in request.FILES and not data.get('live_stream_url'):
        # This creates a "live" video using a pre-recorded file
        # The frontend can treat this as a live stream
        pass
    
    serializer = LiveVideoCreateUpdateSerializer(
        data=data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        live_video = serializer.save()
        
        # Start the stream immediately
        live_video.start_stream()
        
        return Response({
            'message': 'Live video created and started successfully.',
            'live_video': LiveVideoDetailSerializer(live_video).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_live_video_dashboard(request):
    """Get live video dashboard data for admin"""
    if not request.user.is_staff:
        return Response({
            'detail': 'Admin privileges required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get comprehensive dashboard data
    now = timezone.now()
    
    # Current status
    currently_live = LiveVideo.objects.filter(live_status='live')
    upcoming_today = LiveVideo.objects.filter(
        live_status='scheduled',
        scheduled_start_time__date=now.date()
    )
    
    # Recent performance
    recent_ended = LiveVideo.objects.filter(
        live_status='ended',
        actual_end_time__gte=now - timezone.timedelta(days=7)
    ).order_by('-actual_end_time')[:10]
    
    # Top performers
    top_viewed = LiveVideo.objects.order_by('-total_views')[:5]
    top_liked = LiveVideo.objects.order_by('-like_count')[:5]
    
    dashboard_data = {
        'currently_live': LiveVideoListSerializer(currently_live, many=True).data,
        'upcoming_today': LiveVideoListSerializer(upcoming_today, many=True).data,
        'recent_ended': LiveVideoListSerializer(recent_ended, many=True).data,
        'top_viewed': LiveVideoListSerializer(top_viewed, many=True).data,
        'top_liked': LiveVideoListSerializer(top_liked, many=True).data,
        'stats': {
            'total_live_videos': LiveVideo.objects.count(),
            'live_now': currently_live.count(),
            'scheduled_today': upcoming_today.count(),
            'total_viewers_now': sum(lv.current_viewers for lv in currently_live),
            'total_views_today': LiveVideo.objects.filter(
                created_at__date=now.date()
            ).aggregate(Sum('total_views'))['total_views__sum'] or 0,
        }
    }
    
    return Response(dashboard_data)


@api_view(['GET'])
def current_live_status(request):
    """Get current live video status for real-time updates"""
    live_videos = LiveVideo.objects.filter(live_status='live').values(
        'id', 'slug', 'title', 'current_viewers', 'like_count', 'comment_count'
    )
    
    return JsonResponse({
        'live_videos': list(live_videos),
        'total_live_streams': len(live_videos),
        'total_current_viewers': sum(lv['current_viewers'] for lv in live_videos)
    })