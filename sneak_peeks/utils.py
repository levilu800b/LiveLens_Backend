# sneak_peeks/utils.py
# type: ignore

import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def detect_device_type(request):
    """Detect device type from user agent"""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        return 'tablet'
    elif 'tv' in user_agent or 'smart-tv' in user_agent:
        return 'tv'
    else:
        return 'desktop'

def log_sneak_peek_activity(user, action, sneak_peek, request=None):
    """Log sneak peek-related user activity"""
    try:
        logger.info(f"User {user.username} performed {action} on sneak peek {sneak_peek.id}")
        
        # Additional logging can be added here
        # For example, save to database, send to analytics service, etc.
        
    except Exception as e:
        logger.error(f"Failed to log sneak peek activity: {e}")

def clear_sneak_peek_cache():
    """Clear all sneak peek related cache"""
    cache.delete("sneak_peek_stats")
    # Add other cache keys as needed