# admin_dashboard/views.py
# type: ignore

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum, Avg, Q, F
from django.db import models
from django.utils import timezone
from datetime import timedelta, date
from django.core.cache import cache
import logging
from rest_framework.pagination import PageNumberPagination


# Import custom permissions
from authapp.permissions import IsAdminUser, CanViewDashboard, CanManageContent, CanManageUsers

# Import models
from .models import DashboardStats, ContentAnalytics, UserActivity, SystemAlert, ReportGeneration
from authapp.models import User
from stories.models import Story
from media_content.models import Film, Content
from podcasts.models import Podcast
from animations.models import Animation
from sneak_peeks.models import SneakPeek
from comments.models import Comment

# Import serializers
from .serializers import (
    DashboardOverviewSerializer, ContentAnalyticsSerializer, UserActivitySerializer,
    SystemAlertSerializer, ReportGenerationSerializer
)

logger = logging.getLogger(__name__)



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# Dashboard Overview
@api_view(['GET'])
@permission_classes([CanViewDashboard])
def dashboard_overview(request):
    """
    Get comprehensive dashboard overview data
    GET /api/admin-dashboard/overview/
    """
    
    try:
        # Cache key for dashboard data
        cache_key = f"dashboard_overview_{timezone.now().date()}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)
        
        # Calculate date ranges
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # User Statistics
        total_users = User.objects.count()
        new_users_today = User.objects.filter(created_at__date=today).count()
        new_users_yesterday = User.objects.filter(created_at__date=yesterday).count()
        active_users_today = User.objects.filter(last_login__date=today).count()
        
        # Calculate user growth percentage
        user_growth_percentage = 0
        if new_users_yesterday > 0:
            user_growth_percentage = ((new_users_today - new_users_yesterday) / new_users_yesterday) * 100
        
        # Content Statistics
        total_stories = Story.objects.filter(status='published').count()
        total_films = Film.objects.filter(status='published').count()
        total_content = Content.objects.filter(status='published').count()
        total_podcasts = Podcast.objects.filter(status='published').count()
        total_animations = Animation.objects.filter(status='published').count()
        total_sneak_peeks = SneakPeek.objects.filter(status='published').count()
        
        total_content_count = (
            total_stories + total_films + total_content + 
            total_podcasts + total_animations + total_sneak_peeks
        )
        
        content_by_type = {
            'stories': total_stories,
            'films': total_films,
            'content': total_content,
            'podcasts': total_podcasts,
            'animations': total_animations,
            'sneak_peeks': total_sneak_peeks
        }
        
        # Engagement Statistics (for today)
        total_views_today = (
            (Story.objects.filter(updated_at__date=today).aggregate(Sum('view_count'))['view_count__sum'] or 0) +
            (Film.objects.filter(updated_at__date=today).aggregate(Sum('view_count'))['view_count__sum'] or 0) +
            (Content.objects.filter(updated_at__date=today).aggregate(Sum('view_count'))['view_count__sum'] or 0) +
            (Podcast.objects.filter(updated_at__date=today).aggregate(Sum('view_count'))['view_count__sum'] or 0) +
            (Animation.objects.filter(updated_at__date=today).aggregate(Sum('view_count'))['view_count__sum'] or 0) +
            (SneakPeek.objects.filter(updated_at__date=today).aggregate(Sum('view_count'))['view_count__sum'] or 0)
        )
        
        total_likes_today = (
            (Story.objects.filter(updated_at__date=today).aggregate(Sum('like_count'))['like_count__sum'] or 0) +
            (Film.objects.filter(updated_at__date=today).aggregate(Sum('like_count'))['like_count__sum'] or 0) +
            (Content.objects.filter(updated_at__date=today).aggregate(Sum('like_count'))['like_count__sum'] or 0) +
            (Podcast.objects.filter(updated_at__date=today).aggregate(Sum('like_count'))['like_count__sum'] or 0) +
            (Animation.objects.filter(updated_at__date=today).aggregate(Sum('like_count'))['like_count__sum'] or 0) +
            (SneakPeek.objects.filter(updated_at__date=today).aggregate(Sum('like_count'))['like_count__sum'] or 0)
        )
        
        total_comments_today = Comment.objects.filter(created_at__date=today).count()
        
        # Most viewed content (across all types)
        most_viewed_stories = Story.objects.filter(status='published').order_by('-view_count')[:3]
        most_viewed_films = Film.objects.filter(status='published').order_by('-view_count')[:3]
        most_viewed_content = Content.objects.filter(status='published').order_by('-view_count')[:3]
        
        # Trending content (high engagement in last 7 days)
        trending_content = []
        
        # Get trending stories
        trending_stories = Story.objects.filter(
            status='published',
            updated_at__gte=week_ago
        ).annotate(
            engagement_score=F('view_count') + F('like_count') * 2
        ).order_by('-engagement_score')[:5]
        
        for story in trending_stories:
            trending_content.append({
                'type': 'story',
                'id': str(story.id),
                'title': story.title,
                'view_count': story.view_count,
                'like_count': story.like_count,
                'engagement_score': story.view_count + (story.like_count * 2)
            })
        
        # Recent Activities
        recent_user_signups = User.objects.filter(
            created_at__gte=week_ago
        ).order_by('-created_at')[:5].values(
            'id', 'first_name', 'last_name', 'email', 'created_at'
        )
        
        recent_comments = Comment.objects.filter(
            created_at__gte=week_ago
        ).select_related('user').order_by('-created_at')[:5]
        
        recent_comments_data = []
        for comment in recent_comments:
            recent_comments_data.append({
                'id': str(comment.id),
                'user': comment.user.full_name if comment.user else 'Anonymous',
                'content': comment.content[:100] + '...' if len(comment.content) > 100 else comment.content,
                'created_at': comment.created_at
            })
        
        # System Health
        system_alerts = SystemAlert.objects.filter(is_resolved=False)
        critical_alerts = system_alerts.filter(priority='critical')
        
        # Performance Metrics (mock data - implement actual calculations)
        average_session_duration = 25.5  # minutes
        bounce_rate = 15.2  # percentage
        conversion_rate = 3.8  # percentage
        storage_usage_percentage = 45.6  # percentage
        
        dashboard_data = {
            # User statistics
            'total_users': total_users,
            'active_users_today': active_users_today,
            'new_users_today': new_users_today,
            'user_growth_percentage': round(user_growth_percentage, 2),
            
            # Content statistics
            'total_content': total_content_count,
            'content_by_type': content_by_type,
            'most_viewed_content': {
                'stories': [{'id': str(s.id), 'title': s.title, 'views': s.view_count} for s in most_viewed_stories],
                'films': [{'id': str(f.id), 'title': f.title, 'views': f.view_count} for f in most_viewed_films],
                'content': [{'id': str(c.id), 'title': c.title, 'views': c.view_count} for c in most_viewed_content],
            },
            'trending_content': trending_content,
            
            # Engagement statistics
            'total_views_today': total_views_today,
            'total_likes_today': total_likes_today,
            'total_comments_today': total_comments_today,
            'total_shares_today': 0,  # Implement when sharing feature is added
            
            # Performance metrics
            'average_session_duration': average_session_duration,
            'bounce_rate': bounce_rate,
            'conversion_rate': conversion_rate,
            
            # Recent activities
            'recent_user_signups': list(recent_user_signups),
            'recent_content_uploads': [],  # Will be populated from content upload activities
            'recent_comments': recent_comments_data,
            
            # System health
            'system_alerts_count': system_alerts.count(),
            'critical_alerts_count': critical_alerts.count(),
            'server_uptime': '99.9%',  # Implement actual uptime calculation
            'storage_usage_percentage': storage_usage_percentage,
        }
        
        # Cache the data for 5 minutes
        cache.set(cache_key, dashboard_data, 300)
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in dashboard_overview: {e}")
        return Response({
            'error': 'Failed to fetch dashboard data',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([CanViewDashboard])
def analytics_summary(request):
    """
    Get analytics summary data
    GET /api/admin-dashboard/analytics/
    """
    
    try:
        # Get analytics for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        analytics_data = ContentAnalytics.objects.filter(
            date__gte=thirty_days_ago.date()
        ).aggregate(
            total_views=Sum('views_count'),
            total_likes=Sum('likes_count'),
            total_comments=Sum('comments_count'),
            avg_completion_rate=Avg('completion_rate'),
            avg_performance_score=Avg('performance_score')
        )
        
        # Get top performing content
        top_content = ContentAnalytics.objects.filter(
            date__gte=thirty_days_ago.date()
        ).order_by('-performance_score')[:10]
        
        serializer = ContentAnalyticsSerializer(top_content, many=True)
        
        return Response({
            'summary': analytics_data,
            'top_content': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in analytics_summary: {e}")
        return Response({
            'error': 'Failed to fetch analytics data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([CanManageUsers])
def user_management_stats(request):
    """
    Get user management statistics
    GET /api/admin-dashboard/user-stats/
    """
    
    try:
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        user_stats = {
            'total_users': User.objects.count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'admin_users': User.objects.filter(is_admin_user=True).count(),
            'active_users_this_week': User.objects.filter(last_login__gte=week_ago).count(),
            'new_users_this_month': User.objects.filter(created_at__gte=month_ago).count(),
            'users_by_country': list(
                User.objects.exclude(country__isnull=True)
                .exclude(country='')
                .values('country')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            ),
            'recent_users': User.objects.order_by('-created_at')[:10].values(
                'id', 'first_name', 'last_name', 'email', 'created_at', 'is_verified', 'is_admin_user'
            )
        }
        
        return Response(user_stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in user_management_stats: {e}")
        return Response({
            'error': 'Failed to fetch user stats'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Content Analytics List View
class ContentAnalyticsListView(generics.ListAPIView):
    """
    List content analytics with filtering and pagination
    GET /api/admin-dashboard/content-analytics/
    """
    permission_classes = [CanViewDashboard]
    serializer_class = ContentAnalyticsSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = ContentAnalytics.objects.all().order_by('-date', '-performance_score')
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset

# User Activities List View
class UserActivityListView(generics.ListAPIView):
    """
    List user activities with filtering and pagination
    GET /api/admin-dashboard/user-activities/
    """
    permission_classes = [CanViewDashboard]
    serializer_class = UserActivitySerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = UserActivity.objects.select_related('user').order_by('-created_at')
        
        # Filter by activity type
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset

# System Alerts Views
class SystemAlertListCreateView(generics.ListCreateAPIView):
    """
    List and create system alerts
    GET/POST /api/admin-dashboard/alerts/
    """
    permission_classes = [CanViewDashboard]
    serializer_class = SystemAlertSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = SystemAlert.objects.order_by('-created_at')
        
        # Filter by alert type
        alert_type = self.request.query_params.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by resolved status
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        
        return queryset

class SystemAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a system alert
    GET/PUT/DELETE /api/admin-dashboard/alerts/{id}/
    """
    permission_classes = [CanViewDashboard]
    serializer_class = SystemAlertSerializer
    queryset = SystemAlert.objects.all()

@api_view(['POST'])
@permission_classes([CanViewDashboard])
def mark_alerts_as_read(request):
    """
    Mark multiple alerts as read
    POST /api/admin-dashboard/alerts/mark-read/
    """
    
    alert_ids = request.data.get('alert_ids', [])
    if not alert_ids:
        return Response({
            'error': 'No alert IDs provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        updated_count = SystemAlert.objects.filter(
            id__in=alert_ids
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated_count} alerts marked as read'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error marking alerts as read: {e}")
        return Response({
            'error': 'Failed to mark alerts as read'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def resolve_alert(request, alert_id):
    """
    Resolve a system alert
    POST /api/admin-dashboard/alerts/{alert_id}/resolve/
    """
    
    try:
        alert = SystemAlert.objects.get(id=alert_id)
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.resolution_notes = request.data.get('resolution_notes', '')
        alert.save()
        
        return Response({
            'message': 'Alert resolved successfully'
        }, status=status.HTTP_200_OK)
        
    except SystemAlert.DoesNotExist:
        return Response({
            'error': 'Alert not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        return Response({
            'error': 'Failed to resolve alert'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Report Generation Views
class ReportGenerationListCreateView(generics.ListCreateAPIView):
    """
    List and create reports
    GET/POST /api/admin-dashboard/reports/
    """
    permission_classes = [CanViewDashboard]
    serializer_class = ReportGenerationSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return ReportGeneration.objects.filter(
            generated_by=self.request.user
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)

@api_view(['GET'])
@permission_classes([CanViewDashboard])
def download_report(request, report_id):
    """
    Download a generated report
    GET /api/admin-dashboard/reports/{report_id}/download/
    """
    
    try:
        report = ReportGeneration.objects.get(
            id=report_id,
            generated_by=request.user
        )
        
        if not report.file_path:
            return Response({
                'error': 'Report file not available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # In a real implementation, you would return the file
        # For now, return the file path
        return Response({
            'download_url': report.file_path,
            'filename': report.title,
            'generated_at': report.created_at
        }, status=status.HTTP_200_OK)
        
    except ReportGeneration.DoesNotExist:
        return Response({
            'error': 'Report not found'
        }, status=status.HTTP_404_NOT_FOUND)