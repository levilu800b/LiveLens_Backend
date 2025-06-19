# authapp/user_library_views.py - DEBUG VERSION
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
import traceback


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_library(request):
    """
    Get user's complete library across all content types
    DEBUG VERSION - handles missing imports gracefully
    """
    user = request.user
    
    try:
        print(f"Library request from user: {user.email}")  # Debug log
        
        library_data = {
            'watched_stories': [],
            'watched_films': [],
            'watched_content': [],
            'watched_podcasts': [],
            'watched_animations': [],
            'watched_sneak_peeks': [],
        }
        
        # Try to import and process stories
        try:
            from stories.models import Story, StoryInteraction
            from stories.serializers import StoryListSerializer
            
            watched_stories = Story.objects.filter(
                storyinteraction__user=user,
                storyinteraction__interaction_type__in=['read', 'bookmark'],
                status='published'
            ).select_related('author').distinct()
            
            library_data['watched_stories'] = StoryListSerializer(
                watched_stories, many=True, context={'request': request}
            ).data
            
            print(f"Found {len(library_data['watched_stories'])} stories")
            
        except Exception as e:
            print(f"Stories error: {str(e)}")
            library_data['watched_stories'] = []
        
        # Try to import and process films
        try:
            from media_content.models import Film, MediaInteraction
            from media_content.serializers import FilmListSerializer
            
            watched_films = Film.objects.filter(
                mediainteraction__user=user,
                mediainteraction__interaction_type__in=['watch', 'bookmark'],
                status='published'
            ).select_related('author').distinct()
            
            library_data['watched_films'] = FilmListSerializer(
                watched_films, many=True, context={'request': request}
            ).data
            
            print(f"Found {len(library_data['watched_films'])} films")
            
        except Exception as e:
            print(f"Films error: {str(e)}")
            library_data['watched_films'] = []
        
        # Try to import and process content
        try:
            from media_content.models import Content, MediaInteraction
            from media_content.serializers import ContentListSerializer
            
            watched_content = Content.objects.filter(
                mediainteraction__user=user,
                mediainteraction__interaction_type__in=['watch', 'bookmark'],
                status='published'
            ).select_related('author').distinct()
            
            library_data['watched_content'] = ContentListSerializer(
                watched_content, many=True, context={'request': request}
            ).data
            
            print(f"Found {len(library_data['watched_content'])} content items")
            
        except Exception as e:
            print(f"Content error: {str(e)}")
            library_data['watched_content'] = []
        
        # Try to import and process podcasts
        try:
            from podcasts.models import Podcast, PodcastInteraction
            from podcasts.serializers import PodcastListSerializer
            
            listened_podcasts = Podcast.objects.filter(
                podcastinteraction__user=user,
                podcastinteraction__interaction_type__in=['listen', 'bookmark'],
                status='published'
            ).select_related('author').distinct()
            
            library_data['watched_podcasts'] = PodcastListSerializer(
                listened_podcasts, many=True, context={'request': request}
            ).data
            
            print(f"Found {len(library_data['watched_podcasts'])} podcasts")
            
        except Exception as e:
            print(f"Podcasts error: {str(e)}")
            library_data['watched_podcasts'] = []
        
        # Try to import and process animations
        try:
            from animations.models import Animation, AnimationInteraction
            from animations.serializers import AnimationListSerializer
            
            watched_animations = Animation.objects.filter(
                animationinteraction__user=user,
                animationinteraction__interaction_type__in=['watch', 'bookmark'],
                status='published'
            ).select_related('author').distinct()
            
            library_data['watched_animations'] = AnimationListSerializer(
                watched_animations, many=True, context={'request': request}
            ).data
            
            print(f"Found {len(library_data['watched_animations'])} animations")
            
        except Exception as e:
            print(f"Animations error: {str(e)}")
            library_data['watched_animations'] = []
        
        # Try to import and process sneak peeks
        try:
            from sneak_peeks.models import SneakPeek, SneakPeekInteraction
            from sneak_peeks.serializers import SneakPeekListSerializer
            
            watched_sneak_peeks = SneakPeek.objects.filter(
                sneakpeekinteraction__user=user,
                sneakpeekinteraction__interaction_type__in=['like', 'favorite'],
                status='published'
            ).select_related('author').distinct()
            
            library_data['watched_sneak_peeks'] = SneakPeekListSerializer(
                watched_sneak_peeks, many=True, context={'request': request}
            ).data
            
            print(f"Found {len(library_data['watched_sneak_peeks'])} sneak peeks")
            
        except Exception as e:
            print(f"Sneak peeks error: {str(e)}")
            library_data['watched_sneak_peeks'] = []
        
        # Add summary statistics
        library_data['summary'] = {
            'total_items': sum([
                len(library_data.get('watched_stories', [])),
                len(library_data.get('watched_films', [])),
                len(library_data.get('watched_content', [])),
                len(library_data.get('watched_podcasts', [])),
                len(library_data.get('watched_animations', [])),
                len(library_data.get('watched_sneak_peeks', [])),
            ]),
            'stories_count': len(library_data.get('watched_stories', [])),
            'films_count': len(library_data.get('watched_films', [])),
            'content_count': len(library_data.get('watched_content', [])),
            'podcasts_count': len(library_data.get('watched_podcasts', [])),
            'animations_count': len(library_data.get('watched_animations', [])),
            'sneak_peeks_count': len(library_data.get('watched_sneak_peeks', [])),
            'last_updated': timezone.now(),
        }
        
        print(f"Library summary: {library_data['summary']}")
        
        return Response(library_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Print full traceback for debugging
        print(f"FULL ERROR TRACEBACK:")
        print(traceback.format_exc())
        
        return Response({
            'error': 'Failed to fetch user library',
            'detail': str(e),
            'traceback': traceback.format_exc()  # Include traceback in response for debugging
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_favorites(request):
    """
    Get user's favorite content across all content types
    DEBUG VERSION - simplified
    """
    user = request.user
    
    try:
        print(f"Favorites request from user: {user.email}")
        
        # Return empty data for now - we'll implement this after library works
        favorites_data = {
            'stories': [],
            'films': [],
            'content': [],
            'podcasts': [],
            'animations': [],
            'sneak_peeks': [],
            'summary': {
                'total_favorites': 0,
                'stories_count': 0,
                'films_count': 0,
                'content_count': 0,
                'podcasts_count': 0,
                'animations_count': 0,
                'sneak_peeks_count': 0,
            }
        }
        
        return Response(favorites_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Favorites Error: {str(e)}")
        print(traceback.format_exc())
        
        return Response({
            'error': 'Failed to fetch user favorites',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)