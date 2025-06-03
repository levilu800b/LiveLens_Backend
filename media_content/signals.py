# type: ignore

# media_content/signals.py
"""
Signals for the media_content app
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Film, Content, MediaInteraction

@receiver(post_save, sender=Film)
def film_post_save(sender, instance, created, **kwargs):
    """Handle film post-save operations"""
    if created:
        # Log film creation
        pass
    
    # Update published_at when status changes to published
    if instance.status == 'published' and not instance.published_at:
        instance.published_at = timezone.now()
        instance.save(update_fields=['published_at'])

@receiver(post_save, sender=Content)
def content_post_save(sender, instance, created, **kwargs):
    """Handle content post-save operations"""
    if created:
        # Log content creation
        pass
    
    # Update published_at when status changes to published
    if instance.status == 'published' and not instance.published_at:
        instance.published_at = timezone.now()
        instance.save(update_fields=['published_at'])

@receiver(post_save, sender=MediaInteraction)
def update_media_counts_on_interaction(sender, instance, created, **kwargs):
    """Update media counts when interactions are created"""
    if created:
        # Get the media object
        if instance.content_type == 'film':
            from .models import Film
            media_obj = Film.objects.filter(id=instance.object_id).first()
        else:
            from .models import Content
            media_obj = Content.objects.filter(id=instance.object_id).first()
        
        if media_obj:
            if instance.interaction_type == 'like':
                # Update like count
                like_count = MediaInteraction.objects.filter(
                    content_type=instance.content_type,
                    object_id=instance.object_id,
                    interaction_type='like'
                ).count()
                media_obj.like_count = like_count
                media_obj.save(update_fields=['like_count'])
            
            elif instance.interaction_type == 'rate' and instance.rating:
                # Update average rating
                ratings = MediaInteraction.objects.filter(
                    content_type=instance.content_type,
                    object_id=instance.object_id,
                    interaction_type='rate',
                    rating__isnull=False
                )
                
                if ratings.exists():
                    avg_rating = sum(r.rating for r in ratings) / ratings.count()
                    media_obj.average_rating = round(avg_rating, 1)
                    media_obj.rating_count = ratings.count()
                    media_obj.save(update_fields=['average_rating', 'rating_count'])

@receiver(post_delete, sender=MediaInteraction)
def update_media_counts_on_interaction_delete(sender, instance, **kwargs):
    """Update media counts when interactions are deleted"""
    # Get the media object
    if instance.content_type == 'film':
        from .models import Film
        media_obj = Film.objects.filter(id=instance.object_id).first()
    else:
        from .models import Content
        media_obj = Content.objects.filter(id=instance.object_id).first()
    
    if media_obj:
        if instance.interaction_type == 'like':
            # Update like count
            like_count = MediaInteraction.objects.filter(
                content_type=instance.content_type,
                object_id=instance.object_id,
                interaction_type='like'
            ).count()
            media_obj.like_count = like_count
            media_obj.save(update_fields=['like_count'])
        
        elif instance.interaction_type == 'rate':
            # Recalculate average rating
            ratings = MediaInteraction.objects.filter(
                content_type=instance.content_type,
                object_id=instance.object_id,
                interaction_type='rate',
                rating__isnull=False
            )
            
            if ratings.exists():
                avg_rating = sum(r.rating for r in ratings) / ratings.count()
                media_obj.average_rating = round(avg_rating, 1)
                media_obj.rating_count = ratings.count()
            else:
                media_obj.average_rating = 0.0
                media_obj.rating_count = 0
            
            media_obj.save(update_fields=['average_rating', 'rating_count'])