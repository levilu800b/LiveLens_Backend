# type: ignore

# animations/signals.py
"""
Signals for the animations app
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Animation, AnimationInteraction

@receiver(post_save, sender=Animation)
def animation_post_save(sender, instance, created, **kwargs):
    """Handle animation post-save operations"""
    if created:
        # Log animation creation
        pass
    
    # Update published_at when status changes to published
    if instance.status == 'published' and not instance.published_at:
        instance.published_at = timezone.now()
        instance.save(update_fields=['published_at'])

@receiver(post_save, sender=AnimationInteraction)
def update_animation_counts_on_interaction(sender, instance, created, **kwargs):
    """Update animation counts when interactions are created"""
    if created:
        animation = instance.animation
        
        if instance.interaction_type == 'like':
            # Update like count
            like_count = AnimationInteraction.objects.filter(
                animation=animation,
                interaction_type='like'
            ).count()
            animation.like_count = like_count
            animation.save(update_fields=['like_count'])
        
        elif instance.interaction_type == 'rate' and instance.rating:
            # Update average rating
            ratings = AnimationInteraction.objects.filter(
                animation=animation,
                interaction_type='rate',
                rating__isnull=False
            )
            
            if ratings.exists():
                avg_rating = sum(r.rating for r in ratings) / ratings.count()
                animation.average_rating = round(avg_rating, 1)
                animation.rating_count = ratings.count()
                animation.save(update_fields=['average_rating', 'rating_count'])

@receiver(post_delete, sender=AnimationInteraction)
def update_animation_counts_on_interaction_delete(sender, instance, **kwargs):
    """Update animation counts when interactions are deleted"""
    animation = instance.animation
    
    if instance.interaction_type == 'like':
        # Update like count
        like_count = AnimationInteraction.objects.filter(
            animation=animation,
            interaction_type='like'
        ).count()
        animation.like_count = like_count
        animation.save(update_fields=['like_count'])
    
    elif instance.interaction_type == 'rate':
        # Recalculate average rating
        ratings = AnimationInteraction.objects.filter(
            animation=animation,
            interaction_type='rate',
            rating__isnull=False
        )
        
        if ratings.exists():
            avg_rating = sum(r.rating for r in ratings) / ratings.count()
            animation.average_rating = round(avg_rating, 1)
            animation.rating_count = ratings.count()
        else:
            animation.average_rating = 0.0
            animation.rating_count = 0
        
        animation.save(update_fields=['average_rating', 'rating_count'])