# analytics/services.py
# type: ignore

from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta, datetime
from typing import Dict, Any, List, Optional
import logging
import re  # Using built-in regex instead of user_agent

from .models import ContentView, UserEngagement, ContentPerformanceMetrics, UserBehaviorPattern
from authapp.models import User

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Service for tracking and analyzing user behavior and content performance
    """
    
    def __init__(self):
        self.content_models = {
            'story': 'stories.Story',
            'film': 'media_content.Film',
            'content': 'media_content.Content',
            'podcast': 'podcasts.Podcast',
            'animation': 'animations.Animation',
            'sneak_peek': 'sneak_peeks.SneakPeek'
        }
    
    def track_content_view(self, content_type: str, content_id: str, user: User = None, 
                          request_data: Dict[str, Any] = None) -> ContentView:
        """
        Track a content view with detailed analytics
        
        Args:
            content_type: Type of content (story, film, etc.)
            content_id: ID of the content
            user: User viewing the content (None for anonymous)
            request_data: Request metadata (IP, user agent, etc.)
        
        Returns:
            ContentView instance
        """
        
        try:
            # Get content type object
            ct = ContentType.objects.get(model=content_type)
            
            # Parse request data
            parsed_data = self._parse_request_data(request_data or {})
            
            # Check if this is a unique view
            is_unique = self._is_unique_view(user, ct, content_id, parsed_data.get('session_id'))
            
            # Create content view record
            content_view = ContentView.objects.create(
                user=user,
                content_type=ct,
                object_id=content_id,
                is_unique_view=is_unique,
                session_id=parsed_data.get('session_id', ''),
                ip_address=parsed_data.get('ip_address'),
                user_agent=parsed_data.get('user_agent', ''),
                device_type=parsed_data.get('device_type', 'unknown'),
                browser=parsed_data.get('browser', ''),
                os=parsed_data.get('os', ''),
                screen_resolution=parsed_data.get('screen_resolution', ''),
                country=parsed_data.get('country', ''),
                city=parsed_data.get('city', ''),
                referrer=parsed_data.get('referrer', ''),
                utm_source=parsed_data.get('utm_source', ''),
                utm_medium=parsed_data.get('utm_medium', ''),
                utm_campaign=parsed_data.get('utm_campaign', ''),
            )
            
            # Update content view count if unique
            if is_unique:
                self._increment_content_view_count(ct, content_id)
            
            return content_view
            
        except Exception as e:
            logger.error(f"Error tracking content view: {e}")
            raise
    
    def update_view_progress(self, view_id: str, duration: float, completion_percentage: float,
                           engagement_data: Dict[str, Any] = None) -> bool:
        """
        Update view progress and engagement metrics
        
        Args:
            view_id: ContentView ID
            duration: View duration in seconds
            completion_percentage: Percentage of content consumed
            engagement_data: Additional engagement metrics
        
        Returns:
            Success status
        """
        
        try:
            content_view = ContentView.objects.get(id=view_id)
            
            content_view.view_duration = duration
            content_view.completion_percentage = completion_percentage
            
            # Update engagement metrics if provided
            if engagement_data:
                content_view.likes_during_view = engagement_data.get('likes', 0)
                content_view.comments_during_view = engagement_data.get('comments', 0)
                content_view.shares_during_view = engagement_data.get('shares', 0)
                content_view.pauses_count = engagement_data.get('pauses', 0)
                content_view.seeks_count = engagement_data.get('seeks', 0)
                content_view.buffering_events = engagement_data.get('buffering_events', 0)
            
            content_view.save()
            
            # Update aggregated metrics
            self._update_content_metrics(content_view)
            
            return True
            
        except ContentView.DoesNotExist:
            logger.warning(f"ContentView {view_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating view progress: {e}")
            return False
    
    def track_user_engagement(self, user: User, content_type: str, content_id: str,
                            engagement_type: str, engagement_value: float = None,
                            engagement_data: Dict[str, Any] = None,
                            request_data: Dict[str, Any] = None) -> UserEngagement:
        """
        Track user engagement with content
        
        Args:
            user: User performing the engagement
            content_type: Type of content
            content_id: ID of the content
            engagement_type: Type of engagement (like, comment, share, etc.)
            engagement_value: Numeric value for the engagement (rating, duration, etc.)
            engagement_data: Additional engagement metadata
            request_data: Request metadata
        
        Returns:
            UserEngagement instance
        """
        
        try:
            ct = ContentType.objects.get(model=content_type)
            parsed_data = self._parse_request_data(request_data or {})
            
            # Create or update engagement
            engagement, created = UserEngagement.objects.get_or_create(
                user=user,
                content_type=ct,
                object_id=content_id,
                engagement_type=engagement_type,
                defaults={
                    'engagement_value': engagement_value,
                    'engagement_data': engagement_data or {},
                    'session_id': parsed_data.get('session_id', ''),
                    'ip_address': parsed_data.get('ip_address'),
                    'user_agent': parsed_data.get('user_agent', ''),
                }
            )
            
            if not created:
                # Update existing engagement
                engagement.engagement_value = engagement_value
                engagement.engagement_data.update(engagement_data or {})
                engagement.save()
            
            # Update content engagement counts
            self._update_content_engagement_count(ct, content_id, engagement_type, created)
            
            return engagement
            
        except Exception as e:
            logger.error(f"Error tracking user engagement: {e}")
            raise
    
    def get_content_analytics(self, content_type: str, content_id: str,
                            period_days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a piece of content
        
        Args:
            content_type: Type of content
            content_id: ID of the content
            period_days: Number of days to analyze
        
        Returns:
            Analytics data dictionary
        """
        
        try:
            ct = ContentType.objects.get(model=content_type)
            start_date = timezone.now() - timedelta(days=period_days)
            
            # Get basic view metrics
            views = ContentView.objects.filter(
                content_type=ct,
                object_id=content_id,
                started_at__gte=start_date
            )
            
            unique_views = views.filter(is_unique_view=True)
            
            analytics = {
                'period_days': period_days,
                'total_views': views.count(),
                'unique_views': unique_views.count(),
                'returning_views': views.count() - unique_views.count(),
                
                # Duration metrics
                'average_view_duration': views.aggregate(
                    avg_duration=Avg('view_duration')
                )['avg_duration'] or 0,
                
                'average_completion_rate': views.aggregate(
                    avg_completion=Avg('completion_percentage')
                )['avg_completion'] or 0,
                
                # Engagement metrics
                'total_engagements': UserEngagement.objects.filter(
                    content_type=ct,
                    object_id=content_id,
                    created_at__gte=start_date
                ).count(),
                
                # Device breakdown
                'device_breakdown': dict(views.values('device_type').annotate(
                    count=Count('device_type')
                ).values_list('device_type', 'count')),
                
                # Geographic breakdown
                'country_breakdown': dict(views.exclude(
                    country=''
                ).values('country').annotate(
                    count=Count('country')
                ).order_by('-count')[:10].values_list('country', 'count')),
                
                # Hourly view distribution
                'hourly_distribution': self._get_hourly_view_distribution(views),
                
                # Performance metrics
                'performance_metrics': self._calculate_performance_metrics(views),
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting content analytics: {e}")
            return {}
    
    def get_user_analytics(self, user: User, period_days: int = 30) -> Dict[str, Any]:
        """
        Get analytics for a specific user
        
        Args:
            user: User to analyze
            period_days: Number of days to analyze
        
        Returns:
            User analytics data
        """
        
        try:
            start_date = timezone.now() - timedelta(days=period_days)
            
            # Get user views
            user_views = ContentView.objects.filter(
                user=user,
                started_at__gte=start_date
            )
            
            # Get user engagements
            user_engagements = UserEngagement.objects.filter(
                user=user,
                created_at__gte=start_date
            )
            
            analytics = {
                'period_days': period_days,
                'total_views': user_views.count(),
                'total_watch_time': user_views.aggregate(
                    total_time=Sum('view_duration')
                )['total_time'] or 0,
                
                'average_session_duration': user_views.aggregate(
                    avg_duration=Avg('view_duration')
                )['avg_duration'] or 0,
                
                'content_type_preferences': dict(
                    user_views.values('content_type__model').annotate(
                        count=Count('content_type__model')
                    ).values_list('content_type__model', 'count')
                ),
                
                'engagement_breakdown': dict(
                    user_engagements.values('engagement_type').annotate(
                        count=Count('engagement_type')
                    ).values_list('engagement_type', 'count')
                ),
                
                'favorite_viewing_hours': self._get_user_viewing_hours(user_views),
                'favorite_devices': dict(
                    user_views.values('device_type').annotate(
                        count=Count('device_type')
                    ).values_list('device_type', 'count')
                ),
                
                'behavior_patterns': self._analyze_user_behavior_patterns(user, start_date),
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {}
    
    def _parse_request_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse request data for analytics - SIMPLIFIED VERSION"""
        
        parsed = {}
        
        # Parse user agent using simple regex instead of user_agent library
        if 'user_agent' in request_data:
            try:
                user_agent = request_data['user_agent']
                parsed['user_agent'] = user_agent
                
                # Simple device type detection
                user_agent_lower = user_agent.lower()
                if any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone']):
                    parsed['device_type'] = 'mobile'
                elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
                    parsed['device_type'] = 'tablet'
                elif any(desktop in user_agent_lower for desktop in ['windows', 'mac', 'linux']):
                    parsed['device_type'] = 'desktop'
                else:
                    parsed['device_type'] = 'unknown'
                
                # Simple browser detection
                if 'chrome' in user_agent_lower:
                    parsed['browser'] = 'Chrome'
                elif 'firefox' in user_agent_lower:
                    parsed['browser'] = 'Firefox'
                elif 'safari' in user_agent_lower:
                    parsed['browser'] = 'Safari'
                elif 'edge' in user_agent_lower:
                    parsed['browser'] = 'Edge'
                else:
                    parsed['browser'] = 'Unknown'
                
                # Simple OS detection
                if 'windows' in user_agent_lower:
                    parsed['os'] = 'Windows'
                elif 'mac' in user_agent_lower:
                    parsed['os'] = 'macOS'
                elif 'linux' in user_agent_lower:
                    parsed['os'] = 'Linux'
                elif 'android' in user_agent_lower:
                    parsed['os'] = 'Android'
                elif 'ios' in user_agent_lower or 'iphone' in user_agent_lower:
                    parsed['os'] = 'iOS'
                else:
                    parsed['os'] = 'Unknown'
                    
            except Exception as e:
                logger.warning(f"Error parsing user agent: {e}")
                parsed['device_type'] = 'unknown'
                parsed['browser'] = 'Unknown'
                parsed['os'] = 'Unknown'
        
        # Copy other fields
        fields = ['ip_address', 'session_id', 'referrer', 'utm_source', 
                 'utm_medium', 'utm_campaign', 'country', 'city', 'screen_resolution']
        
        for field in fields:
            if field in request_data:
                parsed[field] = request_data[field]
        
        return parsed
    
    def _is_unique_view(self, user: User, content_type: ContentType, 
                       content_id: str, session_id: str) -> bool:
        """Check if this is a unique view"""
        
        try:
            # Check for existing views in the last 24 hours
            day_ago = timezone.now() - timedelta(days=1)
            
            if user:
                # Check by user
                existing = ContentView.objects.filter(
                    user=user,
                    content_type=content_type,
                    object_id=content_id,
                    started_at__gte=day_ago
                ).exists()
            else:
                # Check by session for anonymous users
                existing = ContentView.objects.filter(
                    session_id=session_id,
                    content_type=content_type,
                    object_id=content_id,
                    started_at__gte=day_ago
                ).exists()
            
            return not existing
            
        except Exception as e:
            logger.warning(f"Error checking unique view: {e}")
            return True  # Default to unique if error
    
    def _increment_content_view_count(self, content_type: ContentType, content_id: str):
        """Increment view count on the actual content object"""
        
        try:
            model_class = content_type.model_class()
            content_obj = model_class.objects.get(id=content_id)
            
            if hasattr(content_obj, 'view_count'):
                content_obj.view_count = F('view_count') + 1
                content_obj.save(update_fields=['view_count'])
                
        except Exception as e:
            logger.warning(f"Error incrementing view count: {e}")
    
    def _update_content_engagement_count(self, content_type: ContentType, 
                                       content_id: str, engagement_type: str, 
                                       is_new: bool):
        """Update engagement count on the actual content object"""
        
        try:
            model_class = content_type.model_class()
            content_obj = model_class.objects.get(id=content_id)
            
            field_map = {
                'like': 'like_count',
                'comment': 'comment_count',
                'share': 'share_count',
                'download': 'download_count'
            }
            
            field_name = field_map.get(engagement_type)
            if field_name and hasattr(content_obj, field_name):
                if is_new:
                    setattr(content_obj, field_name, F(field_name) + 1)
                    content_obj.save(update_fields=[field_name])
                    
        except Exception as e:
            logger.warning(f"Error updating engagement count: {e}")
    
    def _get_hourly_view_distribution(self, views) -> Dict[int, int]:
        """Get hourly distribution of views"""
        
        try:
            hourly_data = {}
            for hour in range(24):
                hourly_data[hour] = views.filter(
                    started_at__hour=hour
                ).count()
            return hourly_data
            
        except Exception as e:
            logger.warning(f"Error getting hourly distribution: {e}")
            return {}
    
    def _calculate_performance_metrics(self, views) -> Dict[str, float]:
        """Calculate performance metrics for content"""
        
        try:
            total_views = views.count()
            if total_views == 0:
                return {}
            
            # Calculate bounce rate (views with less than 30% completion)
            low_completion_views = views.filter(completion_percentage__lt=30).count()
            bounce_rate = (low_completion_views / total_views) * 100
            
            # Calculate engagement rate
            engaged_views = views.filter(
                Q(completion_percentage__gte=50) |
                Q(likes_during_view__gt=0) |
                Q(comments_during_view__gt=0)
            ).count()
            engagement_rate = (engaged_views / total_views) * 100
            
            return {
                'bounce_rate': bounce_rate,
                'engagement_rate': engagement_rate,
                'average_buffering_events': views.aggregate(
                    avg_buffering=Avg('buffering_events')
                )['avg_buffering'] or 0,
            }
            
        except Exception as e:
            logger.warning(f"Error calculating performance metrics: {e}")
            return {}
    
    def _get_user_viewing_hours(self, user_views) -> Dict[int, int]:
        """Get user's favorite viewing hours"""
        
        try:
            hourly_views = {}
            for hour in range(24):
                hourly_views[hour] = user_views.filter(
                    started_at__hour=hour
                ).count()
            
            # Return top 5 hours
            sorted_hours = sorted(hourly_views.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_hours[:5])
            
        except Exception as e:
            logger.warning(f"Error getting user viewing hours: {e}")
            return {}
    
    def _analyze_user_behavior_patterns(self, user: User, start_date: datetime) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        
        try:
            patterns = {}
            
            # Get recent behavior patterns
            recent_patterns = UserBehaviorPattern.objects.filter(
                user=user,
                period_start__gte=start_date
            )
            
            for pattern in recent_patterns:
                patterns[pattern.behavior_type] = {
                    'data': pattern.pattern_data,
                    'confidence': pattern.confidence_score,
                    'last_updated': pattern.updated_at.isoformat()
                }
            
            return patterns
            
        except Exception as e:
            logger.warning(f"Error analyzing user behavior patterns: {e}")
            return {}
    
    def _update_content_metrics(self, content_view: ContentView):
        """Update aggregated content metrics"""
        
        try:
            # This would be called to update ContentPerformanceMetrics
            # Implementation depends on whether you want real-time or batch updates
            pass
            
        except Exception as e:
            logger.warning(f"Error updating content metrics: {e}")

# Global analytics service instance
analytics_service = AnalyticsService()

# Convenience functions
def track_content_view(content_type: str, content_id: str, user: User = None, 
                      request_data: Dict[str, Any] = None) -> ContentView:
    """Track a content view"""
    return analytics_service.track_content_view(content_type, content_id, user, request_data)

def update_view_progress(view_id: str, duration: float, completion_percentage: float,
                        engagement_data: Dict[str, Any] = None) -> bool:
    """Update view progress"""
    return analytics_service.update_view_progress(view_id, duration, completion_percentage, engagement_data)

def track_user_engagement(user: User, content_type: str, content_id: str,
                         engagement_type: str, engagement_value: float = None,
                         engagement_data: Dict[str, Any] = None,
                         request_data: Dict[str, Any] = None) -> UserEngagement:
    """Track user engagement"""
    return analytics_service.track_user_engagement(
        user, content_type, content_id, engagement_type, 
        engagement_value, engagement_data, request_data
    )

def get_content_analytics(content_type: str, content_id: str, period_days: int = 30) -> Dict[str, Any]:
    """Get content analytics"""
    return analytics_service.get_content_analytics(content_type, content_id, period_days)

def get_user_analytics(user: User, period_days: int = 30) -> Dict[str, Any]:
    """Get user analytics"""
    return analytics_service.get_user_analytics(user, period_days)