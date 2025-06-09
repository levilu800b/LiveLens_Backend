# recommendations/tasks.py (for background processing)
# type: ignore

from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def generate_recommendations_for_all_active_users():
    """
    Background task to generate recommendations for all active users
    Run this daily via cron job or Celery
    """
    
    try:
        from authapp.models import User
        
        # Get active users (logged in within last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_users = User.objects.filter(
            last_login__gte=thirty_days_ago,
            is_active=True
        )
        
        logger.info(f"Generating recommendations for {active_users.count()} active users")
        
        success_count = 0
        for user in active_users:
            try:
                recommendations = generate_user_recommendations(user, 20)
                if recommendations:
                    success_count += 1
                    logger.debug(f"Generated {len(recommendations)} recommendations for user {user.id}")
            
            except Exception as e:
                logger.warning(f"Failed to generate recommendations for user {user.id}: {e}")
                continue
        
        logger.info(f"Successfully generated recommendations for {success_count}/{active_users.count()} users")
        
    except Exception as e:
        logger.error(f"Error in batch recommendation generation: {e}")

def cleanup_old_recommendations():
    """
    Cleanup expired recommendations
    """
    
    try:
        from user_library.models import UserContentRecommendation
        
        deleted_count = UserContentRecommendation.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} expired recommendations")
        
    except Exception as e:
        logger.error(f"Error cleaning up recommendations: {e}")