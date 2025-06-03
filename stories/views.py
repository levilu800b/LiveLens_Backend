# type: ignore

# stories/views.py
from rest_framework import generics, viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Story, StoryPage, StoryInteraction, StoryView, StoryCollection
from .serializers import (
    StoryListSerializer, StoryDetailSerializer, StoryCreateUpdateSerializer,
    StoryInteractionSerializer, StoryCollectionSerializer, StoryViewSerializer,
    StoryStatsSerializer, StoryPageSerializer
)
from .filters import StoryFilter
from .permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly

class StoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Story CRUD operations
    """
    serializer_class = StoryListSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = StoryFilter
    search_fields = ['title', 'description', 'content', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'published_at', 'read_count', 'like_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter stories based on user permissions"""
        queryset = Story.objects.select_related('author').prefetch_related('pages')
        
        # Non-authenticated users only see published stories
        if not self.request.user.is_authenticated:
            return queryset.filter(status='published')
        
        # Authors can see their own stories, others only see published
        if self.action == 'list':
            if self.request.user.is_admin():
                return queryset  # Admins see all stories
            else:
                return queryset.filter(
                    Q(status='published') | Q(author=self.request.user)
                )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return StoryDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StoryCreateUpdateSerializer
        return StoryListSerializer
    
    def perform_create(self, serializer):
        """Set the author when creating a story"""
        serializer.save(author=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve story and increment read count"""
        instance = self.get_object()
        
        # Increment read count
        instance.increment_read_count()
        
        # Track the view
        if request.user.is_authenticated:
            StoryView.objects.create(
                story=instance,
                user=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def interact(self, request, pk=None):
        """Handle story interactions (like, bookmark, reading progress)"""
        story = self.get_object()
        serializer = StoryInteractionSerializer(
            data=request.data,
            context={'request': request, 'story': story}
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
                'interaction': StoryInteractionSerializer(interaction).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def pages(self, request, pk=None):
        """Get paginated story content"""
        story = self.get_object()
        pages = story.pages.all().order_by('page_number')
        
        # Optional page number filter
        page_number = request.query_params.get('page_number')
        if page_number:
            pages = pages.filter(page_number=page_number)
        
        serializer = StoryPageSerializer(pages, many=True)
        return Response({
            'total_pages': story.pages.count(),
            'pages': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured stories"""
        featured_stories = self.get_queryset().filter(
            is_featured=True, 
            status='published'
        )[:10]
        
        serializer = self.get_serializer(featured_stories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending stories"""
        trending_stories = self.get_queryset().filter(
            is_trending=True,
            status='published'
        ).order_by('-read_count', '-like_count')[:10]
        
        serializer = self.get_serializer(trending_stories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_stories(self, request):
        """Get current user's stories"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_stories = Story.objects.filter(author=request.user)
        
        # Apply filters
        filter_backend = DjangoFilterBackend()
        user_stories = filter_backend.filter_queryset(request, user_stories, self)
        
        page = self.paginate_queryset(user_stories)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(user_stories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_library(self, request):
        """Get user's reading library (read stories, bookmarks)"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get stories user has interacted with
        read_stories = Story.objects.filter(
            storyinteraction__user=request.user,
            storyinteraction__interaction_type='read'
        ).distinct()
        
        bookmarked_stories = Story.objects.filter(
            storyinteraction__user=request.user,
            storyinteraction__interaction_type='bookmark'
        ).distinct()
        
        return Response({
            'read_stories': StoryListSerializer(read_stories, many=True, context={'request': request}).data,
            'bookmarked_stories': StoryListSerializer(bookmarked_stories, many=True, context={'request': request}).data
        })
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available story categories"""
        categories = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Story.CATEGORY_CHOICES
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

class StoryCollectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Story Collections
    """
    serializer_class = StoryCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return user's collections and public collections"""
        return StoryCollection.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).select_related('user').prefetch_related('stories')
    
    def perform_create(self, serializer):
        """Set the user when creating a collection"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_story(self, request, pk=None):
        """Add a story to the collection"""
        collection = self.get_object()
        
        if collection.user != request.user:
            return Response(
                {'detail': 'You can only modify your own collections.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        story_id = request.data.get('story_id')
        if not story_id:
            return Response(
                {'detail': 'story_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            story = Story.objects.get(id=story_id, status='published')
            collection.stories.add(story)
            return Response({'message': 'Story added to collection successfully.'})
        except Story.DoesNotExist:
            return Response(
                {'detail': 'Story not found or not published.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['delete'])
    def remove_story(self, request, pk=None):
        """Remove a story from the collection"""
        collection = self.get_object()
        
        if collection.user != request.user:
            return Response(
                {'detail': 'You can only modify your own collections.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        story_id = request.data.get('story_id')
        if not story_id:
            return Response(
                {'detail': 'story_id is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            story = Story.objects.get(id=story_id)
            collection.stories.remove(story)
            return Response({'message': 'Story removed from collection successfully.'})
        except Story.DoesNotExist:
            return Response(
                {'detail': 'Story not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class StoryStatsView(APIView):
    """
    API view for story statistics
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get comprehensive story statistics"""
        # Basic counts
        total_stories = Story.objects.count()
        published_stories = Story.objects.filter(status='published').count()
        draft_stories = Story.objects.filter(status='draft').count()
        
        # Aggregate stats
        total_reads = Story.objects.aggregate(
            total=models.Sum('read_count')
        )['total'] or 0
        
        total_likes = Story.objects.aggregate(
            total=models.Sum('like_count')
        )['total'] or 0
        
        # Top stories
        trending_stories = Story.objects.filter(
            status='published'
        ).order_by('-read_count', '-like_count')[:5]
        
        featured_stories = Story.objects.filter(
            is_featured=True,
            status='published'
        )[:5]
        
        recent_stories = Story.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]
        
        stats_data = {
            'total_stories': total_stories,
            'published_stories': published_stories,
            'draft_stories': draft_stories,
            'total_reads': total_reads,
            'total_likes': total_likes,
            'trending_stories': trending_stories,
            'featured_stories': featured_stories,
            'recent_stories': recent_stories,
        }
        
        serializer = StoryStatsSerializer(stats_data)
        return Response(serializer.data)

class HeroStoryView(APIView):
    """
    API view for getting hero story (most popular/trending)
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Get the hero story for the homepage"""
        # Get the story with highest engagement score
        hero_story = Story.objects.filter(
            status='published'
        ).annotate(
            engagement_score=F('read_count') + F('like_count') * 2 + F('comment_count') * 3
        ).order_by('-engagement_score', '-is_featured', '-is_trending').first()
        
        if not hero_story:
            return Response({'detail': 'No published stories found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = StoryDetailSerializer(hero_story, context={'request': request})
        return Response(serializer.data)

class StorySearchView(APIView):
    """
    Advanced story search functionality
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Advanced search for stories"""
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        tags = request.query_params.get('tags', '').split(',') if request.query_params.get('tags') else []
        author = request.query_params.get('author', '')
        
        stories = Story.objects.filter(status='published')
        
        # Text search
        if query:
            stories = stories.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__icontains=query)
            )
        
        # Category filter
        if category:
            stories = stories.filter(category=category)
        
        # Tags filter
        if tags:
            for tag in tags:
                if tag.strip():
                    stories = stories.filter(tags__icontains=tag.strip())
        
        # Author filter
        if author:
            stories = stories.filter(
                Q(author__username__icontains=author) |
                Q(author__first_name__icontains=author) |
                Q(author__last_name__icontains=author)
            )
        
        # Order by relevance (read count and likes)
        stories = stories.order_by('-read_count', '-like_count', '-created_at')
        
        # Pagination
        from django.core.paginator import Paginator
        page_number = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 20)
        
        paginator = Paginator(stories, page_size)
        page_obj = paginator.get_page(page_number)
        
        serializer = StoryListSerializer(page_obj, many=True, context={'request': request})
        
        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'results': serializer.data
        })

class TrackStoryViewAPIView(APIView):
    """
    Track story view for analytics
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, story_id):
        """Track a story view"""
        try:
            story = Story.objects.get(id=story_id, status='published')
        except Story.DoesNotExist:
            return Response(
                {'detail': 'Story not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StoryViewSerializer(
            data=request.data,
            context={'request': request, 'story': story}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'View tracked successfully.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)