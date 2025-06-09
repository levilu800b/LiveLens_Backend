# admin_dashboard/utils.py
# type: ignore

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def calculate_dashboard_stats():
    """Calculate comprehensive dashboard statistics"""
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    try:
        # User statistics
        total_users = User.objects.count()
        active_users_today = User.objects.filter(
            last_login__date=today
        ).count()
        new_users_today = User.objects.filter(
            date_joined__date=today
        ).count()
        new_users_yesterday = User.objects.filter(
            date_joined__date=yesterday
        ).count()
        
        # Calculate user growth percentage
        if new_users_yesterday > 0:
            user_growth_percentage = ((new_users_today - new_users_yesterday) / new_users_yesterday) * 100
        else:
            user_growth_percentage = 100.0 if new_users_today > 0 else 0.0
        
        # Content statistics
        from stories.models import Story
        from media_content.models import Film, Content
        from podcasts.models import Podcast
        from animations.models import Animation
        from sneak_peeks.models import SneakPeek
        
        content_counts = {
            'stories': Story.objects.filter(status='published').count(),
            'films': Film.objects.filter(status='published').count(),
            'content': Content.objects.filter(status='published').count(),
            'podcasts': Podcast.objects.filter(status='published').count(),
            'animations': Animation.objects.filter(status='published').count(),
            'sneak_peeks': SneakPeek.objects.filter(status='published').count(),
        }
        
        total_content = sum(content_counts.values())
        
        # Get most viewed content across all types
        most_viewed_content = {}
        
        # Stories
        top_story = Story.objects.filter(status='published').order_by('-view_count').first()
        if top_story:
            most_viewed_content['story'] = {
                'id': str(top_story.id),
                'title': top_story.title,
                'view_count': top_story.view_count,
                'type': 'story'
            }
        
        # Films
        top_film = Film.objects.filter(status='published').order_by('-view_count').first()
        if top_film:
            most_viewed_content['film'] = {
                'id': str(top_film.id),
                'title': top_film.title,
                'view_count': top_film.view_count,
                'type': 'film'
            }
        
        # Get trending content (high activity in last 7 days)
        trending_content = []
        
        # Add trending stories
        trending_stories = Story.objects.filter(
            status='published',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-view_count', '-like_count')[:3]
        
        for story in trending_stories:
            trending_content.append({
                'id': str(story.id),
                'title': story.title,
                'type': 'story',
                'view_count': story.view_count,
                'like_count': story.like_count
            })
        
        # Engagement statistics (simplified for now)
        from .models import UserActivity
        
        activities_today = UserActivity.objects.filter(created_at__date=today)
        total_views_today = activities_today.filter(activity_type='content_view').count()
        total_likes_today = activities_today.filter(activity_type='content_like').count()
        total_comments_today = activities_today.filter(activity_type='comment_post').count()
        total_shares_today = activities_today.filter(activity_type='content_share').count()
        
        # Performance metrics (mock data for now - implement based on your tracking)
        average_session_duration = 12.5  # minutes
        bounce_rate = 35.2  # percentage
        conversion_rate = 2.8  # percentage
        
        # Recent activities
        recent_user_signups = list(
            User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(hours=24)
            ).values('id', 'username', 'email', 'date_joined').order_by('-date_joined')[:5]
        )
        
        # Recent content uploads
        recent_content_uploads = []
        
        # Add recent stories
        recent_stories = Story.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).values('id', 'title', 'author__username', 'created_at').order_by('-created_at')[:3]
        
        for story in recent_stories:
            recent_content_uploads.append({
                'id': str(story['id']),
                'title': story['title'],
                'author': story['author__username'],
                'type': 'story',
                'created_at': story['created_at']
            })
        
        # Recent comments
        from comments.models import Comment
        recent_comments = list(
            Comment.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24),
                status='published'
            ).select_related('user').values(
                'id', 'text', 'user__username', 'created_at'
            ).order_by('-created_at')[:5]
        )
        
        # System health
        from .models import SystemAlert
        
        system_alerts_count = SystemAlert.objects.filter(is_resolved=False).count()
        critical_alerts_count = SystemAlert.objects.filter(
            alert_type='critical',
            is_resolved=False
        ).count()
        
        # Mock system data (implement actual monitoring)
        server_uptime = "99.9%"
        storage_usage_percentage = 67.3
        
        return {
            'total_users': total_users,
            'active_users_today': active_users_today,
            'new_users_today': new_users_today,
            'user_growth_percentage': round(user_growth_percentage, 2),
            'total_content': total_content,
            'content_by_type': content_counts,
            'most_viewed_content': most_viewed_content,
            'trending_content': trending_content,
            'total_views_today': total_views_today,
            'total_likes_today': total_likes_today,
            'total_comments_today': total_comments_today,
            'total_shares_today': total_shares_today,
            'average_session_duration': average_session_duration,
            'bounce_rate': bounce_rate,
            'conversion_rate': conversion_rate,
            'recent_user_signups': recent_user_signups,
            'recent_content_uploads': recent_content_uploads,
            'recent_comments': recent_comments,
            'system_alerts_count': system_alerts_count,
            'critical_alerts_count': critical_alerts_count,
            'server_uptime': server_uptime,
            'storage_usage_percentage': storage_usage_percentage,
        }
        
    except Exception as e:
        logger.error(f"Error calculating dashboard stats: {e}")
        return {}

