# user_library/views.py
# type: ignore

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta
import logging

from .models import (
    UserLibrary, UserFavorites, UserPlaylist, 
    UserPlaylistItem, UserContentRecommendation, UserSearchHistory
)
from .serializers import (
    UserLibrarySerializer, UserFavoritesSerializer, UserPlaylistSerializer,
    UserPlaylistItemSerializer, UserContentRecommendationSerializer
)

logger = logging.getLogger(__name__)

class UserLibraryListView(generics.ListAPIView):
    """
    Get user's library items with filtering
    GET /api/user-library/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserLibrarySerializer
    
    def get_queryset(self):
        queryset = UserLibrary.objects.filter(user=self.request.user)
        
        # Filter by interaction type
        interaction_type = self.request.query_params.get('interaction_type')
        if interaction_type:
            queryset = queryset.filter(interaction_type=interaction_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type')
        if content_type:
            try:
                ct = ContentType.objects.get(model=content_type)
                queryset = queryset.filter(content_type=ct)
            except ContentType.DoesNotExist:
                pass
        
        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        
        return queryset.select_related('content_type').order_by('-last_accessed')

class UpdateProgressView(APIView):
    """
    Update progress for a content item
    POST /api/user-library/update-progress/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            content_type_name = request.data.get('content_type')
            object_id = request.data.get('object_id')
            current_position = request.data.get('current_position', 0)
            total_duration = request.data.get('total_duration')
            interaction_type = request.data.get('interaction_type', 'viewed')
            
            if not all([content_type_name, object_id]):
                return Response({
                    'error': 'content_type and object_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create content type
            try:
                content_type = ContentType.objects.get(model=content_type_name)
            except ContentType.DoesNotExist:
                return Response({
                    'error': f'Invalid content type: {content_type_name}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create library item
            library_item, created = UserLibrary.objects.get_or_create(
                user=request.user,
                content_type=content_type,
                object_id=object_id,
                interaction_type=interaction_type,
                defaults={
                    'current_position': current_position,
                    'total_duration': total_duration or 0,
                }
            )
            
            if not created:
                # Update existing item
                library_item.update_progress(current_position, total_duration)
                library_item.view_count += 1
                
                # Update time spent (rough calculation)
                time_since_last = (timezone.now() - library_item.last_accessed).total_seconds()
                if time_since_last < 3600:  # Less than 1 hour since last access
                    library_item.time_spent += min(time_since_last, current_position)
                
                library_item.save()
            
            serializer = UserLibrarySerializer(library_item)
            return Response({
                'success': True,
                'library_item': serializer.data,
                'message': 'Progress updated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            return Response({
                'error': 'Failed to update progress'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserFavoritesListView(generics.ListCreateAPIView):
    """
    List and create user favorites
    GET/POST /api/user-library/favorites/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserFavoritesSerializer
    
    def get_queryset(self):
        queryset = UserFavorites.objects.filter(user=self.request.user)
        
        # Filter by favorite type
        favorite_type = self.request.query_params.get('favorite_type')
        if favorite_type:
            queryset = queryset.filter(favorite_type=favorite_type)
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type')
        if content_type:
            try:
                ct = ContentType.objects.get(model=content_type)
                queryset = queryset.filter(content_type=ct)
            except ContentType.DoesNotExist:
                pass
        
        return queryset.select_related('content_type').order_by('-created_at')
    
    def perform_create(self, serializer):
        # Get content type and object
        content_type_name = self.request.data.get('content_type')
        object_id = self.request.data.get('object_id')
        
        try:
            content_type = ContentType.objects.get(model=content_type_name)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError({'content_type': 'Invalid content type'})
        
        serializer.save(
            user=self.request.user,
            content_type=content_type,
            object_id=object_id
        )

class ToggleFavoriteView(APIView):
    """
    Toggle favorite status for content
    POST /api/user-library/toggle-favorite/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            content_type_name = request.data.get('content_type')
            object_id = request.data.get('object_id')
            favorite_type = request.data.get('favorite_type', 'like')
            
            if not all([content_type_name, object_id]):
                return Response({
                    'error': 'content_type and object_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                content_type = ContentType.objects.get(model=content_type_name)
            except ContentType.DoesNotExist:
                return Response({
                    'error': f'Invalid content type: {content_type_name}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if favorite exists
            favorite = UserFavorites.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=object_id,
                favorite_type=favorite_type
            ).first()
            
            if favorite:
                # Remove favorite
                favorite.delete()
                return Response({
                    'success': True,
                    'action': 'removed',
                    'message': 'Removed from favorites'
                }, status=status.HTTP_200_OK)
            else:
                # Add favorite
                favorite = UserFavorites.objects.create(
                    user=request.user,
                    content_type=content_type,
                    object_id=object_id,
                    favorite_type=favorite_type
                )
                
                serializer = UserFavoritesSerializer(favorite)
                return Response({
                    'success': True,
                    'action': 'added',
                    'favorite': serializer.data,
                    'message': 'Added to favorites'
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            return Response({
                'error': 'Failed to toggle favorite'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserPlaylistListCreateView(generics.ListCreateAPIView):
    """
    List and create user playlists
    GET/POST /api/user-library/playlists/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPlaylistSerializer
    
    def get_queryset(self):
        return UserPlaylist.objects.filter(user=self.request.user).order_by('-updated_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserPlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a playlist
    GET/PUT/DELETE /api/user-library/playlists/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserPlaylistSerializer
    
    def get_queryset(self):
        return UserPlaylist.objects.filter(user=self.request.user)

class AddToPlaylistView(APIView):
    """
    Add content to a playlist
    POST /api/user-library/playlists/{playlist_id}/add-item/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, playlist_id):
        try:
            # Get playlist
            playlist = UserPlaylist.objects.get(id=playlist_id, user=request.user)
            
            content_type_name = request.data.get('content_type')
            object_id = request.data.get('object_id')
            
            if not all([content_type_name, object_id]):
                return Response({
                    'error': 'content_type and object_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                content_type = ContentType.objects.get(model=content_type_name)
            except ContentType.DoesNotExist:
                return Response({
                    'error': f'Invalid content type: {content_type_name}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if item already exists
            existing_item = UserPlaylistItem.objects.filter(
                playlist=playlist,
                content_type=content_type,
                object_id=object_id
            ).first()
            
            if existing_item:
                return Response({
                    'error': 'Item already in playlist'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get next order number
            max_order = playlist.items.aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            
            # Create playlist item
            playlist_item = UserPlaylistItem.objects.create(
                playlist=playlist,
                content_type=content_type,
                object_id=object_id,
                order=max_order + 1
            )
            
            serializer = UserPlaylistItemSerializer(playlist_item)
            return Response({
                'success': True,
                'playlist_item': serializer.data,
                'message': 'Item added to playlist'
            }, status=status.HTTP_201_CREATED)
            
        except UserPlaylist.DoesNotExist:
            return Response({
                'error': 'Playlist not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error adding to playlist: {e}")
            return Response({
                'error': 'Failed to add item to playlist'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_recommendations(request):
    """
    Get personalized content recommendations
    GET /api/user-library/recommendations/
    """
    
    try:
        # Get active recommendations
        recommendations = UserContentRecommendation.objects.filter(
            user=request.user,
            expires_at__gt=timezone.now(),
            dismissed=False
        ).select_related('content_type').order_by('-confidence_score')[:20]
        
        # Group by recommendation type
        grouped_recommendations = {}
        for rec in recommendations:
            rec_type = rec.recommendation_type
            if rec_type not in grouped_recommendations:
                grouped_recommendations[rec_type] = []
            grouped_recommendations[rec_type].append(rec)
        
        # Serialize recommendations
        serializer = UserContentRecommendationSerializer(recommendations, many=True)
        
        return Response({
            'success': True,
            'recommendations': serializer.data,
            'grouped_recommendations': {
                rec_type: UserContentRecommendationSerializer(items, many=True).data
                for rec_type, items in grouped_recommendations.items()
            },
            'total_count': len(recommendations)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return Response({
            'error': 'Failed to get recommendations'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_dashboard_summary(request):
    """
    Get user dashboard summary with library stats
    GET /api/user-library/dashboard-summary/
    """
    
    try:
        user = request.user
        
        # Library statistics
        library_stats = {
            'total_items': UserLibrary.objects.filter(user=user).count(),
            'completed_items': UserLibrary.objects.filter(user=user, status='completed').count(),
            'in_progress_items': UserLibrary.objects.filter(user=user, status='in_progress').count(),
            'total_favorites': UserFavorites.objects.filter(user=user).count(),
            'total_playlists': UserPlaylist.objects.filter(user=user).count(),
        }
        
        # Recent activity
        recent_library_items = UserLibrary.objects.filter(
            user=user
        ).order_by('-last_accessed')[:5]
        
        recent_favorites = UserFavorites.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
        
        # Continue watching
        continue_watching = UserLibrary.objects.filter(
            user=user,
            status='in_progress',
            progress_percentage__gt=5,
            progress_percentage__lt=95
        ).order_by('-last_accessed')[:10]
        
        return Response({
            'success': True,
            'library_stats': library_stats,
            'recent_library_items': UserLibrarySerializer(recent_library_items, many=True).data,
            'recent_favorites': UserFavoritesSerializer(recent_favorites, many=True).data,
            'continue_watching': UserLibrarySerializer(continue_watching, many=True).data,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        return Response({
            'error': 'Failed to get dashboard summary'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)