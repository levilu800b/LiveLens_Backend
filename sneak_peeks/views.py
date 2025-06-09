# sneak_peeks/views.py
# type: ignore

from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Count, Sum, Avg
from django.utils import timezone
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    SneakPeek, SneakPeekView, SneakPeekInteraction, 
    SneakPeekPlaylist, SneakPeekPlaylistItem
)
from .serializers import (
    SneakPeekListSerializer, SneakPeekDetailSerializer,
    SneakPeekCreateUpdateSerializer, SneakPeekInteractionSerializer,
    SneakPeekViewSerializer, SneakPeekPlaylistSerializer,
    SneakPeekPlaylistCreateUpdateSerializer, SneakPeekStatsSerializer
)
from .filters import SneakPeekFilter
from .permissions import IsAuthorOrReadOnly
from .utils import get_client_ip, detect_device_type, log_sneak_peek_activity

class SneakPeekPagination(PageNumberPagination):
    """Custom pagination for sneak peeks"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class SneakPeekListCreateView(generics.ListCreateAPIView):
    """
    List all published sneak peeks or create a new one
    GET /api/sneak-peeks/
    POST /api/sneak-peeks/
    """
    
    queryset = SneakPeek.objects.filter(status='published').select_related('author')
    serializer_class = SneakPeekListSerializer
    pagination_class = SneakPeekPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SneakPeekFilter
    search_fields = ['title', 'description', 'tags', 'category']
    ordering_fields = ['created_at', 'view_count', 'like_count', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SneakPeekCreateUpdateSerializer
        return SneakPeekListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by featured/trending if requested
        if self.request.query_params.get('featured') == 'true':
            queryset = queryset.filter(is_featured=True)
        
        if self.request.query_params.get('trending') == 'true':
            queryset = queryset.filter(is_trending=True)
        
        # Filter by premium status
        if self.request.query_params.get('premium') == 'true':
            queryset = queryset.filter(is_premium=True)
        elif self.request.query_params.get('premium') == 'false':
            queryset = queryset.filter(is_premium=False)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create a new sneak peek"""
        sneak_peek = serializer.save(author=self.request.user)
        
        # Log activity
        log_sneak_peek_activity(
            user=self.request.user,
            action='sneak_peek_created',
            sneak_peek=sneak_peek,
            request=self.request
        )


class SneakPeekDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific sneak peek
    GET /api/sneak-peeks/{id}/
    PUT /api/sneak-peeks/{id}/
    DELETE /api/sneak-peeks/{id}/
    """
    
    queryset = SneakPeek.objects.select_related('author')
    serializer_class = SneakPeekDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SneakPeekCreateUpdateSerializer
        return SneakPeekDetailSerializer
    
    def get_object(self):
        """Get sneak peek and check permissions"""
        obj = super().get_object()
        
        # Check if user can view this sneak peek
        if obj.status != 'published':
            if not self.request.user.is_authenticated or \
               (obj.author != self.request.user and not self.request.user.is_admin):
                from rest_framework.exceptions import NotFound
                raise NotFound("Sneak peek not found")
        
        # Track view if it's a GET request
        if self.request.method == 'GET':
            self.track_view(obj)
        
        return obj
    
    def track_view(self, sneak_peek):
        """Track sneak peek view"""
        # Don't track views from the author
        if self.request.user.is_authenticated and sneak_peek.author == self.request.user:
            return
        
        # Create view record
        view_data = {
            'sneak_peek': sneak_peek,
            'ip_address': get_client_ip(self.request),
            'user_agent': self.request.META.get('HTTP_USER_AGENT', ''),
            'device_type': detect_device_type(self.request),
            'referrer': self.request.META.get('HTTP_REFERER', ''),
        }
        
        if self.request.user.is_authenticated:
            view_data['user'] = self.request.user
        
        # Extract UTM parameters
        for param in ['utm_source', 'utm_medium', 'utm_campaign']:
            value = self.request.query_params.get(param)
            if value:
                view_data[param] = value
        
        SneakPeekView.objects.create(**view_data)
        
        # Increment view count
        sneak_peek.increment_view_count()
    
    def perform_destroy(self, instance):
        """Soft delete sneak peek by changing status"""
        instance.status = 'archived'
        instance.save()
        
        # Log activity
        log_sneak_peek_activity(
            user=self.request.user,
            action='sneak_peek_deleted',
            sneak_peek=instance,
            request=self.request
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sneak_peek_interaction(request, sneak_peek_slug):
    """
    Handle sneak peek interactions (like, dislike, share, etc.)
    POST /api/sneak-peeks/{slug}/interact/
    """
    
    sneak_peek = get_object_or_404(
        SneakPeek, 
        slug=sneak_peek_slug, 
        status='published'
    )
    
    interaction_type = request.data.get('interaction_type')
    if not interaction_type:
        return Response({
            'error': 'interaction_type is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    valid_interactions = ['like', 'dislike', 'share', 'favorite', 'download', 'report']
    if interaction_type not in valid_interactions:
        return Response({
            'error': f'Invalid interaction type. Must be one of: {", ".join(valid_interactions)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user already has this interaction
    existing_interaction = SneakPeekInteraction.objects.filter(
        user=request.user,
        sneak_peek=sneak_peek,
        interaction_type=interaction_type
    ).first()
    
    if existing_interaction:
        # Remove existing interaction (toggle off)
        existing_interaction.delete()
        
        # Update sneak peek counts
        if interaction_type == 'like':
            SneakPeek.objects.filter(id=sneak_peek.id).update(
                like_count=F('like_count') - 1
            )
        elif interaction_type == 'dislike':
            SneakPeek.objects.filter(id=sneak_peek.id).update(
                dislike_count=F('dislike_count') - 1
            )
        elif interaction_type == 'share':
            SneakPeek.objects.filter(id=sneak_peek.id).update(
                share_count=F('share_count') - 1
            )
        
        return Response({
            'message': f'{interaction_type.title()} removed',
            'action': 'removed'
        }, status=status.HTTP_200_OK)
    
    else:
        # Remove opposite interaction if it's like/dislike
        if interaction_type in ['like', 'dislike']:
            opposite_type = 'dislike' if interaction_type == 'like' else 'like'
            opposite_interaction = SneakPeekInteraction.objects.filter(
                user=request.user,
                sneak_peek=sneak_peek,
                interaction_type=opposite_type
            ).first()
            
            if opposite_interaction:
                opposite_interaction.delete()
                # Update opposite count
                if opposite_type == 'like':
                    SneakPeek.objects.filter(id=sneak_peek.id).update(
                        like_count=F('like_count') - 1
                    )
                else:
                    SneakPeek.objects.filter(id=sneak_peek.id).update(
                        dislike_count=F('dislike_count') - 1
                    )
        
        # Create new interaction
        interaction_data = {
            'user': request.user,
            'sneak_peek': sneak_peek,
            'interaction_type': interaction_type
        }
        
        # Add additional data for specific interactions
        if interaction_type == 'share':
            interaction_data['share_platform'] = request.data.get('share_platform', '')
        elif interaction_type in ['like', 'dislike']:
            interaction_data['rating'] = request.data.get('rating')
        
        interaction = SneakPeekInteraction.objects.create(**interaction_data)
        
        # Update sneak peek counts
        if interaction_type == 'like':
            SneakPeek.objects.filter(id=sneak_peek.id).update(
                like_count=F('like_count') + 1
            )
        elif interaction_type == 'dislike':
            SneakPeek.objects.filter(id=sneak_peek.id).update(
                dislike_count=F('dislike_count') + 1
            )
        elif interaction_type == 'share':
            SneakPeek.objects.filter(id=sneak_peek.id).update(
                share_count=F('share_count') + 1
            )
        
        # Log activity
        log_sneak_peek_activity(
            user=request.user,
            action=f'sneak_peek_{interaction_type}',
            sneak_peek=sneak_peek,
            request=request
        )
        
        return Response({
            'message': f'{interaction_type.title()} added',
            'action': 'added',
            'interaction': SneakPeekInteractionSerializer(interaction).data
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def track_watch_progress(request, sneak_peek_slug):
    """
    Track user's watch progress for a sneak peek
    POST /api/sneak-peeks/{slug}/track-progress/
    """
    
    sneak_peek = get_object_or_404(
        SneakPeek, 
        slug=sneak_peek_slug, 
        status='published'
    )
    
    watch_duration = request.data.get('watch_duration', 0)
    completion_percentage = request.data.get('completion_percentage', 0.0)
    
    # Update or create view record with watch progress
    view, created = SneakPeekView.objects.get_or_create(
        sneak_peek=sneak_peek,
        user=request.user,
        ip_address=get_client_ip(request),
        defaults={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'device_type': detect_device_type(request),
            'watch_duration': watch_duration,
            'completion_percentage': completion_percentage,
        }
    )
    
    if not created:
        # Update existing record with maximum values
        view.watch_duration = max(view.watch_duration, watch_duration)
        view.completion_percentage = max(view.completion_percentage, completion_percentage)
        view.save()
    
    return Response({
        'message': 'Watch progress tracked successfully'
    }, status=status.HTTP_200_OK)


class SneakPeekPlaylistListCreateView(generics.ListCreateAPIView):
    """
    List user's playlists or create a new one
    GET /api/sneak-peeks/playlists/
    POST /api/sneak-peeks/playlists/
    """
    
    serializer_class = SneakPeekPlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SneakPeekPagination
    
    def get_queryset(self):
        if self.request.query_params.get('public') == 'true':
            # Public playlists
            return SneakPeekPlaylist.objects.filter(
                is_public=True
            ).select_related('creator').annotate(
                sneak_peek_count=Count('sneak_peeks'),
                total_duration=Sum('sneak_peeks__duration')
            ).order_by('-updated_at')
        else:
            # User's own playlists
            return SneakPeekPlaylist.objects.filter(
                creator=self.request.user
            ).annotate(
                sneak_peek_count=Count('sneak_peeks'),
                total_duration=Sum('sneak_peeks__duration')
            ).order_by('-updated_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SneakPeekPlaylistCreateUpdateSerializer
        return SneakPeekPlaylistSerializer
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class SneakPeekPlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific playlist
    GET /api/sneak-peeks/playlists/{id}/
    PUT /api/sneak-peeks/playlists/{id}/
    DELETE /api/sneak-peeks/playlists/{id}/
    """
    
    serializer_class = SneakPeekPlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SneakPeekPlaylist.objects.annotate(
            sneak_peek_count=Count('sneak_peeks'),
            total_duration=Sum('sneak_peeks__duration')
        ).select_related('creator')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SneakPeekPlaylistCreateUpdateSerializer
        return SneakPeekPlaylistSerializer
    
    def get_object(self):
        playlist = super().get_object()
        
        # Check permissions
        if not playlist.is_public:
            if playlist.creator != self.request.user and not self.request.user.is_admin:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to access this playlist")
        
        return playlist