def generate_content_analytics(content_type, content_id, date=None):
    """Generate analytics for a specific piece of content"""
    
    if not date:
        date = timezone.now().date()
    
    try:
        from .models import ContentAnalytics, UserActivity
        
        # Get or create analytics record
        analytics, created = ContentAnalytics.objects.get_or_create(
            content_type=content_type,
            content_id=content_id,
            date=date,
            defaults={'content_title': 'Unknown'}
        )
        
        # Calculate metrics based on user activities
        activities = UserActivity.objects.filter(
            content_type__model=content_type,
            object_id=content_id,
            created_at__date=date
        )
        
        # Update analytics
        analytics.views_count = activities.filter(activity_type='content_view').count()
        analytics.likes_count = activities.filter(activity_type='content_like').count()
        analytics.dislikes_count = activities.filter(activity_type='content_dislike').count()
        analytics.shares_count = activities.filter(activity_type='content_share').count()
        analytics.downloads_count = activities.filter(activity_type='content_download').count()
        
        # Calculate performance score
        analytics.calculate_performance_score()
        analytics.save()
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error generating content analytics: {e}")
        return None

def create_system_alert(title, message, alert_type='info', category='system', 
                       priority=1, requires_action=False, metadata=None):
    """Create a new system alert"""
    
    try:
        from .models import SystemAlert
        
        alert = SystemAlert.objects.create(
            title=title,
            message=message,
            alert_type=alert_type,
            category=category,
            priority=priority,
            requires_action=requires_action,
            metadata=metadata or {}
        )
        
        # Send notifications if critical
        if alert_type == 'critical' or priority >= 4:
            send_alert_notification(alert)
        
        return alert
        
    except Exception as e:
        logger.error(f"Error creating system alert: {e}")
        return None

def send_alert_notification(alert):
    """Send notification for system alert"""
    
    try:
        # Email notification to admins
        admin_users = User.objects.filter(is_admin=True, is_active=True)
        
        for admin in admin_users:
            # Send email (implement based on your email service)
            logger.info(f"Alert notification sent to {admin.email}: {alert.title}")
        
        # Mark as sent
        alert.email_sent = True
        alert.save()
        
    except Exception as e:
        logger.error(f"Error sending alert notification: {e}")

