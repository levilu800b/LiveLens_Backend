# type: ignore

# podcasts/views.py
from rest_framework import generics, viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    PodcastSeries, Podcast, PodcastInteraction, PodcastView, 
    PodcastPlaylist, PodcastSubscription
)
from .serializers import (
    PodcastSeriesListSerializer, PodcastSeriesDetailSerializer, 
    PodcastSeriesCreateUpdateSerializer, PodcastListSerializer,
    PodcastDetailSerializer, PodcastCreateUpdateSerializer,
    PodcastInteractionSerializer, PodcastPlaylistSerializer,
    PodcastSubscriptionSerializer, PodcastViewSerializer,
    PodcastStatsSerializer
)
from .filters import PodcastSeriesFilter, PodcastFilter
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from stories.permissions import IsOwnerOrReadOnly

class PodcastSeriesViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Podcast Series CRUD operations
    """
    serializer_class = PodcastSeriesListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PodcastSeriesFilter
    search_fields = ['title', 'description', 'host', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter series based on user permissions"""
        queryset = PodcastSeries.objects.select_related('author').annotate(
            episode_count=Count('episodes', filter=Q(episodes__status='published'))
        )
        
        # Only show active series to non-admin users
        if not (self.request.user.is_authenticated and 
                hasattr(self.request.user, 'is_admin') and 
                self.request.user.is_admin()):
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return PodcastSeriesDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PodcastSeriesCreateUpdateSerializer
        return PodcastSeriesListSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Subscribe/unsubscribe to podcast series"""
        series = self.get_object()
        
        subscription, created = PodcastSubscription.objects.get_or_create(
            user=request.user,
            series=series,
            defaults={
                'notifications_enabled': True,
                'auto_download': False
            }
        )
        
        if not created:
            # If subscription exists, unsubscribe
            subscription.delete()
            return Response({
                'message': 'Unsubscribed successfully.',
                'subscribed': False
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Subscribed successfully.',
            'subscribed': True,
            'subscription': PodcastSubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def episodes(self, request, pk=None):
        """Get episodes for this series"""
        series = self.get_object()
        episodes = series.episodes.filter(status='published').order_by(
            '-season_number', '-episode_number'
        )
        
        # Apply pagination
        page = self.paginate_queryset(episodes)
        if page is not None:
            serializer = PodcastListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = PodcastListSerializer(episodes, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def interact(self, request, pk=None):
        """Handle series interactions (subscribe, rate)"""
        series = self.get_object()
        serializer = PodcastInteractionSerializer(
            data=request.data,
            context={'request': request, 'series': series, 'podcast': None}
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
                'interaction': PodcastInteractionSerializer(interaction).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured podcast series"""
        featured_series = self.get_queryset().filter(is_featured=True)[:10]
        serializer = self.get_serializer(featured_series, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available podcast categories"""
        categories = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in PodcastSeries.CATEGORY_CHOICES
        ]
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def my_series(self, request):
        """Get current user's podcast series"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_series = PodcastSeries.objects.filter(author=request.user)
        
        # Apply filters
        filter_backend = DjangoFilterBackend()
        user_series = filter_backend.filter_queryset(request, user_series, self)
        
        page = self.paginate_queryset(user_series)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(user_series, many=True)
        return Response(serializer.data)

class PodcastViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Podcast Episode CRUD operations
    """
    serializer_class = PodcastListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PodcastFilter
    search_fields = ['title', 'description', 'guest', 'tags', 'series__title']
    ordering_fields = [
        'created_at', 'updated_at', 'published_at', 'play_count', 
        'like_count', 'average_rating', 'duration', 'episode_number'
    ]
    ordering = ['-published_at', '-created_at']
    
    def get_queryset(self):
        """Filter episodes based on user permissions"""
        queryset = Podcast.objects.select_related('author', 'series')
        
        # Non-authenticated users only see published episodes
        if not self.request.user.is_authenticated:
            return queryset.filter(status='published')
        
        # Authors can see their own episodes, others only see published
        if self.action == 'list':
            if hasattr(self.request.user, 'is_admin') and self.request.user.is_admin():
                return queryset  # Admins see all episodes
            else:
                return queryset.filter(
                    Q(status='published') | Q(author=self.request.user)
                )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return PodcastDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PodcastCreateUpdateSerializer
        return PodcastListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve episode and increment play count"""
        instance = self.get_object()
        
        # Increment play count
        instance.increment_play_count()
        
        # Track the listen
        if request.user.is_authenticated:
            PodcastView.objects.create(
                podcast=instance,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def interact(self, request, pk=None):
        """Handle episode interactions (like, bookmark, listen, rate)"""
        podcast = self.get_object()
        serializer = PodcastInteractionSerializer(
            data=request.data,
            context={'request': request, 'podcast': podcast, 'series': None}
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
                'interaction': PodcastInteractionSerializer(interaction).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def play(self, request, pk=None):
        """Get audio file for playback (authenticated users only)"""
        podcast = self.get_object()
        
        if not podcast.audio_file and not podcast.video_file:
            return Response({
                'detail': 'No audio or video file available for this episode.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user has access (premium content)
        if podcast.is_premium and not getattr(request.user, 'is_premium', False):
            return Response({
                'detail': 'Premium subscription required to listen to this episode.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        response_data = {
            'duration': podcast.duration,
            'duration_formatted': podcast.duration_formatted,
            'audio_quality': podcast.audio_quality,
        }
        
        if podcast.audio_file:
            response_data['audio_url'] = podcast.audio_file.url
        
        if podcast.video_file:
            response_data['video_url'] = podcast.video_file.url
        
        if podcast.transcript_file:
            response_data['transcript_url'] = podcast.transcript_file.url
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured episodes"""
        featured_episodes = self.get_queryset().filter(
            is_featured=True, 
            status='published'
        )[:10]
        
        serializer = self.get_serializer(featured_episodes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending episodes based on recent play count"""
        trending_episodes = self.get_queryset().filter(
            status='published'
        ).order_by('-play_count', '-like_count')[:10]
        
        serializer = self.get_serializer(trending_episodes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recently published episodes"""
        recent_episodes = self.get_queryset().filter(
            status='published'
        ).order_by('-published_at')[:20]
        
        serializer = self.get_serializer(recent_episodes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_episodes(self, request):
        """Get current user's episodes"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_episodes = Podcast.objects.filter(author=request.user)
        
        # Apply filters
        filter_backend = DjangoFilterBackend()
        user_episodes = filter_backend.filter_queryset(request, user_episodes, self)
        
        page = self.paginate_queryset(user_episodes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(user_episodes, many=True)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PodcastPlaylistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Podcast Playlists
    """
    serializer_class = PodcastPlaylistSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return user's playlists and public playlists"""
        return PodcastPlaylist.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).select_related('user').prefetch_related('episodes').annotate(
            episode_count=Count('episodes'),
            total_duration=Sum('episodes__duration')
        )
    
    @action(detail=True, methods=['post'])
    def add_episode(self, request, pk=None):
        """Add episode to playlist"""
        playlist = self.get_object()
        
        if playlist.user != request.user:
            return Response(
                {'detail': 'You can only modify your own playlists.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        episode_id = request.data.get('episode_id')
        if not episode_id:
            return Response(
                {'detail': 'episode_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            episode = Podcast.objects.get(id=episode_id, status='published')
            playlist.episodes.add(episode)
            return Response({'message': 'Episode added to playlist successfully.'})
        except Podcast.DoesNotExist:
            return Response(
                {'detail': 'Episode not found or not published.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['delete'])
    def remove_episode(self, request, pk=None):
        """Remove episode from playlist"""
        playlist = self.get_object()
        
        if playlist.user != request.user:
            return Response(
                {'detail': 'You can only modify your own playlists.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        episode_id = request.data.get('episode_id')
        if not episode_id:
            return Response(
                {'detail': 'episode_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            episode = Podcast.objects.get(id=episode_id)
            playlist.episodes.remove(episode)
            return Response({'message': 'Episode removed from playlist successfully.'})
        except Podcast.DoesNotExist:
            return Response(
                {'detail': 'Episode not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class PodcastLibraryView(APIView):
    """
    API view for user's podcast library
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's podcast library (subscriptions, listened, bookmarked)"""
        user = request.user
        
        # Get subscribed series
        subscriptions = PodcastSubscription.objects.filter(user=user).select_related('series')
        subscribed_series = [sub.series for sub in subscriptions]
        
        # Get listened episodes
        listened_episodes = Podcast.objects.filter(
            podcastinteraction__user=user,
            podcastinteraction__interaction_type='listen'
        ).distinct()
        
        # Get bookmarked episodes
        bookmarked_episodes = Podcast.objects.filter(
            podcastinteraction__user=user,
            podcastinteraction__interaction_type='bookmark'
        ).distinct()
        
        # Get user's playlists
        user_playlists = PodcastPlaylist.objects.filter(user=user)
        
        return Response({
            'subscribed_series': PodcastSeriesListSerializer(
                subscribed_series, many=True, context={'request': request}
            ).data,
            'listened_episodes': PodcastListSerializer(
                listened_episodes, many=True, context={'request': request}
            ).data,
            'bookmarked_episodes': PodcastListSerializer(
                bookmarked_episodes, many=True, context={'request': request}
            ).data,
            'playlists': PodcastPlaylistSerializer(
                user_playlists, many=True, context={'request': request}
            ).data,
        })

class PodcastStatsView(APIView):
    """
    API view for podcast statistics
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get comprehensive podcast statistics"""
        # Basic counts
        total_series = PodcastSeries.objects.filter(is_active=True).count()
        total_episodes = Podcast.objects.filter(status='published').count()
        
        # Aggregate stats
        total_plays = Podcast.objects.aggregate(
            total=Sum('play_count')
        )['total'] or 0
        
        total_subscribers = PodcastSubscription.objects.count()
        
        # Top content
        featured_series = PodcastSeries.objects.filter(
            is_featured=True,
            is_active=True
        ).annotate(
            episode_count=Count('episodes', filter=Q(episodes__status='published'))
        )[:5]
        
        trending_episodes = Podcast.objects.filter(
            status='published'
        ).order_by('-play_count', '-like_count')[:5]
        
        recent_episodes = Podcast.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]
        
        top_series = PodcastSeries.objects.filter(
            is_active=True
        ).annotate(
            subscriber_count=Count('subscribers'),
            total_plays=Sum('episodes__play_count')
        ).order_by('-subscriber_count', '-total_plays')[:5]
        
        stats_data = {
            'total_series': total_series,
            'total_episodes': total_episodes,
            'total_plays': total_plays,
            'total_subscribers': total_subscribers,
            'featured_series': featured_series,
            'trending_episodes': trending_episodes,
            'recent_episodes': recent_episodes,
            'top_series': top_series,
        }
        
        serializer = PodcastStatsSerializer(stats_data)
        return Response(serializer.data)

class HeroPodcastView(APIView):
    """
    API view for getting hero podcast (most popular)
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get the hero podcast for the homepage"""
        content_type = request.query_params.get('type', 'episode')  # 'episode' or 'series'
        
        if content_type == 'series':
            # Get the series with highest engagement score
            hero_series = PodcastSeries.objects.filter(
                is_active=True
            ).annotate(
                subscriber_count=Count('subscribers'),
                total_plays=Sum('episodes__play_count')
            ).order_by('-subscriber_count', '-total_plays', '-is_featured').first()
            
            if not hero_series:
                return Response({'detail': 'No podcast series found.'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = PodcastSeriesDetailSerializer(hero_series, context={'request': request})
        else:
            # Get the episode with highest engagement score
            hero_episode = Podcast.objects.filter(
                status='published'
            ).annotate(
                engagement_score=F('play_count') + F('like_count') * 2
            ).order_by('-engagement_score', '-is_featured').first()
            
            if not hero_episode:
                return Response({'detail': 'No podcast episodes found.'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = PodcastDetailSerializer(hero_episode, context={'request': request})
        
        return Response(serializer.data)

class PodcastSearchView(APIView):
    """
    Advanced podcast search functionality
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Advanced search for podcasts"""
        query = request.query_params.get('q', '')
        search_type = request.query_params.get('type', 'all')  # 'series', 'episode', 'all'
        category = request.query_params.get('category', '')
        tags = request.query_params.get('tags', '').split(',') if request.query_params.get('tags') else []
        host = request.query_params.get('host', '')
        
        results = {'series': [], 'episodes': []}
        
        # Search series
        if search_type in ['series', 'all']:
            series = PodcastSeries.objects.filter(is_active=True)
            
            if query:
                series = series.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(host__icontains=query) |
                    Q(tags__icontains=query)
                )
            
            if category:
                series = series.filter(category=category)
            
            if tags:
                for tag in tags:
                    if tag.strip():
                        series = series.filter(tags__icontains=tag.strip())
            
            if host:
                series = series.filter(host__icontains=host)
            
            series = series.order_by('-is_featured', '-created_at')[:10]
            results['series'] = PodcastSeriesListSerializer(
                series, many=True, context={'request': request}
            ).data
        
        # Search episodes
        if search_type in ['episode', 'all']:
            episodes = Podcast.objects.filter(status='published')
            
            if query:
                episodes = episodes.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(guest__icontains=query) |
                    Q(tags__icontains=query) |
                    Q(series__title__icontains=query) |
                    Q(series__host__icontains=query)
                )
            
            if category:
                episodes = episodes.filter(series__category=category)
            
            if tags:
                for tag in tags:
                    if tag.strip():
                        episodes = episodes.filter(
                            Q(tags__icontains=tag.strip()) |
                            Q(series__tags__icontains=tag.strip())
                        )
            
            if host:
                episodes = episodes.filter(series__host__icontains=host)
            
            episodes = episodes.order_by('-is_featured', '-published_at')[:10]
            results['episodes'] = PodcastListSerializer(
                episodes, many=True, context={'request': request}
            ).data
        
        return Response(results)

class TrackPodcastListenAPIView(APIView):
    """
    Track podcast listening for analytics
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, podcast_id):
        """Track a podcast listen"""
        try:
            podcast = Podcast.objects.get(id=podcast_id, status='published')
        except Podcast.DoesNotExist:
            return Response(
                {'detail': 'Podcast episode not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PodcastViewSerializer(
            data=request.data,
            context={'request': request, 'podcast': podcast}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Listen tracked successfully.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)