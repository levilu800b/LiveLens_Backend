# type: ignore

# podcasts/signals.py
"""
Signals for the podcasts app
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Podcast, PodcastInteraction, PodcastSeries

@receiver(post_save, sender=Podcast)
def podcast_post_save(sender, instance, created, **kwargs):
    """Handle podcast post-save operations"""
    if created:
        # Log podcast creation
        pass
    
    # Update published_at when status changes to published
    if instance.status == 'published' and not instance.published_at:
        instance.published_at = timezone.now()
        instance.save(update_fields=['published_at'])

@receiver(post_save, sender=PodcastInteraction)
def update_podcast_counts_on_interaction(sender, instance, created, **kwargs):
    """Update podcast counts when interactions are created"""
    if created:
        # Update podcast episode counts
        if instance.podcast:
            podcast = instance.podcast
            
            if instance.interaction_type == 'like':
                # Update like count
                like_count = PodcastInteraction.objects.filter(
                    podcast=podcast,
                    interaction_type='like'
                ).count()
                podcast.like_count = like_count
                podcast.save(update_fields=['like_count'])
            
            elif instance.interaction_type == 'rate' and instance.rating:
                # Update average rating
                ratings = PodcastInteraction.objects.filter(
                    podcast=podcast,
                    interaction_type='rate',
                    rating__isnull=False
                )
                
                if ratings.exists():
                    avg_rating = sum(r.rating for r in ratings) / ratings.count()
                    podcast.average_rating = round(avg_rating, 1)
                    podcast.rating_count = ratings.count()
                    podcast.save(update_fields=['average_rating', 'rating_count'])

@receiver(post_delete, sender=PodcastInteraction)
def update_podcast_counts_on_interaction_delete(sender, instance, **kwargs):
    """Update podcast counts when interactions are deleted"""
    # Update podcast episode counts
    if instance.podcast:
        podcast = instance.podcast
        
        if instance.interaction_type == 'like':
            # Update like count
            like_count = PodcastInteraction.objects.filter(
                podcast=podcast,
                interaction_type='like'
            ).count()
            podcast.like_count = like_count
            podcast.save(update_fields=['like_count'])
        
        elif instance.interaction_type == 'rate':
            # Recalculate average rating
            ratings = PodcastInteraction.objects.filter(
                podcast=podcast,
                interaction_type='rate',
                rating__isnull=False
            )
            
            if ratings.exists():
                avg_rating = sum(r.rating for r in ratings) / ratings.count()
                podcast.average_rating = round(avg_rating, 1)
                podcast.rating_count = ratings.count()
            else:
                podcast.average_rating = 0.0
                podcast.rating_count = 0
            
            podcast.save(update_fields=['average_rating', 'rating_count'])