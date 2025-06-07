# type: ignore

# animations/views.py
from rest_framework import generics, viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    Animation, AnimationInteraction, AnimationView, AnimationCollection,
    AnimationPlaylist, AIAnimationRequest
)
from .serializers import (
    AnimationListSerializer, AnimationDetailSerializer, AnimationCreateUpdateSerializer,
    AnimationInteractionSerializer, AnimationCollectionSerializer, AnimationPlaylistSerializer,
    AnimationViewSerializer, AIAnimationRequestSerializer, AnimationStatsSerializer
)
from .filters import AnimationFilter
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from stories.permissions import IsOwnerOrReadOnly

class AnimationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Animation CRUD operations
    """
    serializer_class = AnimationListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AnimationFilter
    search_fields = ['title', 'description', 'director', 'animator', 'tags']
    ordering_fields = [
        'created_at', 'updated_at', 'published_at', 'view_count', 
        'like_count', 'average_rating', 'duration'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter animations based on user permissions"""
        queryset = Animation.objects.select_related('author')
        
        # Non-authenticated users only see published animations
        if not self.request.user.is_authenticated:
            return queryset.filter(status='published')
        
        # Authors can see their own animations, others only see published
        if self.action == 'list':
            if hasattr(self.request.user, 'is_admin') and self.request.user.is_admin():
                return queryset  # Admins see all animations
            else:
                return queryset.filter(
                    Q(status='published') | Q(author=self.request.user)
                )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return AnimationDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AnimationCreateUpdateSerializer
        return AnimationListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve animation and increment view count"""
        instance = self.get_object()
        
        # Increment view count
        instance.increment_view_count()
        
        # Track the view
        if request.user.is_authenticated:
            AnimationView.objects.create(
                animation=instance,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def interact(self, request, pk=None):
        """Handle animation interactions (like, bookmark, watch, rate)"""
        animation = self.get_object()
        serializer = AnimationInteractionSerializer(
            data=request.data,
            context={'request': request, 'animation': animation}
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
                'interaction': AnimationInteractionSerializer(interaction).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def watch_trailer(self, request, pk=None):
        """Get trailer information for the animation"""
        animation = self.get_object()
        
        if not animation.trailer_file:
            return Response({
                'detail': 'No trailer available for this animation.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'trailer_url': animation.trailer_file.url if animation.trailer_file else None,
            'trailer_duration': animation.trailer_duration,
            'trailer_duration_formatted': animation.trailer_duration_formatted,
        })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def play_now(self, request, pk=None):
        """Get video file for playback (authenticated users only)"""
        animation = self.get_object()
        
        if not animation.video_file:
            return Response({
                'detail': 'No video file available for this animation.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user has access (premium content)
        if animation.is_premium and not getattr(request.user, 'is_premium', False):
            return Response({
                'detail': 'Premium subscription required to watch this animation.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        response_data = {
            'video_url': animation.video_file.url,
            'duration': animation.duration,
            'duration_formatted': animation.duration_formatted,
            'quality': animation.video_quality,
            'frame_rate': animation.frame_rate,
            'resolution': animation.resolution_formatted,
            'subtitles': animation.subtitles_available,
        }
        
        # Include additional files if available
        if animation.project_file:
            response_data['project_file_url'] = animation.project_file.url
        if animation.storyboard:
            response_data['storyboard_url'] = animation.storyboard.url
        if animation.concept_art:
            response_data['concept_art_url'] = animation.concept_art.url
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured animations"""
        featured_animations = self.get_queryset().filter(
            is_featured=True, 
            status='published'
        )[:10]
        
        serializer = self.get_serializer(featured_animations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending animations"""
        trending_animations = self.get_queryset().filter(
            is_trending=True,
            status='published'
        ).order_by('-view_count', '-like_count')[:10]
        
        serializer = self.get_serializer(trending_animations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def ai_generated(self, request):
        """Get AI-generated animations"""
        ai_animations = self.get_queryset().filter(
            is_ai_generated=True,
            status='published'
        ).order_by('-created_at')[:10]
        
        serializer = self.get_serializer(ai_animations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def series(self, request):
        """Get animation series"""
        series_animations = self.get_queryset().filter(
            is_series=True,
            status='published'
        ).values('series_name').annotate(
            episode_count=Count('id'),
            latest_episode=Max('created_at')
        ).order_by('-latest_episode')
        
        return Response(series_animations)
    
    @action(detail=False, methods=['get'])
    def my_animations(self, request):
        """Get current user's animations"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_animations = Animation.objects.filter(author=request.user)
        
        # Apply filters
        filter_backend = DjangoFilterBackend()
        user_animations = filter_backend.filter_queryset(request, user_animations, self)
        
        page = self.paginate_queryset(user_animations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(user_animations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available animation categories"""
        categories = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Animation.CATEGORY_CHOICES
        ]
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def animation_types(self, request):
        """Get available animation types"""
        animation_types = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Animation.ANIMATION_TYPE_CHOICES
        ]
        return Response(animation_types)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class AnimationCollectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Animation Collections
    """
    serializer_class = AnimationCollectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return user's collections and public collections"""
        return AnimationCollection.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).select_related('user').prefetch_related('animations')
    
    @action(detail=True, methods=['post'])
    def add_animation(self, request, pk=None):
        """Add an animation to the collection"""
        collection = self.get_object()
        
        if collection.user != request.user:
            return Response(
                {'detail': 'You can only modify your own collections.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        animation_id = request.data.get('animation_id')
        if not animation_id:
            return Response(
                {'detail': 'animation_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            animation = Animation.objects.get(id=animation_id, status='published')
            collection.animations.add(animation)
            return Response({'message': 'Animation added to collection successfully.'})
        except Animation.DoesNotExist:
            return Response(
                {'detail': 'Animation not found or not published.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['delete'])
    def remove_animation(self, request, pk=None):
        """Remove an animation from the collection"""
        collection = self.get_object()
        
        if collection.user != request.user:
            return Response(
                {'detail': 'You can only modify your own collections.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        animation_id = request.data.get('animation_id')
        if not animation_id:
            return Response(
                {'detail': 'animation_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            animation = Animation.objects.get(id=animation_id)
            collection.animations.remove(animation)
            return Response({'message': 'Animation removed from collection successfully.'})
        except Animation.DoesNotExist:
            return Response(
                {'detail': 'Animation not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class AnimationPlaylistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Animation Playlists
    """
    serializer_class = AnimationPlaylistSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return user's playlists and public playlists"""
        return AnimationPlaylist.objects.filter(
            Q(creator=self.request.user) | Q(is_public=True)
        ).select_related('creator').prefetch_related('animations').annotate(
            animation_count=Count('animations'),
            total_duration=Sum('animations__duration')
        )
    
    @action(detail=True, methods=['post'])
    def add_animation(self, request, pk=None):
        """Add animation to playlist"""
        playlist = self.get_object()
        
        if playlist.creator != request.user:
            return Response(
                {'detail': 'You can only modify your own playlists.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        animation_id = request.data.get('animation_id')
        if not animation_id:
            return Response(
                {'detail': 'animation_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            animation = Animation.objects.get(id=animation_id, status='published')
            playlist.animations.add(animation)
            return Response({'message': 'Animation added to playlist successfully.'})
        except Animation.DoesNotExist:
            return Response(
                {'detail': 'Animation not found or not published.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['delete'])
    def remove_animation(self, request, pk=None):
        """Remove animation from playlist"""
        playlist = self.get_object()
        
        if playlist.creator != request.user:
            return Response(
                {'detail': 'You can only modify your own playlists.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        animation_id = request.data.get('animation_id')
        if not animation_id:
            return Response(
                {'detail': 'animation_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            animation = Animation.objects.get(id=animation_id)
            playlist.animations.remove(animation)
            return Response({'message': 'Animation removed from playlist successfully.'})
        except Animation.DoesNotExist:
            return Response(
                {'detail': 'Animation not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class AIAnimationRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AI Animation Generation Requests
    """
    serializer_class = AIAnimationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return user's AI animation requests"""
        if hasattr(self.request.user, 'is_admin') and self.request.user.is_admin():
            return AIAnimationRequest.objects.all()
        return AIAnimationRequest.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create AI animation generation request"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            ai_request = serializer.save()
            
            # Here you would typically trigger the AI animation generation
            # For now, we'll just set the status to processing
            ai_request.status = 'processing'
            ai_request.save()
            
            return Response({
                'message': 'AI animation generation request created successfully.',
                'request': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate animation with modified parameters"""
        ai_request = self.get_object()
        
        if ai_request.user != request.user:
            return Response(
                {'detail': 'You can only regenerate your own requests.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create new request with updated parameters
        new_data = request.data.copy()
        new_data['prompt'] = new_data.get('prompt', ai_request.prompt)
        
        serializer = self.get_serializer(data=new_data)
        if serializer.is_valid():
            new_request = serializer.save()
            new_request.status = 'processing'
            new_request.save()
            
            return Response({
                'message': 'Animation regeneration request created successfully.',
                'request': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AnimationLibraryView(APIView):
    """
    API view for user's animation library
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's animation library (watched, bookmarked animations)"""
        user = request.user
        
        # Get watched animations
        watched_animations = Animation.objects.filter(
            animationinteraction__user=user,
            animationinteraction__interaction_type='watch'
        ).distinct()
        
        # Get bookmarked animations
        bookmarked_animations = Animation.objects.filter(
            animationinteraction__user=user,
            animationinteraction__interaction_type='bookmark'
        ).distinct()
        
        # Get user's collections
        user_collections = AnimationCollection.objects.filter(user=user)
        
        # Get user's playlists
        user_playlists = AnimationPlaylist.objects.filter(creator=user)
        
        return Response({
            'watched_animations': AnimationListSerializer(
                watched_animations, many=True, context={'request': request}
            ).data,
            'bookmarked_animations': AnimationListSerializer(
                bookmarked_animations, many=True, context={'request': request}
            ).data,
            'collections': AnimationCollectionSerializer(
                user_collections, many=True, context={'request': request}
            ).data,
            'playlists': AnimationPlaylistSerializer(
                user_playlists, many=True, context={'request': request}
            ).data,
        })

class AnimationStatsView(APIView):
    """
    API view for animation statistics
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get comprehensive animation statistics"""
        # Basic counts
        total_animations = Animation.objects.count()
        published_animations = Animation.objects.filter(status='published').count()
        ai_generated_animations = Animation.objects.filter(is_ai_generated=True).count()
        
        # Aggregate stats
        total_views = Animation.objects.aggregate(
            total=Sum('view_count')
        )['total'] or 0
        
        total_likes = Animation.objects.aggregate(
            total=Sum('like_count')
        )['total'] or 0
        
        # Top content
        trending_animations = Animation.objects.filter(
            status='published'
        ).order_by('-view_count', '-like_count')[:5]
        
        featured_animations = Animation.objects.filter(
            is_featured=True,
            status='published'
        )[:5]
        
        recent_animations = Animation.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]
        
        # Category stats
        top_categories = Animation.objects.filter(
            status='published'
        ).values('category').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # AI requests stats
        ai_requests_pending = AIAnimationRequest.objects.filter(
            status__in=['pending', 'processing']
        ).count()
        
        stats_data = {
            'total_animations': total_animations,
            'published_animations': published_animations,
            'ai_generated_animations': ai_generated_animations,
            'total_views': total_views,
            'total_likes': total_likes,
            'trending_animations': trending_animations,
            'featured_animations': featured_animations,
            'recent_animations': recent_animations,
            'top_categories': list(top_categories),
            'ai_requests_pending': ai_requests_pending,
        }
        
        serializer = AnimationStatsSerializer(stats_data)
        return Response(serializer.data)

class HeroAnimationView(APIView):
    """
    API view for getting hero animation (most popular)
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get the hero animation for the homepage"""
        # Get the animation with highest engagement score
        hero_animation = Animation.objects.filter(
            status='published'
        ).annotate(
            engagement_score=F('view_count') + F('like_count') * 2
        ).order_by('-engagement_score', '-is_featured', '-is_trending').first()
        
        if not hero_animation:
            return Response({'detail': 'No published animations found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AnimationDetailSerializer(hero_animation, context={'request': request})
        return Response(serializer.data)

class AnimationSearchView(APIView):
    """
    Advanced animation search functionality
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Advanced search for animations"""
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        animation_type = request.query_params.get('animation_type', '')
        tags = request.query_params.get('tags', '').split(',') if request.query_params.get('tags') else []
        author = request.query_params.get('author', '')
        is_ai_generated = request.query_params.get('is_ai_generated', '')
        
        animations = Animation.objects.filter(status='published')
        
        # Text search
        if query:
            animations = animations.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(director__icontains=query) |
                Q(animator__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # Category filter
        if category:
            animations = animations.filter(category=category)
        
        # Animation type filter
        if animation_type:
            animations = animations.filter(animation_type=animation_type)
        
        # Tags filter
        if tags:
            for tag in tags:
                if tag.strip():
                    animations = animations.filter(tags__icontains=tag.strip())
        
        # Author filter
        if author:
            animations = animations.filter(
                Q(author__username__icontains=author) |
                Q(author__first_name__icontains=author) |
                Q(author__last_name__icontains=author)
            )
        
        # AI generated filter
        if is_ai_generated.lower() in ['true', '1']:
            animations = animations.filter(is_ai_generated=True)
        elif is_ai_generated.lower() in ['false', '0']:
            animations = animations.filter(is_ai_generated=False)
        
        # Order by relevance
        animations = animations.order_by('-view_count', '-like_count', '-created_at')[:20]
        
        serializer = AnimationListSerializer(animations, many=True, context={'request': request})
        return Response(serializer.data)

class TrackAnimationViewAPIView(APIView):
    """
    Track animation view for analytics
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, animation_id):
        """Track an animation view"""
        try:
            animation = Animation.objects.get(id=animation_id, status='published')
        except Animation.DoesNotExist:
            return Response(
                {'detail': 'Animation not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AnimationViewSerializer(
            data=request.data,
            context={'request': request, 'animation': animation}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'View tracked successfully.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GenerateAIAnimationView(APIView):
    """
    Generate animation using AI
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Generate animation using AI prompt"""
        prompt = request.data.get('prompt')
        if not prompt:
            return Response(
                {'detail': 'Prompt is required for AI generation.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create AI request
        ai_request_data = {
            'prompt': prompt,
            'style': request.data.get('style', '2d'),
            'duration_requested': request.data.get('duration', 30),
            'quality_requested': request.data.get('quality', '1080p'),
            'frame_rate_requested': request.data.get('frame_rate', '24'),
            'additional_parameters': request.data.get('additional_parameters', {})
        }
        
        serializer = AIAnimationRequestSerializer(
            data=ai_request_data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            ai_request = serializer.save()
            
            # Here you would integrate with Google AI or other AI service
            # For now, simulate the process
            ai_request.status = 'processing'
            ai_request.ai_model_used = 'Google AI Animation Generator'
            ai_request.save()
            
            return Response({
                'message': 'AI animation generation started.',
                'request_id': ai_request.id,
                'status': ai_request.status
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AIAnimationStatusView(APIView):
    """
    Check AI animation generation status
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, request_id):
        """Get AI animation generation status"""
        try:
            ai_request = AIAnimationRequest.objects.get(
                id=request_id,
                user=request.user
            )
        except AIAnimationRequest.DoesNotExist:
            return Response(
                {'detail': 'AI request not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AIAnimationRequestSerializer(ai_request)
        return Response(serializer.data)