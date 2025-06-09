# recommendations/engine.py
# type: ignore

from django.db.models import Count, Q, Avg, Sum
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
from typing import List, Dict, Any, Tuple
import logging
import random

# Import models
from authapp.models import User
from user_library.models import (
    UserLibrary, UserFavorites, UserContentRecommendation,
    UserSearchHistory
)
from stories.models import Story
from media_content.models import Film, Content
from podcasts.models import Podcast
from animations.models import Animation
from sneak_peeks.models import SneakPeek
from comments.models import Comment

logger = logging.getLogger(__name__)

class ContentRecommendationEngine:
    """
    Advanced content recommendation engine using multiple algorithms
    """
    
    def __init__(self):
        self.content_models = {
            'story': Story,
            'film': Film,
            'content': Content,
            'podcast': Podcast,
            'animation': Animation,
            'sneak_peek': SneakPeek
        }
    
    def generate_recommendations_for_user(self, user: User, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Generate comprehensive recommendations for a user
        
        Args:
            user: User to generate recommendations for
            limit: Maximum number of recommendations
        
        Returns:
            List of recommendation dictionaries
        """
        
        try:
            recommendations = []
            
            # 1. Trending content (20% of recommendations)
            trending_recs = self._get_trending_recommendations(user, int(limit * 0.2))
            recommendations.extend(trending_recs)
            
            # 2. Similar to liked content (30% of recommendations)
            similar_recs = self._get_similar_content_recommendations(user, int(limit * 0.3))
            recommendations.extend(similar_recs)
            
            # 3. Genre-based recommendations (25% of recommendations)
            genre_recs = self._get_genre_based_recommendations(user, int(limit * 0.25))
            recommendations.extend(genre_recs)
            
            # 4. Collaborative filtering (15% of recommendations)
            collaborative_recs = self._get_collaborative_recommendations(user, int(limit * 0.15))
            recommendations.extend(collaborative_recs)
            
            # 5. New content (10% of recommendations)
            new_content_recs = self._get_new_content_recommendations(user, int(limit * 0.1))
            recommendations.extend(new_content_recs)
            
            # Remove duplicates and already consumed content
            recommendations = self._deduplicate_and_filter(user, recommendations)
            
            # Sort by confidence score
            recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            # Limit results
            recommendations = recommendations[:limit]
            
            # Save recommendations to database
            self._save_recommendations_to_db(user, recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user.id}: {e}")
            return self._get_fallback_recommendations(user, limit)
    
    def _get_trending_recommendations(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get trending content recommendations"""
        
        recommendations = []
        week_ago = timezone.now() - timedelta(days=7)
        
        try:
            for content_type, model in self.content_models.items():
                # Get trending content from last week
                trending_items = model.objects.filter(
                    status='published',
                    created_at__gte=week_ago
                ).annotate(
                    engagement_score=Sum('view_count') + Sum('like_count') * 2
                ).order_by('-engagement_score')[:limit//len(self.content_models) + 1]
                
                for item in trending_items:
                    recommendations.append({
                        'content_type': content_type,
                        'content_id': str(item.id),
                        'content_object': item,
                        'recommendation_type': 'trending',
                        'confidence_score': min(0.9, 0.5 + (item.view_count / 10000)),
                        'reason': f"Trending {content_type} with high engagement"
                    })
        
        except Exception as e:
            logger.warning(f"Error getting trending recommendations: {e}")
        
        return recommendations[:limit]
    
    def _get_similar_content_recommendations(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get recommendations based on similar content to user's liked items"""
        
        recommendations = []
        
        try:
            # Get user's favorite content
            user_favorites = UserFavorites.objects.filter(user=user).select_related('content_type')
            
            # Get user's highly rated content
            highly_rated = UserLibrary.objects.filter(
                user=user,
                rating__gte=4
            ).select_related('content_type')
            
            # Combine favorite and highly rated content
            liked_content = list(user_favorites) + list(highly_rated)
            
            for liked_item in liked_content:
                try:
                    content_obj = liked_item.content_object
                    if not content_obj:
                        continue
                    
                    # Find similar content based on category and tags
                    similar_items = self._find_similar_content(content_obj, limit//len(liked_content) + 1)
                    
                    for similar_item in similar_items:
                        recommendations.append({
                            'content_type': similar_item._meta.model_name,
                            'content_id': str(similar_item.id),
                            'content_object': similar_item,
                            'recommendation_type': 'similar',
                            'confidence_score': 0.8,
                            'reason': f"Similar to '{content_obj.title}' which you liked"
                        })
                
                except Exception as e:
                    logger.warning(f"Error processing similar content: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error getting similar content recommendations: {e}")
        
        return recommendations[:limit]
    
    def _get_genre_based_recommendations(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get recommendations based on user's genre preferences"""
        
        recommendations = []
        
        try:
            # Analyze user's genre preferences from library
            genre_preferences = {}
            
            user_library = UserLibrary.objects.filter(user=user).select_related('content_type')
            
            for library_item in user_library:
                content_obj = library_item.content_object
                if content_obj and hasattr(content_obj, 'category'):
                    category = content_obj.category
                    if category:
                        genre_preferences[category] = genre_preferences.get(category, 0) + 1
                        
                        # Weight by rating if available
                        if library_item.rating:
                            genre_preferences[category] += library_item.rating / 5.0
            
            # Sort genres by preference
            sorted_genres = sorted(genre_preferences.items(), key=lambda x: x[1], reverse=True)
            
            # Get recommendations for top genres
            for genre, preference_score in sorted_genres[:5]:  # Top 5 genres
                try:
                    for content_type, model in self.content_models.items():
                        if hasattr(model, 'category'):
                            genre_content = model.objects.filter(
                                status='published',
                                category=genre
                            ).order_by('-view_count', '-created_at')[:limit//10 + 1]
                            
                            for item in genre_content:
                                confidence = min(0.9, 0.4 + (preference_score / 10))
                                recommendations.append({
                                    'content_type': content_type,
                                    'content_id': str(item.id),
                                    'content_object': item,
                                    'recommendation_type': 'genre_based',
                                    'confidence_score': confidence,
                                    'reason': f"You enjoy {genre} content"
                                })
                
                except Exception as e:
                    logger.warning(f"Error getting genre recommendations for {genre}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error getting genre-based recommendations: {e}")
        
        return recommendations[:limit]
    
    def _get_collaborative_recommendations(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get recommendations based on similar users' preferences"""
        
        recommendations = []
        
        try:
            # Find users with similar preferences
            similar_users = self._find_similar_users(user, 10)
            
            for similar_user in similar_users:
                try:
                    # Get highly rated content from similar users
                    similar_user_favorites = UserLibrary.objects.filter(
                        user=similar_user,
                        rating__gte=4
                    ).select_related('content_type')[:5]
                    
                    for fav_item in similar_user_favorites:
                        content_obj = fav_item.content_object
                        if content_obj:
                            recommendations.append({
                                'content_type': fav_item.content_type.model,
                                'content_id': str(fav_item.object_id),
                                'content_object': content_obj,
                                'recommendation_type': 'collaborative',
                                'confidence_score': 0.7,
                                'reason': f"Users with similar tastes also enjoyed this"
                            })
                
                except Exception as e:
                    logger.warning(f"Error processing similar user {similar_user.id}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error getting collaborative recommendations: {e}")
        
        return recommendations[:limit]
    
    def _get_new_content_recommendations(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get recommendations for new content"""
        
        recommendations = []
        three_days_ago = timezone.now() - timedelta(days=3)
        
        try:
            for content_type, model in self.content_models.items():
                new_content = model.objects.filter(
                    status='published',
                    created_at__gte=three_days_ago
                ).order_by('-created_at')[:limit//len(self.content_models) + 1]
                
                for item in new_content:
                    recommendations.append({
                        'content_type': content_type,
                        'content_id': str(item.id),
                        'content_object': item,
                        'recommendation_type': 'new_content',
                        'confidence_score': 0.6,
                        'reason': f"New {content_type} just released"
                    })
        
        except Exception as e:
            logger.warning(f"Error getting new content recommendations: {e}")
        
        return recommendations[:limit]
    
    def _find_similar_content(self, content_obj, limit: int = 5) -> List[Any]:
        """Find content similar to the given content object"""
        
        try:
            model = content_obj.__class__
            similar_items = []
            
            # Find by same category
            if hasattr(content_obj, 'category') and content_obj.category:
                category_matches = model.objects.filter(
                    status='published',
                    category=content_obj.category
                ).exclude(id=content_obj.id).order_by('-view_count')[:limit]
                similar_items.extend(category_matches)
            
            # Find by same author
            if hasattr(content_obj, 'author') and content_obj.author:
                author_matches = model.objects.filter(
                    status='published',
                    author=content_obj.author
                ).exclude(id=content_obj.id).order_by('-created_at')[:limit//2]
                similar_items.extend(author_matches)
            
            # Remove duplicates
            seen_ids = set()
            unique_items = []
            for item in similar_items:
                if item.id not in seen_ids:
                    unique_items.append(item)
                    seen_ids.add(item.id)
            
            return unique_items[:limit]
        
        except Exception as e:
            logger.warning(f"Error finding similar content: {e}")
            return []
    
    def _find_similar_users(self, user: User, limit: int = 10) -> List[User]:
        """Find users with similar preferences"""
        
        try:
            # Get user's favorite categories
            user_categories = set()
            user_library = UserLibrary.objects.filter(user=user, rating__gte=4)
            
            for item in user_library:
                content_obj = item.content_object
                if content_obj and hasattr(content_obj, 'category'):
                    user_categories.add(content_obj.category)
            
            if not user_categories:
                return []
            
            # Find users who also like similar categories
            similar_users = []
            
            for category in user_categories:
                # Find users who rated content in this category highly
                category_users = User.objects.filter(
                    library_items__rating__gte=4,
                    library_items__content_type__in=[
                        ContentType.objects.get_for_model(model) 
                        for model in self.content_models.values()
                    ]
                ).exclude(id=user.id).distinct()[:limit//len(user_categories) + 1]
                
                similar_users.extend(category_users)
            
            # Remove duplicates and return
            return list(set(similar_users))[:limit]
        
        except Exception as e:
            logger.warning(f"Error finding similar users: {e}")
            return []
    
    def _deduplicate_and_filter(self, user: User, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and filter out already consumed content"""
        
        try:
            # Get user's already consumed content
            user_library_content = set()
            user_library = UserLibrary.objects.filter(user=user)
            
            for item in user_library:
                content_key = f"{item.content_type.model}_{item.object_id}"
                user_library_content.add(content_key)
            
            # Filter recommendations
            filtered_recs = []
            seen_content = set()
            
            for rec in recommendations:
                content_key = f"{rec['content_type']}_{rec['content_id']}"
                
                # Skip if already seen in recommendations
                if content_key in seen_content:
                    continue
                
                # Skip if user already consumed this content
                if content_key in user_library_content:
                    continue
                
                filtered_recs.append(rec)
                seen_content.add(content_key)
            
            return filtered_recs
        
        except Exception as e:
            logger.warning(f"Error filtering recommendations: {e}")
            return recommendations
    
    def _save_recommendations_to_db(self, user: User, recommendations: List[Dict[str, Any]]):
        """Save recommendations to database for tracking"""
        
        try:
            # Clear old recommendations
            UserContentRecommendation.objects.filter(
                user=user,
                expires_at__lt=timezone.now()
            ).delete()
            
            # Create new recommendations
            expires_at = timezone.now() + timedelta(days=7)  # Valid for 7 days
            
            for rec in recommendations:
                try:
                    content_type = ContentType.objects.get(model=rec['content_type'])
                    
                    UserContentRecommendation.objects.get_or_create(
                        user=user,
                        content_type=content_type,
                        object_id=rec['content_id'],
                        recommendation_type=rec['recommendation_type'],
                        defaults={
                            'confidence_score': rec['confidence_score'],
                            'reason': rec['reason'],
                            'expires_at': expires_at
                        }
                    )
                
                except Exception as e:
                    logger.warning(f"Error saving recommendation: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error saving recommendations to database: {e}")
    
    def _get_fallback_recommendations(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get fallback recommendations when main algorithm fails"""
        
        recommendations = []
        
        try:
            # Get most popular content from each type
            for content_type, model in self.content_models.items():
                popular_items = model.objects.filter(
                    status='published'
                ).order_by('-view_count')[:limit//len(self.content_models) + 1]
                
                for item in popular_items:
                    recommendations.append({
                        'content_type': content_type,
                        'content_id': str(item.id),
                        'content_object': item,
                        'recommendation_type': 'popular',
                        'confidence_score': 0.5,
                        'reason': f"Popular {content_type} content"
                    })
        
        except Exception as e:
            logger.error(f"Error getting fallback recommendations: {e}")
        
        return recommendations[:limit]

# Global recommendation engine instance
recommendation_engine = ContentRecommendationEngine()

# Convenience functions
def generate_user_recommendations(user: User, limit: int = 20) -> List[Dict[str, Any]]:
    """Generate recommendations for a user"""
    return recommendation_engine.generate_recommendations_for_user(user, limit)

def update_recommendation_engagement(user: User, content_type: str, content_id: str, action: str):
    """Update recommendation engagement (clicked, dismissed, etc.)"""
    try:
        ct = ContentType.objects.get(model=content_type)
        recommendation = UserContentRecommendation.objects.filter(
            user=user,
            content_type=ct,
            object_id=content_id
        ).first()
        
        if recommendation:
            if action == 'clicked':
                recommendation.clicked = True
            elif action == 'dismissed':
                recommendation.dismissed = True
            
            recommendation.shown_count += 1
            recommendation.save()
    
    except Exception as e:
        logger.warning(f"Error updating recommendation engagement: {e}")


