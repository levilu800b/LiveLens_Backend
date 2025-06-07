# comments/signals.py
# type: ignore

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Comment, CommentInteraction
from .utils import process_comment_mentions, send_comment_notification

@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    """Handle actions after comment is saved"""
    
    if created:
        # Process mentions in the comment
        process_comment_mentions(instance, instance.user)
        
        # Invalidate cache for comment stats
        if instance.content_type and instance.object_id:
            cache_key = f"comment_stats_{instance.content_type.model}_{instance.object_id}"
            cache.delete(cache_key)
    
    # Clear user comment cache
    cache.delete(f"user_comments_{instance.user.id}")

@receiver(post_save, sender=CommentInteraction)
def comment_interaction_post_save(sender, instance, created, **kwargs):
    """Handle actions after comment interaction is saved"""
    
    if created:
        # Invalidate cache for comment stats
        if instance.comment.content_type and instance.comment.object_id:
            cache_key = f"comment_stats_{instance.comment.content_type.model}_{instance.comment.object_id}"
            cache.delete(cache_key)

@receiver(pre_delete, sender=Comment)
def comment_pre_delete(sender, instance, **kwargs):
    """Handle actions before comment is deleted"""
    
    # Invalidate cache for comment stats
    if instance.content_type and instance.object_id:
        cache_key = f"comment_stats_{instance.content_type.model}_{instance.object_id}"
        cache.delete(cache_key)
    
    # Clear user comment cache
    cache.delete(f"user_comments_{instance.user.id}")