def cleanup_old_data():
    """Clean up old data to free up storage"""
    
    try:
        from .models import UserActivity, DashboardStats
        
        # Delete old user activities (keep only last 3 months)
        three_months_ago = timezone.now() - timedelta(days=90)
        old_activities = UserActivity.objects.filter(created_at__lt=three_months_ago)
        deleted_count = old_activities.count()
        old_activities.delete()
        
        logger.info(f"Deleted {deleted_count} old user activities")
        
        # Delete old dashboard stats (keep only last 1 year)
        one_year_ago = timezone.now() - timedelta(days=365)
        old_stats = DashboardStats.objects.filter(created_at__lt=one_year_ago)
        deleted_count = old_stats.count()
        old_stats.delete()
        
        logger.info(f"Deleted {deleted_count} old dashboard stats")
        
        # Auto-dismiss old alerts
        from .models import SystemAlert
        alerts_to_dismiss = SystemAlert.objects.filter(
            is_resolved=False,
            auto_dismiss_after__isnull=False
        )
        
        dismissed_count = 0
        for alert in alerts_to_dismiss:
            if alert.should_auto_dismiss():
                alert.is_resolved = True
                alert.resolution_notes = "Auto-dismissed due to age"
                alert.save()
                dismissed_count += 1
        
        logger.info(f"Auto-dismissed {dismissed_count} old alerts")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def export_analytics_data(date_from, date_to, content_type=None):
    """Export analytics data to CSV format"""
    
    import csv
    import io
    from .models import ContentAnalytics
    
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Content Type', 'Content ID', 'Content Title',
            'Views', 'Unique Views', 'Likes', 'Dislikes', 'Comments',
            'Shares', 'Downloads', 'Avg Watch Time', 'Completion Rate',
            'Performance Score', 'Trending Score'
        ])
        
        # Filter analytics
        analytics = ContentAnalytics.objects.filter(
            date__range=[date_from, date_to]
        )
        
        if content_type:
            analytics = analytics.filter(content_type=content_type)
        
        # Write data
        for item in analytics.order_by('-date'):
            writer.writerow([
                item.date,
                item.content_type,
                str(item.content_id),
                item.content_title,
                item.views_count,
                item.unique_views_count,
                item.likes_count,
                item.dislikes_count,
                item.comments_count,
                item.shares_count,
                item.downloads_count,
                item.average_watch_time,
                item.completion_rate,
                item.performance_score,
                item.trending_score
            ])
        
        output.seek(0)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        return None

def get_user_analytics(user_id, date_from=None, date_to=None):
    """Get analytics for a specific user"""
    
    try:
        user = User.objects.get(id=user_id)
        
        if not date_from:
            date_from = timezone.now() - timedelta(days=30)
        if not date_to:
            date_to = timezone.now()
        
        from .models import UserActivity
        
        activities = UserActivity.objects.filter(
            user=user,
            created_at__range=[date_from, date_to]
        )
        
        # Activity breakdown
        activity_breakdown = activities.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Daily activity
        daily_activity = activities.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        # Content interactions
        content_views = activities.filter(activity_type='content_view').count()
        content_likes = activities.filter(activity_type='content_like').count()
        comments_posted = activities.filter(activity_type='comment_post').count()
        
        return {
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined,
                'last_login': user.last_login
            },
            'date_range': {
                'from': date_from,
                'to': date_to
            },
            'activity_breakdown': list(activity_breakdown),
            'daily_activity': list(daily_activity),
            'summary': {
                'total_activities': activities.count(),
                'content_views': content_views,
                'content_likes': content_likes,
                'comments_posted': comments_posted,
                'avg_daily_activities': activities.count() / max((date_to - date_from).days, 1)
            }
        }
        
    except User.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        return None

def get_client_ip(request):
    """Extract client IP address from request"""
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def generate_analytics_report(report_type, date_from, date_to, filters=None):
    """Generate analytics report based on type and date range"""
    
    try:
        from .models import ContentAnalytics, UserActivity
        
        if report_type == 'content_performance':
            analytics = ContentAnalytics.objects.filter(
                date__range=[date_from, date_to]
            )
            
            if filters:
                if 'content_type' in filters:
                    analytics = analytics.filter(content_type=filters['content_type'])
            
            return {
                'type': 'content_performance',
                'date_range': {'from': date_from, 'to': date_to},
                'total_items': analytics.count(),
                'total_views': analytics.aggregate(Sum('views_count'))['views_count__sum'] or 0,
                'total_likes': analytics.aggregate(Sum('likes_count'))['likes_count__sum'] or 0,
                'avg_performance': analytics.aggregate(Avg('performance_score'))['performance_score__avg'] or 0,
                'data': list(analytics.values())
            }
        
        elif report_type == 'user_activity':
            activities = UserActivity.objects.filter(
                created_at__range=[date_from, date_to]
            )
            
            return {
                'type': 'user_activity',
                'date_range': {'from': date_from, 'to': date_to},
                'total_activities': activities.count(),
                'unique_users': activities.values('user').distinct().count(),
                'activity_breakdown': list(
                    activities.values('activity_type').annotate(count=Count('id'))
                ),
                'data': list(activities.values()[:1000])  # Limit for performance
            }
        
        else:
            return {'error': f'Unknown report type: {report_type}'}
            
    except Exception as e:
        logger.error(f"Error generating analytics report: {e}")
        return {'error': str(e)}
