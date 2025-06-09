# search/views.py
# type: ignore

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils import timezone
import logging

# Import all content models
from stories.models import Story
from media_content.models import Film, Content
from podcasts.models import Podcast
from animations.models import Animation
from sneak_peeks.models import SneakPeek
from user_library.models import UserSearchHistory

logger = logging.getLogger(__name__)

class UniversalSearchView(APIView):
    """
    Universal search across all content types
    GET /api/search/
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            query = request.query_params.get('q', '').strip()
            content_types = request.query_params.getlist('content_type')
            category = request.query_params.get('category')
            tags = request.query_params.getlist('tags')
            min_rating = request.query_params.get('min_rating')
            author = request.query_params.get('author')
            sort_by = request.query_params.get('sort_by', 'relevance')
            limit = int(request.query_params.get('limit', 20))
            
            if not query and not content_types and not category and not tags:
                return Response({
                    'error': 'At least one search parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Track search if user is authenticated
            if request.user.is_authenticated and query:
                self._track_search(request.user, query, {
                    'content_types': content_types,
                    'category': category,
                    'tags': tags,
                    'min_rating': min_rating,
                    'author': author,
                    'sort_by': sort_by
                })
            
            # Build search results
            search_results = {
                'query': query,
                'total_results': 0,
                'results_by_type': {},
                'combined_results': []
            }
            
            # Define content models to search
            content_models = {
                'story': Story,
                'film': Film,
                'content': Content,
                'podcast': Podcast,
                'animation': Animation,
                'sneak_peek': SneakPeek
            }
            
            # Filter models based on content_types parameter
            if content_types:
                content_models = {k: v for k, v in content_models.items() if k in content_types}
            
            # Search each content type
            for content_type, model in content_models.items():
                results = self._search_model(
                    model, query, category, tags, min_rating, author, sort_by, limit
                )
                
                search_results['results_by_type'][content_type] = results
                search_results['total_results'] += len(results)
                
                # Add to combined results with content type info
                for result in results:
                    result['content_type'] = content_type
                    search_results['combined_results'].append(result)
            
            # Sort combined results
            if sort_by == 'relevance':
                search_results['combined_results'].sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            elif sort_by == 'date':
                search_results['combined_results'].sort(key=lambda x: x.get('created_at', ''), reverse=True)
            elif sort_by == 'popularity':
                search_results['combined_results'].sort(key=lambda x: x.get('view_count', 0), reverse=True)
            elif sort_by == 'rating':
                search_results['combined_results'].sort(key=lambda x: x.get('average_rating', 0), reverse=True)
            
            # Limit combined results
            search_results['combined_results'] = search_results['combined_results'][:limit]
            
            # Update search history with results count
            if request.user.is_authenticated and query:
                UserSearchHistory.objects.filter(
                    user=request.user,
                    query=query
                ).update(results_count=search_results['total_results'])
            
            return Response({
                'success': True,
                'search_results': search_results,
                'filters_applied': {
                    'content_types': content_types,
                    'category': category,
                    'tags': tags,
                    'min_rating': min_rating,
                    'author': author,
                    'sort_by': sort_by
                },
                'pagination': {
                    'limit': limit,
                    'has_more': search_results['total_results'] > limit
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in universal search: {e}")
            return Response({
                'error': 'Search failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _search_model(self, model, query, category, tags, min_rating, author, sort_by, limit):
        """Search within a specific model"""
        
        queryset = model.objects.filter(status='published')
        
        # Text search
        if query:
            q_objects = Q()
            search_fields = ['title']
            
            # Add description field if it exists
            if hasattr(model, 'description'):
                search_fields.append('description')
            if hasattr(model, 'content'):
                search_fields.append('content')
            if hasattr(model, 'short_description'):
                search_fields.append('short_description')
            
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        
        # Category filter
        if category and hasattr(model, 'category'):
            queryset = queryset.filter(category=category)
        
        # Tags filter
        if tags and hasattr(model, 'tags'):
            for tag in tags:
                if hasattr(model._meta.get_field('tags'), 'related_model'):
                    # If tags is a many-to-many field
                    queryset = queryset.filter(tags__name__icontains=tag)
                else:
                    # If tags is a JSONField or CharField
                    queryset = queryset.filter(tags__icontains=tag)
        
        # Rating filter
        if min_rating and hasattr(model, 'average_rating'):
            queryset = queryset.filter(average_rating__gte=min_rating)
        
        # Author filter
        if author and hasattr(model, 'author'):
            queryset = queryset.filter(
                Q(author__first_name__icontains=author) |
                Q(author__last_name__icontains=author) |
                Q(author__username__icontains=author)
            )
        
        # Sorting
        if sort_by == 'date':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'popularity':
            queryset = queryset.order_by('-view_count')
        elif sort_by == 'rating' and hasattr(model, 'average_rating'):
            queryset = queryset.order_by('-average_rating')
        else:
            # Default relevance sorting
            queryset = queryset.order_by('-view_count', '-created_at')
        
        # Execute query and serialize
        results = []
        for obj in queryset[:limit]:
            result = self._serialize_search_result(obj, query)
            results.append(result)
        
        return results
    
    def _serialize_search_result(self, obj, query=None):
        """Serialize a search result object"""
        
        result = {
            'id': str(obj.id),
            'title': obj.title,
            'created_at': obj.created_at.isoformat() if obj.created_at else None,
            'view_count': getattr(obj, 'view_count', 0),
            'like_count': getattr(obj, 'like_count', 0),
            'status': getattr(obj, 'status', 'published'),
        }
        
        # Add optional fields
        if hasattr(obj, 'description'):
            result['description'] = obj.description[:200] + ('...' if len(obj.description) > 200 else '')
        
        if hasattr(obj, 'short_description'):
            result['short_description'] = obj.short_description
        
        if hasattr(obj, 'category'):
            result['category'] = obj.category
        
        if hasattr(obj, 'tags'):
            result['tags'] = obj.tags if isinstance(obj.tags, list) else str(obj.tags)
        
        if hasattr(obj, 'author'):
            result['author'] = obj.author.full_name if obj.author else None
        
        if hasattr(obj, 'duration'):
            result['duration'] = obj.duration
        
        if hasattr(obj, 'average_rating'):
            result['average_rating'] = obj.average_rating
        
        # Thumbnail/poster
        if hasattr(obj, 'thumbnail') and obj.thumbnail:
            result['thumbnail'] = obj.thumbnail.url if hasattr(obj.thumbnail, 'url') else str(obj.thumbnail)
        
        if hasattr(obj, 'poster') and obj.poster:
            result['poster'] = obj.poster.url if hasattr(obj.poster, 'url') else str(obj.poster)
        
        # Calculate relevance score if query provided
        if query:
            result['relevance_score'] = self._calculate_relevance_score(obj, query)
        
        return result
    
    def _calculate_relevance_score(self, obj, query):
        """Calculate relevance score for search result"""
        
        score = 0
        query_lower = query.lower()
        
        # Title match (highest weight)
        if hasattr(obj, 'title') and query_lower in obj.title.lower():
            if obj.title.lower().startswith(query_lower):
                score += 100  # Exact title start match
            else:
                score += 50   # Title contains match
        
        # Description match
        if hasattr(obj, 'description') and obj.description and query_lower in obj.description.lower():
            score += 20
        
        # Category match
        if hasattr(obj, 'category') and obj.category and query_lower in obj.category.lower():
            score += 15
        
        # Author match
        if hasattr(obj, 'author') and obj.author:
            author_name = f"{obj.author.first_name} {obj.author.last_name}".lower()
            if query_lower in author_name:
                score += 10
        
        # Popularity boost
        if hasattr(obj, 'view_count'):
            score += min(obj.view_count / 100, 20)  # Max 20 points for popularity
        
        # Recent content boost
        if hasattr(obj, 'created_at'):
            days_old = (timezone.now() - obj.created_at).days
            if days_old <= 7:
                score += 10
            elif days_old <= 30:
                score += 5
        
        return score
    
    def _track_search(self, user, query, filters):
        """Track user search for analytics and recommendations"""
        
        try:
            UserSearchHistory.objects.create(
                user=user,
                query=query,
                filters_applied=filters
            )
        except Exception as e:
            logger.warning(f"Failed to track search: {e}")

class SearchSuggestionsView(APIView):
    """
    Get search suggestions based on popular searches and user history
    GET /api/search/suggestions/
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            query = request.query_params.get('q', '').strip()
            limit = int(request.query_params.get('limit', 10))
            
            suggestions = []
            
            # Get popular searches from cache
            cache_key = 'popular_searches'
            popular_searches = cache.get(cache_key)
            
            if not popular_searches:
                # Calculate popular searches
                popular_searches = list(
                    UserSearchHistory.objects.values('query')
                    .annotate(search_count=Count('query'))
                    .filter(search_count__gt=1)
                    .order_by('-search_count')[:50]
                )
                cache.set(cache_key, popular_searches, 3600)  # Cache for 1 hour
            
            # Filter suggestions based on query
            if query:
                filtered_suggestions = [
                    item['query'] for item in popular_searches
                    if query.lower() in item['query'].lower()
                ][:limit]
            else:
                filtered_suggestions = [item['query'] for item in popular_searches[:limit]]
            
            # Add user's recent searches if authenticated
            if request.user.is_authenticated:
                recent_searches = UserSearchHistory.objects.filter(
                    user=request.user
                ).order_by('-created_at')[:5].values_list('query', flat=True)
                
                # Add unique recent searches
                for search in recent_searches:
                    if search not in filtered_suggestions:
                        filtered_suggestions.append(search)
                        if len(filtered_suggestions) >= limit:
                            break
            
            # Get trending content titles as suggestions
            trending_suggestions = self._get_trending_content_suggestions(query, limit - len(filtered_suggestions))
            filtered_suggestions.extend(trending_suggestions)
            
            return Response({
                'success': True,
                'suggestions': filtered_suggestions[:limit],
                'query': query
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return Response({
                'error': 'Failed to get suggestions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_trending_content_suggestions(self, query, limit):
        """Get trending content titles as search suggestions"""
        
        suggestions = []
        
        try:
            # Get trending stories
            trending_stories = Story.objects.filter(
                status='published'
            ).order_by('-view_count')[:limit//2]
            
            for story in trending_stories:
                if not query or query.lower() in story.title.lower():
                    suggestions.append(story.title)
            
            # Get trending films
            trending_films = Film.objects.filter(
                status='published'
            ).order_by('-view_count')[:limit//2]
            
            for film in trending_films:
                if not query or query.lower() in film.title.lower():
                    suggestions.append(film.title)
                    
        except Exception as e:
            logger.warning(f"Error getting trending suggestions: {e}")
        
        return suggestions[:limit]

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_filters(request):
    """
    Get available search filters (categories, tags, etc.)
    GET /api/search/filters/
    """
    
    try:
        # Get unique categories from all content types
        categories = set()
        
        # Collect categories from each model
        for model in [Story, Film, Content, Podcast, Animation, SneakPeek]:
            if hasattr(model, 'category'):
                model_categories = model.objects.filter(
                    status='published'
                ).values_list('category', flat=True).distinct()
                categories.update(model_categories)
        
        # Get popular tags
        popular_tags = []
        try:
            # This would need to be adapted based on your tag implementation
            # For now, we'll provide common tags
            popular_tags = [
                'fiction', 'non-fiction', 'comedy', 'drama', 'action',
                'sci-fi', 'fantasy', 'horror', 'documentary', 'educational',
                'music', 'art', 'technology', 'lifestyle', 'travel'
            ]
        except Exception:
            pass
        
        # Get content types
        content_types = [
            {'value': 'story', 'label': 'Stories'},
            {'value': 'film', 'label': 'Films'},
            {'value': 'content', 'label': 'Content'},
            {'value': 'podcast', 'label': 'Podcasts'},
            {'value': 'animation', 'label': 'Animations'},
            {'value': 'sneak_peek', 'label': 'Sneak Peeks'},
        ]
        
        # Sort options
        sort_options = [
            {'value': 'relevance', 'label': 'Relevance'},
            {'value': 'date', 'label': 'Date Added'},
            {'value': 'popularity', 'label': 'Most Popular'},
            {'value': 'rating', 'label': 'Highest Rated'},
        ]
        
        return Response({
            'success': True,
            'filters': {
                'categories': sorted(list(categories)),
                'tags': popular_tags,
                'content_types': content_types,
                'sort_options': sort_options,
                'rating_options': [1, 2, 3, 4, 5]
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting search filters: {e}")
        return Response({
            'error': 'Failed to get search filters'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)