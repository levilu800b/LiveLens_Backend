# admin_content/views.py
# type: ignore

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
import logging

# Import models
from stories.models import Story
from media_content.models import Film, Content
from podcasts.models import Podcast
from animations.models import Animation
from sneak_peeks.models import SneakPeek
from comments.models import Comment
from authapp.models import User

# Import serializers
from stories.serializers import StorySerializer
from media_content.serializers import FilmSerializer, ContentSerializer
from podcasts.serializers import PodcastSerializer
from animations.serializers import AnimationSerializer
from sneak_peeks.serializers import SneakPeekSerializer

# Import utilities
from utils.file_handling import file_upload_service
from utils.ai_integration import generate_ai_story, generate_ai_animation
from authapp.permissions import CanManageContent, IsAdminUser

logger = logging.getLogger(__name__)

class AdminContentListView(APIView):
    """
    Get all content across all types for admin management
    GET /api/admin-content/all/
    """
    permission_classes = [CanManageContent]
    
    def get(self, request):
        try:
            # Get query parameters
            content_type = request.query_params.get('content_type', 'all')
            status_filter = request.query_params.get('status', 'all')
            search_query = request.query_params.get('search', '')
            author_id = request.query_params.get('author_id')
            category = request.query_params.get('category')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Build content list
            all_content = []
            
            content_models = {
                'story': Story,
                'film': Film,
                'content': Content,
                'podcast': Podcast,
                'animation': Animation,
                'sneak_peek': SneakPeek
            }
            
            content_serializers = {
                'story': StorySerializer,
                'film': FilmSerializer,
                'content': ContentSerializer,
                'podcast': PodcastSerializer,
                'animation': AnimationSerializer,
                'sneak_peek': SneakPeekSerializer
            }
            
            # Filter models based on content_type
            if content_type != 'all' and content_type in content_models:
                content_models = {content_type: content_models[content_type]}
            
            # Get content from each model
            for model_name, model_class in content_models.items():
                try:
                    queryset = model_class.objects.all()
                    
                    # Apply filters
                    if status_filter != 'all':
                        queryset = queryset.filter(status=status_filter)
                    
                    if search_query:
                        queryset = queryset.filter(
                            Q(title__icontains=search_query) |
                            Q(description__icontains=search_query)
                        )
                    
                    if author_id:
                        queryset = queryset.filter(author_id=author_id)
                    
                    if category and hasattr(model_class, 'category'):
                        queryset = queryset.filter(category=category)
                    
                    if date_from:
                        queryset = queryset.filter(created_at__gte=date_from)
                    
                    if date_to:
                        queryset = queryset.filter(created_at__lte=date_to)
                    
                    # Get items and serialize
                    for item in queryset.select_related('author').order_by('-created_at'):
                        serializer_class = content_serializers[model_name]
                        serialized_item = serializer_class(item, context={'request': request}).data
                        serialized_item['content_type'] = model_name
                        all_content.append(serialized_item)
                
                except Exception as e:
                    logger.warning(f"Error processing {model_name}: {e}")
                    continue
            
            # Sort all content by creation date
            all_content.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Paginate results
            paginator = Paginator(all_content, page_size)
            page_obj = paginator.get_page(page)
            
            # Get content statistics
            content_stats = self._get_content_statistics()
            
            return Response({
                'success': True,
                'content': page_obj.object_list,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                },
                'statistics': content_stats,
                'filters_applied': {
                    'content_type': content_type,
                    'status': status_filter,
                    'search': search_query,
                    'author_id': author_id,
                    'category': category,
                    'date_from': date_from,
                    'date_to': date_to
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting admin content list: {e}")
            return Response({
                'error': 'Failed to get content list'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_content_statistics(self):
        """Get content statistics for admin dashboard"""
        
        try:
            stats = {}
            
            # Count by content type and status
            content_models = {
                'stories': Story,
                'films': Film,
                'content': Content,
                'podcasts': Podcast,
                'animations': Animation,
                'sneak_peeks': SneakPeek
            }
            
            for name, model in content_models.items():
                stats[name] = {
                    'total': model.objects.count(),
                    'published': model.objects.filter(status='published').count(),
                    'draft': model.objects.filter(status='draft').count(),
                    'archived': model.objects.filter(status='archived').count(),
                }
                
                # Add processing status for models that have it
                if hasattr(model, 'status') and 'processing' in [choice[0] for choice in model._meta.get_field('status').choices]:
                    stats[name]['processing'] = model.objects.filter(status='processing').count()
            
            # Overall statistics
            stats['overall'] = {
                'total_content': sum(model.objects.count() for model in content_models.values()),
                'total_published': sum(model.objects.filter(status='published').count() for model in content_models.values()),
                'total_views': sum(model.objects.aggregate(total=Sum('view_count'))['total'] or 0 for model in content_models.values()),
                'total_likes': sum(model.objects.aggregate(total=Sum('like_count'))['total'] or 0 for model in content_models.values()),
                'total_comments': Comment.objects.count(),
            }
            
            return stats
            
        except Exception as e:
            logger.warning(f"Error calculating content statistics: {e}")
            return {}

class AdminStoryCreateView(APIView):
    """
    Create new story content
    POST /api/admin-content/stories/create/
    """
    permission_classes = [CanManageContent]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        try:
            # Check if this is AI-generated content
            is_ai_generated = request.data.get('is_ai_generated', False)
            
            if is_ai_generated:
                return self._create_ai_story(request)
            else:
                return self._create_manual_story(request)
                
        except Exception as e:
            logger.error(f"Error creating story: {e}")
            return Response({
                'error': 'Failed to create story'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_ai_story(self, request):
        """Create story using AI generation"""
        
        ai_prompt = request.data.get('ai_prompt')
        if not ai_prompt:
            return Response({
                'error': 'AI prompt is required for AI-generated stories'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate story content
        generated_content = generate_ai_story(
            prompt=ai_prompt,
            genre=request.data.get('genre', 'general'),
            length=request.data.get('length', 'medium'),
            tone=request.data.get('tone', 'engaging')
        )
        
        if not generated_content:
            return Response({
                'error': 'Failed to generate story content'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create story with generated content
        story_data = {
            'title': request.data.get('title', f"AI Story - {ai_prompt[:50]}"),
            'content': generated_content,
            'description': request.data.get('description', ai_prompt),
            'category': request.data.get('genre', 'general'),
            'status': request.data.get('status', 'draft'),
            'is_ai_generated': True,
            'ai_prompt': ai_prompt,
            'author': request.user.id
        }
        
        serializer = StorySerializer(data=story_data, context={'request': request})
        if serializer.is_valid():
            story = serializer.save()
            return Response({
                'success': True,
                'story': serializer.data,
                'message': 'AI story created successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Invalid story data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_manual_story(self, request):
        """Create story manually"""
        
        # Handle file uploads
        if 'thumbnail' in request.FILES:
            thumbnail_result = file_upload_service.upload_file(
                request.FILES['thumbnail'], 'image', 'stories/thumbnails'
            )
            if thumbnail_result['success']:
                request.data._mutable = True
                request.data['thumbnail'] = thumbnail_result['url']
        
        serializer = StorySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            story = serializer.save(author=request.user)
            return Response({
                'success': True,
                'story': serializer.data,
                'message': 'Story created successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Invalid story data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class AdminAnimationCreateView(APIView):
    """
    Create new animation content
    POST /api/admin-content/animations/create/
    """
    permission_classes = [CanManageContent]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        try:
            # Check if this is AI-generated content
            is_ai_generated = request.data.get('is_ai_generated', False)
            
            if is_ai_generated:
                return self._create_ai_animation(request)
            else:
                return self._create_manual_animation(request)
                
        except Exception as e:
            logger.error(f"Error creating animation: {e}")
            return Response({
                'error': 'Failed to create animation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_ai_animation(self, request):
        """Create animation using AI generation"""
        
        ai_prompt = request.data.get('ai_prompt')
        if not ai_prompt:
            return Response({
                'error': 'AI prompt is required for AI-generated animations'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate animation script
        generated_script = generate_ai_animation(
            description=ai_prompt,
            style=request.data.get('style', '2D animation'),
            duration=request.data.get('duration', '2-3 minutes'),
            target_audience=request.data.get('target_audience', 'general')
        )
        
        if not generated_script:
            return Response({
                'error': 'Failed to generate animation script'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create animation with generated script
        animation_data = {
            'title': request.data.get('title', f"AI Animation - {ai_prompt[:50]}"),
            'description': request.data.get('description', ai_prompt),
            'status': 'generating',  # Special status for AI-generated content
            'is_ai_generated': True,
            'ai_prompt': ai_prompt,
            'ai_script': generated_script.get('full_script', ''),
            'animation_software': 'AI Generated',
            'author': request.user.id
        }
        
        serializer = AnimationSerializer(data=animation_data, context={'request': request})
        if serializer.is_valid():
            animation = serializer.save()
            return Response({
                'success': True,
                'animation': serializer.data,
                'generated_script': generated_script,
                'message': 'AI animation script created successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Invalid animation data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_manual_animation(self, request):
        """Create animation manually"""
        
        # Handle file uploads
        file_uploads = {
            'thumbnail': 'animations/thumbnails',
            'poster': 'animations/posters',
            'video_file': 'animations/videos',
            'trailer_file': 'animations/trailers'
        }
        
        for field, folder in file_uploads.items():
            if field in request.FILES:
                file_type = 'video' if 'video' in field else 'image'
                upload_result = file_upload_service.upload_file(
                    request.FILES[field], file_type, folder
                )
                if upload_result['success']:
                    request.data._mutable = True
                    request.data[field] = upload_result['url']
        
        serializer = AnimationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            animation = serializer.save(author=request.user)
            return Response({
                'success': True,
                'animation': serializer.data,
                'message': 'Animation created successfully'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Invalid animation data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class AdminContentUpdateView(APIView):
    """
    Update existing content
    PUT /api/admin-content/{content_type}/{content_id}/update/
    """
    permission_classes = [CanManageContent]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def put(self, request, content_type, content_id):
        try:
            # Get the content model and object
            content_models = {
                'story': Story,
                'film': Film,
                'content': Content,
                'podcast': Podcast,
                'animation': Animation,
                'sneak_peek': SneakPeek
            }
            
            content_serializers = {
                'story': StorySerializer,
                'film': FilmSerializer,
                'content': ContentSerializer,
                'podcast': PodcastSerializer,
                'animation': AnimationSerializer,
                'sneak_peek': SneakPeekSerializer
            }
            
            if content_type not in content_models:
                return Response({
                    'error': f'Invalid content type: {content_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            model_class = content_models[content_type]
            serializer_class = content_serializers[content_type]
            
            try:
                content_obj = model_class.objects.get(id=content_id)
            except model_class.DoesNotExist:
                return Response({
                    'error': f'{content_type.title()} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Handle file uploads
            self._handle_file_uploads(request, content_type)
            
            # Update the content
            serializer = serializer_class(
                content_obj, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                updated_content = serializer.save()
                return Response({
                    'success': True,
                    'content': serializer.data,
                    'message': f'{content_type.title()} updated successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid content data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            return Response({
                'error': 'Failed to update content'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_file_uploads(self, request, content_type):
        """Handle file uploads for content update"""
        
        file_field_mapping = {
            'story': {
                'thumbnail': 'stories/thumbnails',
                'cover_image': 'stories/covers'
            },
            'film': {
                'thumbnail': 'films/thumbnails',
                'poster': 'films/posters',
                'banner': 'films/banners',
                'video_file': 'films/videos',
                'trailer_file': 'films/trailers'
            },
            'content': {
                'thumbnail': 'content/thumbnails',
                'poster': 'content/posters',
                'banner': 'content/banners',
                'video_file': 'content/videos',
                'trailer_file': 'content/trailers'
            },
            'podcast': {
                'thumbnail': 'podcasts/thumbnails',
                'cover_art': 'podcasts/covers',
                'audio_file': 'podcasts/audio'
            },
            'animation': {
                'thumbnail': 'animations/thumbnails',
                'poster': 'animations/posters',
                'video_file': 'animations/videos',
                'trailer_file': 'animations/trailers'
            },
            'sneak_peek': {
                'thumbnail': 'sneak_peeks/thumbnails',
                'poster': 'sneak_peeks/posters',
                'video_file': 'sneak_peeks/videos'
            }
        }
        
        field_mapping = file_field_mapping.get(content_type, {})
        
        for field, folder in field_mapping.items():
            if field in request.FILES:
                file_type = self._get_file_type(field)
                upload_result = file_upload_service.upload_file(
                    request.FILES[field], file_type, folder
                )
                if upload_result['success']:
                    request.data._mutable = True
                    request.data[field] = upload_result['url']
    
    def _get_file_type(self, field_name):
        """Determine file type based on field name"""
        if 'video' in field_name:
            return 'video'
        elif 'audio' in field_name:
            return 'audio'
        else:
            return 'image'

class AdminContentDeleteView(APIView):
    """
    Delete content
    DELETE /api/admin-content/{content_type}/{content_id}/delete/
    """
    permission_classes = [CanManageContent]
    
    def delete(self, request, content_type, content_id):
        try:
            content_models = {
                'story': Story,
                'film': Film,
                'content': Content,
                'podcast': Podcast,
                'animation': Animation,
                'sneak_peek': SneakPeek
            }
            
            if content_type not in content_models:
                return Response({
                    'error': f'Invalid content type: {content_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            model_class = content_models[content_type]
            
            try:
                content_obj = model_class.objects.get(id=content_id)
            except model_class.DoesNotExist:
                return Response({
                    'error': f'{content_type.title()} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Store content info before deletion
            content_title = content_obj.title
            
            # Delete the content
            content_obj.delete()
            
            return Response({
                'success': True,
                'message': f'{content_type.title()} "{content_title}" deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error deleting content: {e}")
            return Response({
                'error': 'Failed to delete content'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminContentBulkActionsView(APIView):
    """
    Perform bulk actions on content
    POST /api/admin-content/bulk-actions/
    """
    permission_classes = [CanManageContent]
    
    def post(self, request):
        try:
            action = request.data.get('action')
            content_items = request.data.get('content_items', [])  # List of {content_type, content_id}
            
            if not action or not content_items:
                return Response({
                    'error': 'Action and content_items are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            results = {
                'success_count': 0,
                'failed_count': 0,
                'errors': []
            }
            
            for item in content_items:
                try:
                    content_type = item.get('content_type')
                    content_id = item.get('content_id')
                    
                    success = self._perform_bulk_action(action, content_type, content_id, request.data)
                    
                    if success:
                        results['success_count'] += 1
                    else:
                        results['failed_count'] += 1
                        results['errors'].append(f"Failed to {action} {content_type} {content_id}")
                
                except Exception as e:
                    results['failed_count'] += 1
                    results['errors'].append(f"Error processing {item}: {str(e)}")
                    continue
            
            return Response({
                'success': True,
                'results': results,
                'message': f'Bulk {action} completed'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in bulk actions: {e}")
            return Response({
                'error': 'Failed to perform bulk actions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _perform_bulk_action(self, action, content_type, content_id, data):
        """Perform a single bulk action"""
        
        content_models = {
            'story': Story,
            'film': Film,
            'content': Content,
            'podcast': Podcast,
            'animation': Animation,
            'sneak_peek': SneakPeek
        }
        
        if content_type not in content_models:
            return False
        
        model_class = content_models[content_type]
        
        try:
            content_obj = model_class.objects.get(id=content_id)
            
            if action == 'publish':
                content_obj.status = 'published'
                if not content_obj.published_at:
                    content_obj.published_at = timezone.now()
                content_obj.save()
                return True
            
            elif action == 'unpublish':
                content_obj.status = 'draft'
                content_obj.save()
                return True
            
            elif action == 'archive':
                content_obj.status = 'archived'
                content_obj.save()
                return True
            
            elif action == 'delete':
                content_obj.delete()
                return True
            
            elif action == 'feature':
                if hasattr(content_obj, 'is_featured'):
                    content_obj.is_featured = True
                    content_obj.save()
                    return True
            
            elif action == 'unfeature':
                if hasattr(content_obj, 'is_featured'):
                    content_obj.is_featured = False
                    content_obj.save()
                    return True
            
            elif action == 'update_category':
                new_category = data.get('new_category')
                if new_category and hasattr(content_obj, 'category'):
                    content_obj.category = new_category
                    content_obj.save()
                    return True
            
            return False
            
        except model_class.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error performing bulk action {action}: {e}")
            return False

@api_view(['GET'])
@permission_classes([CanManageContent])
def admin_content_statistics(request):
    """
    Get comprehensive content statistics for admin dashboard
    GET /api/admin-content/statistics/
    """
    
    try:
        # Get date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        content_models = {
            'stories': Story,
            'films': Film,
            'content': Content,
            'podcasts': Podcast,
            'animations': Animation,
            'sneak_peeks': SneakPeek
        }
        
        statistics = {
            'period_days': days,
            'total_content': 0,
            'by_type': {},
            'by_status': {},
            'by_author': {},
            'engagement_metrics': {},
            'recent_activity': [],
            'trending_content': []
        }
        
        # Calculate statistics for each content type
        for name, model in content_models.items():
            # Basic counts
            total = model.objects.count()
            recent = model.objects.filter(created_at__gte=start_date).count()
            published = model.objects.filter(status='published').count()
            
            statistics['by_type'][name] = {
                'total': total,
                'recent': recent,
                'published': published,
                'draft': model.objects.filter(status='draft').count(),
                'archived': model.objects.filter(status='archived').count()
            }
            
            statistics['total_content'] += total
            
            # Engagement metrics
            if hasattr(model, 'view_count'):
                stats = model.objects.aggregate(
                    total_views=Sum('view_count'),
                    total_likes=Sum('like_count'),
                    avg_views=Avg('view_count')
                )
                
                statistics['engagement_metrics'][name] = {
                    'total_views': stats['total_views'] or 0,
                    'total_likes': stats['total_likes'] or 0,
                    'average_views': round(stats['avg_views'] or 0, 2)
                }
            
            # Recent activity
            recent_items = model.objects.filter(
                created_at__gte=start_date
            ).select_related('author').order_by('-created_at')[:5]
            
            for item in recent_items:
                statistics['recent_activity'].append({
                    'type': name,
                    'title': item.title,
                    'author': item.author.full_name if item.author else 'System',
                    'status': item.status,
                    'created_at': item.created_at.isoformat()
                })
            
            # Trending content (most viewed in the period)
            if hasattr(model, 'view_count'):
                trending = model.objects.filter(
                    status='published',
                    created_at__gte=start_date
                ).order_by('-view_count', '-like_count')[:3]
                
                for item in trending:
                    statistics['trending_content'].append({
                        'type': name,
                        'title': item.title,
                        'views': item.view_count,
                        'likes': item.like_count,
                        'author': item.author.full_name if item.author else 'System'
                    })
        
        # Sort activities and trending by relevance
        statistics['recent_activity'].sort(key=lambda x: x['created_at'], reverse=True)
        statistics['recent_activity'] = statistics['recent_activity'][:20]
        
        statistics['trending_content'].sort(key=lambda x: x['views'], reverse=True)
        statistics['trending_content'] = statistics['trending_content'][:10]
        
        # Top authors
        author_stats = {}
        for name, model in content_models.items():
            author_counts = model.objects.values('author__id', 'author__first_name', 'author__last_name').annotate(
                content_count=Count('id')
            ).order_by('-content_count')[:10]
            
            for author_data in author_counts:
                author_id = author_data['author__id']
                if author_id:
                    if author_id not in author_stats:
                        author_stats[author_id] = {
                            'name': f"{author_data['author__first_name']} {author_data['author__last_name']}",
                            'total_content': 0,
                            'by_type': {}
                        }
                    
                    author_stats[author_id]['total_content'] += author_data['content_count']
                    author_stats[author_id]['by_type'][name] = author_data['content_count']
        
        # Convert to sorted list
        statistics['by_author'] = sorted(
            author_stats.values(),
            key=lambda x: x['total_content'],
            reverse=True
        )[:10]
        
        return Response({
            'success': True,
            'statistics': statistics
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting content statistics: {e}")
        return Response({
            'error': 'Failed to get content statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([CanManageContent])
def admin_content_filters(request):
    """
    Get available filters for admin content management
    GET /api/admin-content/filters/
    """
    
    try:
        filters = {
            'content_types': [
                {'value': 'all', 'label': 'All Content'},
                {'value': 'story', 'label': 'Stories'},
                {'value': 'film', 'label': 'Films'},
                {'value': 'content', 'label': 'Content'},
                {'value': 'podcast', 'label': 'Podcasts'},
                {'value': 'animation', 'label': 'Animations'},
                {'value': 'sneak_peek', 'label': 'Sneak Peeks'},
            ],
            'statuses': [
                {'value': 'all', 'label': 'All Statuses'},
                {'value': 'draft', 'label': 'Draft'},
                {'value': 'published', 'label': 'Published'},
                {'value': 'archived', 'label': 'Archived'},
                {'value': 'processing', 'label': 'Processing'},
                {'value': 'generating', 'label': 'AI Generating'},
            ],
            'categories': [],
            'authors': []
        }
        
        # Get unique categories
        categories = set()
        content_models = [Story, Film, Content, Podcast, Animation, SneakPeek]
        
        for model in content_models:
            if hasattr(model, 'category'):
                model_categories = model.objects.values_list('category', flat=True).distinct()
                categories.update(filter(None, model_categories))
        
        filters['categories'] = [{'value': cat, 'label': cat.title()} for cat in sorted(categories)]
        
        # Get authors who have created content
        authors = User.objects.filter(
            Q(stories_authored__isnull=False) |
            Q(films_authored__isnull=False) |
            Q(content_authored__isnull=False) |
            Q(podcasts_authored__isnull=False) |
            Q(animations_authored__isnull=False) |
            Q(sneak_peeks_authored__isnull=False)
        ).distinct().order_by('first_name', 'last_name')
        
        filters['authors'] = [
            {'value': str(author.id), 'label': author.full_name}
            for author in authors
        ]
        
        return Response({
            'success': True,
            'filters': filters
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting content filters: {e}")
        return Response({
            'error': 'Failed to get content filters'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


