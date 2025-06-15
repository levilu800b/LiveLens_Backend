# ===================================================================
# admin_dashboard/utils.py (Optional - for utility functions)
# type: ignore
# ===================================================================

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Avg, Q

def calculate_platform_stats():
    """
    Utility function to calculate and cache platform statistics
    This can be called by a daily cron job to update PlatformStatistics
    """
    from django.contrib.auth import get_user_model
    from .models import PlatformStatistics
    
    User = get_user_model()
    
    today = timezone.now().date()
    
    # Calculate user stats
    total_users = User.objects.count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    active_users_today = User.objects.filter(last_login__date=today).count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    # Calculate content stats
    content_stats = {}
    
    try:
        from stories.models import Story
        content_stats['total_stories'] = Story.objects.count()
    except ImportError:
        content_stats['total_stories'] = 0
    
    try:
        from media_content.models import Film, Content
        content_stats['total_films'] = Film.objects.count()
        content_stats['total_content'] = Content.objects.count()
    except ImportError:
        content_stats['total_films'] = 0
        content_stats['total_content'] = 0
    
    try:
        from podcasts.models import Podcast
        content_stats['total_podcasts'] = Podcast.objects.count()
    except ImportError:
        content_stats['total_podcasts'] = 0
    
    try:
        from animations.models import Animation
        content_stats['total_animations'] = Animation.objects.count()
    except ImportError:
        content_stats['total_animations'] = 0
    
    try:
        from sneak_peeks.models import SneakPeek
        content_stats['total_sneak_peeks'] = SneakPeek.objects.count()
    except ImportError:
        content_stats['total_sneak_peeks'] = 0
    
    try:
        from live_video.models import LiveVideo
        content_stats['total_live_videos'] = LiveVideo.objects.count()
    except ImportError:
        content_stats['total_live_videos'] = 0
    
    # Calculate engagement stats
    try:
        from comments.models import Comment
        total_comments = Comment.objects.count()
    except ImportError:
        total_comments = 0
    
    # Create or update statistics
    stats, created = PlatformStatistics.objects.get_or_create(
        date=today,
        defaults={
            'total_users': total_users,
            'new_users_today': new_users_today,
            'active_users_today': active_users_today,
            'verified_users': verified_users,
            'total_comments': total_comments,
            **content_stats
        }
    )
    
    # If not created, update with current values
    if not created:
        for key, value in {
            'total_users': total_users,
            'new_users_today': new_users_today,
            'active_users_today': active_users_today,
            'verified_users': verified_users,
            'total_comments': total_comments,
            **content_stats
        }.items():
            setattr(stats, key, value)
        stats.save()
    
    return stats


def get_trending_content(content_type='all', limit=5):
    """
    Get trending content across different content types
    """
    trending_items = []
    
    if content_type in ['all', 'stories']:
        try:
            from stories.models import Story
            stories = Story.objects.filter(is_trending=True).order_by('-read_count')[:limit]
            for story in stories:
                trending_items.append({
                    'type': 'story',
                    'id': story.id,
                    'title': story.title,
                    'author': story.author.username,
                    'views': story.read_count,
                    'likes': story.like_count,
                    'created_at': story.created_at
                })
        except ImportError:
            pass
    
    if content_type in ['all', 'films']:
        try:
            from media_content.models import Film
            films = Film.objects.filter(is_trending=True).order_by('-view_count')[:limit]
            for film in films:
                trending_items.append({
                    'type': 'film',
                    'id': film.id,
                    'title': film.title,
                    'creator': film.creator.username,
                    'views': film.view_count,
                    'likes': film.like_count,
                    'created_at': film.created_at
                })
        except ImportError:
            pass
    
    # Sort by views descending
    trending_items.sort(key=lambda x: x['views'], reverse=True)
    
    return trending_items[:limit]


def clean_old_admin_activities(days=90):
    """
    Clean up old admin activities to prevent database bloat
    """
    from .models import AdminActivity
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count = AdminActivity.objects.filter(timestamp__lt=cutoff_date).delete()[0]
    
    return deleted_count
