# type: ignore

# stories/views.py
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F
from django.shortcuts import get_object_or_404

from .models import (
    StoryCategory, Story, StoryPage, StoryIllustration,
    StoryLike, StoryView, StoryReadingProgress
)
from .serializers import (
    StoryCategorySerializer, StoryListSerializer, StoryDetailSerializer,
    StoryCreateUpdateSerializer, StoryPageSerializer, StoryIllustrationSerializer,
    StoryLikeSerializer, StoryReadingProgressSerializer
)
from .filters import StoryFilter
from .permissions import IsAuthorOrReadOnly


class StoryCategoryListView(generics.ListCreateAPIView):
    queryset = StoryCategory.objects.all()
    serializer_class = StoryCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class StoryCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StoryCategory.objects.all()
    serializer_class = StoryCategorySerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'slug'


class StoryListView(generics.ListCreateAPIView):
    queryset = Story.objects.filter(status='PUBLISHED')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = StoryFilter
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'view_count', 'like_count', 'published_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StoryCreateUpdateSerializer
        return StoryListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by featured stories
        if self.request.query_params.get('featured'):
            queryset = queryset.filter(is_featured=True)
        
        # Filter by trending stories
        if self.request.query_params.get('trending'):
            queryset = queryset.filter(is_trending=True)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class StoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Story.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StoryCreateUpdateSerializer
        return StoryDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Record story view
        self.record_view(instance, request)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def record_view(self, story, request):
        """Record a view for the story"""
        view_data = {
            'story': story,
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }
        
        if request.user.is_authenticated:
            view_data['user'] = request.user
            
            # Check if user already viewed this story today
            from django.utils import timezone
            today = timezone.now().date()
            
            if not StoryView.objects.filter(
                user=request.user,
                story=story,
                created_at__date=today
            ).exists():
                StoryView.objects.create(**view_data)
                # Increment view count
                Story.objects.filter(id=story.id).update(view_count=F('view_count') + 1)
        else:
            # For anonymous users, check by IP
            if not StoryView.objects.filter(
                ip_address=view_data['ip_address'],
                story=story,
                created_at__date=timezone.now().date()
            ).exists():
                StoryView.objects.create(**view_data)
                Story.objects.filter(id=story.id).update(view_count=F('view_count') + 1)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class StoryPageListView(generics.ListCreateAPIView):
    serializer_class = StoryPageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        story_slug = self.kwargs['story_slug']
        story = get_object_or_404(Story, slug=story_slug)
        return story.pages.all()
    
    def perform_create(self, serializer):
        story_slug = self.kwargs['story_slug']
        story = get_object_or_404(Story, slug=story_slug)
        
        # Check if user is the author
        if story.author != self.request.user:
            raise PermissionDenied("You can only add pages to your own stories.")
        
        serializer.save(story=story)


class StoryPageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StoryPageSerializer
    permission_classes = [IsAuthorOrReadOnly]
    
    def get_queryset(self):
        story_slug = self.kwargs['story_slug']
        story = get_object_or_404(Story, slug=story_slug)
        return story.pages.all()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_story_like(request, story_slug):
    """Toggle like/unlike for a story"""
    story = get_object_or_404(Story, slug=story_slug, status='PUBLISHED')
    
    like, created = StoryLike.objects.get_or_create(
        user=request.user,
        story=story
    )
    
    if created:
        # Increment like count
        Story.objects.filter(id=story.id).update(like_count=F('like_count') + 1)
        message = 'Story liked successfully'
        liked = True
    else:
        # Remove like and decrement count
        like.delete()
        Story.objects.filter(id=story.id).update(like_count=F('like_count') - 1)
        message = 'Story unliked successfully'
        liked = False
    
    return Response({
        'message': message,
        'liked': liked,
        'like_count': story.like_count + (1 if liked else -1)
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_reading_progress(request, story_slug):
    """Update user's reading progress for a story"""
    story = get_object_or_404(Story, slug=story_slug, status='PUBLISHED')
    
    current_page = request.data.get('current_page', 1)
    progress_percentage = request.data.get('progress_percentage', 0.0)
    completed = request.data.get('completed', False)
    
    progress, created = StoryReadingProgress.objects.update_or_create(
        user=request.user,
        story=story,
        defaults={
            'current_page': current_page,
            'progress_percentage': progress_percentage,
            'completed': completed
        }
    )
    
    serializer = StoryReadingProgressSerializer(progress)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_story_progress(request):
    """Get user's reading progress for all stories"""
    progress = StoryReadingProgress.objects.filter(user=request.user)
    serializer = StoryReadingProgressSerializer(progress, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def featured_stories(request):
    """Get featured stories"""
    stories = Story.objects.filter(status='PUBLISHED', is_featured=True)[:6]
    serializer = StoryListSerializer(stories, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def trending_stories(request):
    """Get trending stories"""
    stories = Story.objects.filter(status='PUBLISHED', is_trending=True)[:6]
    serializer = StoryListSerializer(stories, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def latest_stories(request):
    """Get latest published stories"""
    stories = Story.objects.filter(status='PUBLISHED').order_by('-published_at')[:10]
    serializer = StoryListSerializer(stories, many=True, context={'request': request})
    return Response(serializer.data)


class UserStoriesView(generics.ListAPIView):
    """Get stories authored by the current user"""
    serializer_class = StoryListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Story.objects.filter(author=self.request.user)


class StoryIllustrationListView(generics.ListCreateAPIView):
    serializer_class = StoryIllustrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        story_slug = self.kwargs['story_slug']
        story = get_object_or_404(Story, slug=story_slug)
        return story.illustrations.all()
    
    def perform_create(self, serializer):
        story_slug = self.kwargs['story_slug']
        story = get_object_or_404(Story, slug=story_slug)
        
        # Check if user is the author
        if story.author != self.request.user:
            raise PermissionDenied("You can only add illustrations to your own stories.")
        
        page_id = self.request.data.get('page_id')
        page = None
        if page_id:
            page = get_object_or_404(StoryPage, id=page_id, story=story)
        
        serializer.save(story=story, page=page)


class StoryIllustrationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StoryIllustrationSerializer
    permission_classes = [IsAuthorOrReadOnly]
    
    def get_queryset(self):
        story_slug = self.kwargs['story_slug']
        story = get_object_or_404(Story, slug=story_slug)
        return story.illustrations.all()