@api_view(['GET'])
def sneak_peek_stats(request):
    """
    Get sneak peek statistics
    GET /api/sneak-peeks/stats/
    """
    
    # Check cache first
    cache_key = "sneak_peek_stats"
    stats = cache.get(cache_key)
    
    if not stats:
        # Calculate statistics
        sneak_peeks = SneakPeek.objects.filter(status='published')
        
        total_sneak_peeks = sneak_peeks.count()
        total_views = sneak_peeks.aggregate(total=Sum('view_count'))['total'] or 0
        total_likes = sneak_peeks.aggregate(total=Sum('like_count'))['total'] or 0
        total_comments = sneak_peeks.aggregate(total=Sum('comment_count'))['total'] or 0
        
        # Get average rating from interactions
        avg_rating = SneakPeekInteraction.objects.filter(
            rating__isnull=False
        ).aggregate(avg=Avg('rating'))['avg'] or 0.0
        
        # Get most viewed and liked sneak peeks
        most_viewed = sneak_peeks.order_by('-view_count').first()
        most_liked = sneak_peeks.order_by('-like_count').first()
        
        # Get trending sneak peeks (high activity in last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        trending_sneak_peeks = sneak_peeks.filter(
            created_at__gte=week_ago
        ).order_by('-view_count', '-like_count')[:5]
        
        # Get recent sneak peeks
        recent_sneak_peeks = sneak_peeks.order_by('-created_at')[:5]
        
        stats = {
            'total_sneak_peeks': total_sneak_peeks,
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'average_rating': round(avg_rating, 2),
            'most_viewed': SneakPeekListSerializer(most_viewed, context={'request': request}).data if most_viewed else None,
            'most_liked': SneakPeekListSerializer(most_liked, context={'request': request}).data if most_liked else None,
            'trending_sneak_peeks': SneakPeekListSerializer(trending_sneak_peeks, many=True, context={'request': request}).data,
            'recent_sneak_peeks': SneakPeekListSerializer(recent_sneak_peeks, many=True, context={'request': request}).data,
        }
        
        # Cache for 30 minutes
        cache.set(cache_key, stats, 1800)
    
    serializer = SneakPeekStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_sneak_peek_history(request):
    """
    Get user's sneak peek viewing history
    GET /api/sneak-peeks/history/
    """
    
    views = SneakPeekView.objects.filter(
        user=request.user
    ).select_related('sneak_peek__author').order_by('-viewed_at')
    
    paginator = SneakPeekPagination()
    page = paginator.paginate_queryset(views, request)
    
    if page is not None:
        serializer = SneakPeekViewSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = SneakPeekViewSerializer(views, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_favorites(request):
    """
    Get user's favorite sneak peeks
    GET /api/sneak-peeks/favorites/
    """
    
    favorite_interactions = SneakPeekInteraction.objects.filter(
        user=request.user,
        interaction_type='favorite'
    ).select_related('sneak_peek__author').order_by('-created_at')
    
    sneak_peeks = [interaction.sneak_peek for interaction in favorite_interactions]
    
    paginator = SneakPeekPagination()
    page = paginator.paginate_queryset(sneak_peeks, request)
    
    if page is not None:
        serializer = SneakPeekListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = SneakPeekListSerializer(sneak_peeks, many=True, context={'request': request})
    return Response(serializer.data)