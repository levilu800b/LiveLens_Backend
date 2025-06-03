# type: ignore

# media_content/views.py
from rest_framework import generics, viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, F, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    Film, Content, MediaInteraction, MediaView, MediaCollection, 
    Playlist, PlaylistItem
)
from .serializers import (
    FilmListSerializer, FilmDetailSerializer, FilmCreateUpdateSerializer,
    ContentListSerializer, ContentDetailSerializer, ContentCreateUpdateSerializer,
    MediaInteractionSerializer, MediaCollectionSerializer, PlaylistSerializer,
    MediaViewSerializer, MediaStatsSerializer, PlaylistItemSerializer
)
from .filters import FilmFilter, ContentFilter
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from stories.permissions import IsOwnerOrReadOnly

class FilmViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Film CRUD operations
    """
    serializer_class = FilmListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FilmFilter
    search_fields = ['title', 'description', 'director', 'cast', 'tags']
    ordering_fields = [
        'created_at', 'updated_at', 'published_at', 'view_count', 
        'like_count', 'average_rating', 'duration', 'release_year'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter films based on user permissions"""
        queryset = Film.objects.select_related('author')
        
        # Non-authenticated users only see published films
        if not self.request.user.is_authenticated:
            return queryset.filter(status='published')
        
        # Authors can see their own films, others only see published
        if self.action == 'list':
            if hasattr(self.request.user, 'is_admin') and self.request.user.is_admin():
                return queryset  # Admins see all films
            else:
                return queryset.filter(
                    Q(status='published') | Q(author=self.request.user)
                )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return FilmDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FilmCreateUpdateSerializer
        return FilmListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve film and increment view count"""
        instance = self.get_object()
        
        # Increment view count
        instance.increment_view_count()
        
        # Track the view
        if request.user.is_authenticated:
            MediaView.objects.create(
                content_type='film',
                object_id=instance.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def interact(self, request, pk=None):
        """Handle film interactions (like, bookmark, watch, rate)"""
        film = self.get_object()
        serializer = MediaInteractionSerializer(
            data=request.data,
            context={
                'request': request, 
                'content_type': 'film', 
                'object_id': film.id
            }
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
                'interaction': MediaInteractionSerializer(interaction).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def watch_trailer(self, request, pk=None):
        """Get trailer information for the film"""
        film = self.get_object()
        
        if not film.trailer_file:
            return Response({
                'detail': 'No trailer available for this film.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'trailer_url': film.trailer_file.url if film.trailer_file else None,
            'trailer_duration': film.trailer_duration,
            'trailer_duration_formatted': film.trailer_duration_formatted,
        })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def play_now(self, request, pk=None):
        """Get video file for playback (authenticated users only)"""
        film = self.get_object()
        
        if not film.video_file:
            return Response({
                'detail': 'No video file available for this film.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user has access (premium content)
        if film.is_premium and not request.user.is_premium:  # Assuming premium user field
            return Response({
                'detail': 'Premium subscription required to watch this film.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'video_url': film.video_file.url,
            'duration': film.duration,
            'duration_formatted': film.duration_formatted,
            'quality': film.video_quality,
            'subtitles': film.subtitles_available,
        })
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured films"""
        featured_films = self.get_queryset().filter(
            is_featured=True, 
            status='published'
        )[:10]
        
        serializer = self.get_serializer(featured_films, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending films"""
        trending_films = self.get_queryset().filter(
            is_trending=True,
            status='published'
        ).order_by('-view_count', '-like_count')[:10]
        
        serializer = self.get_serializer(trending_films, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_films(self, request):
        """Get current user's films"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_films = Film.objects.filter(author=request.user)
        
        # Apply filters
        filter_backend = DjangoFilterBackend()
        user_films = filter_backend.filter_queryset(request, user_films, self)
        
        page = self.paginate_queryset(user_films)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(user_films, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available film categories"""
        categories = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Film.CATEGORY_CHOICES
        ]
        return Response(categories)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ContentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Content CRUD operations
    """
    serializer_class = ContentListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ContentFilter
    search_fields = ['title', 'description', 'creator', 'series_name', 'tags']
    ordering_fields = [
        'created_at', 'updated_at', 'published_at', 'view_count', 
        'like_count', 'average_rating', 'duration'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter content based on user permissions"""
        queryset = Content.objects.select_related('author')
        
        # Non-authenticated users only see published content
        if not self.request.user.is_authenticated:
            return queryset.filter(status='published')
        
        # Authors can see their own content, others only see published
        if self.action == 'list':
            if hasattr(self.request.user, 'is_admin') and self.request.user.is_admin():
                return queryset  # Admins see all content
            else:
                return queryset.filter(
                    Q(status='published') | Q(author=self.request.user)
                )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return ContentDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ContentCreateUpdateSerializer
        return ContentListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve content and increment view count"""
        instance = self.get_object()
        
        # Increment view count
        instance.increment_view_count()
        
        # Track the view
        if request.user.is_authenticated:
            MediaView.objects.create(
                content_type='content',
                object_id=instance.id,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def interact(self, request, pk=None):
        """Handle content interactions (like, bookmark, watch, rate)"""
        content = self.get_object()
        serializer = MediaInteractionSerializer(
            data=request.data,
            context={
                'request': request, 
                'content_type': 'content', 
                'object_id': content.id
            }
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
                'interaction': MediaInteractionSerializer(interaction).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def watch_trailer(self, request, pk=None):
        """Get trailer information for the content"""
        content = self.get_object()
        
        if not content.trailer_file:
            return Response({
                'detail': 'No trailer available for this content.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'trailer_url': content.trailer_file.url if content.trailer_file else None,
            'trailer_duration': content.trailer_duration,
            'trailer_duration_formatted': content.trailer_duration_formatted,
        })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def play_now(self, request, pk=None):
        """Get video file for playback (authenticated users only)"""
        content = self.get_object()
        
        if not content.video_file:
            return Response({
                'detail': 'No video file available for this content.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user has access (premium content)
        if content.is_premium and not request.user.is_premium:  # Assuming premium user field
            return Response({
                'detail': 'Premium subscription required to watch this content.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'video_url': content.video_file.url,
            'duration': content.duration,
            'duration_formatted': content.duration_formatted,
            'quality': content.video_quality,
            'subtitles': content.subtitles_available,
            'is_live': content.is_live,
            'live_stream_url': content.live_stream_url if content.is_live else None,
        })
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured content"""
        featured_content = self.get_queryset().filter(
            is_featured=True, 
            status='published'
        )[:10]
        
        serializer = self.get_serializer(featured_content, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending content"""
        trending_content = self.get_queryset().filter(
            is_trending=True,
            status='published'
        ).order_by('-view_count', '-like_count')[:10]
        
        serializer = self.get_serializer(trending_content, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def live(self, request):
        """Get live content"""
        live_content = self.get_queryset().filter(
            is_live=True,
            status='published'
        ).order_by('-created_at')[:10]
        
        serializer = self.get_serializer(live_content, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_content(self, request):
        """Get current user's content"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_content = Content.objects.filter(author=request.user)
        
        # Apply filters
        filter_backend = DjangoFilterBackend()
        user_content = filter_backend.filter_queryset(request, user_content, self)
        
        page = self.paginate_queryset(user_content)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(user_content, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def content_types(self, request):
        """Get available content types"""
        content_types = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Content.CONTENT_TYPE_CHOICES
        ]
        return Response(content_types)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class MediaCollectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Media Collections
    """
    serializer_class = MediaCollectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return user's collections and public collections"""
        return MediaCollection.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).select_related('user').prefetch_related('films', 'content')
    
    @action(detail=True, methods=['post'])
    def add_film(self, request, pk=None):
        """Add a film to the collection"""
        collection = self.get_object()
        
        if collection.user != request.user:
            return Response(
                {'detail': 'You can only modify your own collections.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        film_id = request.data.get('film_id')
        if not film_id:
            return Response(
                {'detail': 'film_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            film = Film.objects.get(id=film_id, status='published')
            collection.films.add(film)
            return Response({'message': 'Film added to collection successfully.'})
        except Film.DoesNotExist:
            return Response(
                {'detail': 'Film not found or not published.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def add_content(self, request, pk=None):
        """Add content to the collection"""
        collection = self.get_object()
        
        if collection.user != request.user:
            return Response(
                {'detail': 'You can only modify your own collections.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        content_id = request.data.get('content_id')
        if not content_id:
            return Response(
                {'detail': 'content_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            content = Content.objects.get(id=content_id, status='published')
            collection.content.add(content)
            return Response({'message': 'Content added to collection successfully.'})
        except Content.DoesNotExist:
            return Response(
                {'detail': 'Content not found or not published.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['delete'])
    def remove_film(self, request, pk=None):
        """Remove a film from the collection"""
        collection = self.get_object()
        
        if collection.user != request.user:
            return Response(
                {'detail': 'You can only modify your own collections.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        film_id = request.data.get('film_id')
        if not film_id:
            return Response(
                {'detail': 'film_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            film = Film.objects.get(id=film_id)
            collection.films.remove(film)
            return Response({'message': 'Film removed from collection successfully.'})
        except Film.DoesNotExist:
            return Response(
                {'detail': 'Film not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['delete'])
    def remove_content(self, request, pk=None):
        """Remove content from the collection"""
        collection = self.get_object()
        
        if collection.user != request.user:
            return Response(
                {'detail': 'You can only modify your own collections.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        content_id = request.data.get('content_id')
        if not content_id:
            return Response(
                {'detail': 'content_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            content = Content.objects.get(id=content_id)
            collection.content.remove(content)
            return Response({'message': 'Content removed from collection successfully.'})
        except Content.DoesNotExist:
            return Response(
                {'detail': 'Content not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class PlaylistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Playlists
    """
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return user's playlists and public playlists"""
        return Playlist.objects.filter(
            Q(creator=self.request.user) | Q(is_public=True)
        ).select_related('creator').prefetch_related('items')
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to playlist"""
        playlist = self.get_object()
        
        if playlist.creator != request.user:
            return Response(
                {'detail': 'You can only modify your own playlists.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        content_type = request.data.get('content_type')
        object_id = request.data.get('object_id')
        
        if not content_type or not object_id:
            return Response(
                {'detail': 'content_type and object_id are required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if content_type not in ['film', 'content']:
            return Response(
                {'detail': 'content_type must be "film" or "content".'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the object exists
        if content_type == 'film':
            if not Film.objects.filter(id=object_id, status='published').exists():
                return Response(
                    {'detail': 'Film not found or not published.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            if not Content.objects.filter(id=object_id, status='published').exists():
                return Response(
                    {'detail': 'Content not found or not published.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Get next order number
        last_item = playlist.items.order_by('-order').first()
        next_order = (last_item.order + 1) if last_item else 1
        
        # Create playlist item
        playlist_item = PlaylistItem.objects.create(
            playlist=playlist,
            content_type=content_type,
            object_id=object_id,
            order=next_order
        )
        
        serializer = PlaylistItemSerializer(playlist_item, context={'request': request})
        return Response({
            'message': 'Item added to playlist successfully.',
            'item': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """Remove item from playlist"""
        playlist = self.get_object()
        
        if playlist.creator != request.user:
            return Response(
                {'detail': 'You can only modify your own playlists.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'detail': 'item_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = PlaylistItem.objects.get(id=item_id, playlist=playlist)
            item.delete()
            return Response({'message': 'Item removed from playlist successfully.'})
        except PlaylistItem.DoesNotExist:
            return Response(
                {'detail': 'Playlist item not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def reorder_items(self, request, pk=None):
        """Reorder playlist items"""
        playlist = self.get_object()
        
        if playlist.creator != request.user:
            return Response(
                {'detail': 'You can only modify your own playlists.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        item_orders = request.data.get('item_orders', [])
        if not item_orders:
            return Response(
                {'detail': 'item_orders is required (list of {item_id: order}).'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update item orders
        for item_data in item_orders:
            try:
                item = PlaylistItem.objects.get(
                    id=item_data['item_id'], 
                    playlist=playlist
                )
                item.order = item_data['order']
                item.save()
            except (PlaylistItem.DoesNotExist, KeyError):
                continue
        
        return Response({'message': 'Playlist items reordered successfully.'})

class MediaLibraryView(APIView):
    """
    API view for user's media library
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's media library (watched, bookmarked content)"""
        user = request.user
        
        # Get watched films and content
        watched_films = Film.objects.filter(
            mediainteraction__user=user,
            mediainteraction__interaction_type='watch'
        ).distinct()
        
        watched_content = Content.objects.filter(
            mediainteraction__user=user,
            mediainteraction__interaction_type='watch'
        ).distinct()
        
        # Get bookmarked films and content
        bookmarked_films = Film.objects.filter(
            mediainteraction__user=user,
            mediainteraction__interaction_type='bookmark'
        ).distinct()
        
        bookmarked_content = Content.objects.filter(
            mediainteraction__user=user,
            mediainteraction__interaction_type='bookmark'
        ).distinct()
        
        return Response({
            'watched_films': FilmListSerializer(watched_films, many=True, context={'request': request}).data,
            'watched_content': ContentListSerializer(watched_content, many=True, context={'request': request}).data,
            'bookmarked_films': FilmListSerializer(bookmarked_films, many=True, context={'request': request}).data,
            'bookmarked_content': ContentListSerializer(bookmarked_content, many=True, context={'request': request}).data,
        })

class MediaStatsView(APIView):
    """
    API view for media statistics
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get comprehensive media statistics"""
        # Basic counts
        total_films = Film.objects.count()
        total_content = Content.objects.count()
        
        # Aggregate stats
        total_views = (
            Film.objects.aggregate(total=Sum('view_count'))['total'] or 0
        ) + (
            Content.objects.aggregate(total=Sum('view_count'))['total'] or 0
        )
        
        total_likes = (
            Film.objects.aggregate(total=Sum('like_count'))['total'] or 0
        ) + (
            Content.objects.aggregate(total=Sum('like_count'))['total'] or 0
        )
        
        # Top content
        trending_films = Film.objects.filter(
            status='published'
        ).order_by('-view_count', '-like_count')[:5]
        
        trending_content = Content.objects.filter(
            status='published'
        ).order_by('-view_count', '-like_count')[:5]
        
        featured_films = Film.objects.filter(
            is_featured=True,
            status='published'
        )[:5]
        
        featured_content = Content.objects.filter(
            is_featured=True,
            status='published'
        )[:5]
        
        recent_films = Film.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]
        
        recent_content = Content.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]
        
        stats_data = {
            'total_films': total_films,
            'total_content': total_content,
            'total_views': total_views,
            'total_likes': total_likes,
            'trending_films': trending_films,
            'trending_content': trending_content,
            'featured_films': featured_films,
            'featured_content': featured_content,
            'recent_films': recent_films,
            'recent_content': recent_content,
        }
        
        serializer = MediaStatsSerializer(stats_data)
        return Response(serializer.data)

class HeroMediaView(APIView):
    """
    API view for getting hero media content (most popular)
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get the hero media for the homepage"""
        media_type = request.query_params.get('type', 'film')  # 'film' or 'content'
        
        if media_type == 'film':
            # Get the film with highest engagement score
            hero_media = Film.objects.filter(
                status='published'
            ).annotate(
                engagement_score=F('view_count') + F('like_count') * 2
            ).order_by('-engagement_score', '-is_featured', '-is_trending').first()
            
            if not hero_media:
                return Response({'detail': 'No published films found.'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = FilmDetailSerializer(hero_media, context={'request': request})
        else:
            # Get the content with highest engagement score
            hero_media = Content.objects.filter(
                status='published'
            ).annotate(
                engagement_score=F('view_count') + F('like_count') * 2
            ).order_by('-engagement_score', '-is_featured', '-is_trending').first()
            
            if not hero_media:
                return Response({'detail': 'No published content found.'}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ContentDetailSerializer(hero_media, context={'request': request})
        
        return Response(serializer.data)

class MediaSearchView(APIView):
    """
    Advanced media search functionality
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Advanced search for media content"""
        query = request.query_params.get('q', '')
        media_type = request.query_params.get('type', 'all')  # 'film', 'content', 'all'
        category = request.query_params.get('category', '')
        tags = request.query_params.get('tags', '').split(',') if request.query_params.get('tags') else []
        author = request.query_params.get('author', '')
        
        results = {'films': [], 'content': []}
        
        # Search films
        if media_type in ['film', 'all']:
            films = Film.objects.filter(status='published')
            
            if query:
                films = films.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(director__icontains=query) |
                    Q(cast__icontains=query) |
                    Q(tags__icontains=query)
                )
            
            if category:
                films = films.filter(category=category)
            
            if tags:
                for tag in tags:
                    if tag.strip():
                        films = films.filter(tags__icontains=tag.strip())
            
            if author:
                films = films.filter(
                    Q(author__username__icontains=author) |
                    Q(author__first_name__icontains=author) |
                    Q(author__last_name__icontains=author)
                )
            
            films = films.order_by('-view_count', '-like_count', '-created_at')[:10]
            results['films'] = FilmListSerializer(films, many=True, context={'request': request}).data
        
        # Search content
        if media_type in ['content', 'all']:
            content = Content.objects.filter(status='published')
            
            if query:
                content = content.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(creator__icontains=query) |
                    Q(series_name__icontains=query) |
                    Q(tags__icontains=query)
                )
            
            if category:
                content = content.filter(category=category)
            
            if tags:
                for tag in tags:
                    if tag.strip():
                        content = content.filter(tags__icontains=tag.strip())
            
            if author:
                content = content.filter(
                    Q(author__username__icontains=author) |
                    Q(author__first_name__icontains=author) |
                    Q(author__last_name__icontains=author)
                )
            
            content = content.order_by('-view_count', '-like_count', '-created_at')[:10]
            results['content'] = ContentListSerializer(content, many=True, context={'request': request}).data
        
        return Response(results)

class TrackMediaViewAPIView(APIView):
    """
    Track media view for analytics
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, media_type, media_id):
        """Track a media view"""
        if media_type not in ['film', 'content']:
            return Response(
                {'detail': 'media_type must be "film" or "content".'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify media exists
        if media_type == 'film':
            if not Film.objects.filter(id=media_id, status='published').exists():
                return Response(
                    {'detail': 'Film not found.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            if not Content.objects.filter(id=media_id, status='published').exists():
                return Response(
                    {'detail': 'Content not found.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = MediaViewSerializer(
            data=request.data,
            context={
                'request': request, 
                'content_type': media_type, 
                'object_id': media_id
            }
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'View tracked successfully.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)