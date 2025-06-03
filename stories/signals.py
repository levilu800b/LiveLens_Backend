# type: ignore

# stories/signals.py
"""
Signals for the stories app
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Story, StoryInteraction

@receiver(post_save, sender=Story)
def story_post_save(sender, instance, created, **kwargs):
    """Handle story post-save operations"""
    if created:
        # Log story creation
        pass
    
    # Update published_at when status changes to published
    if instance.status == 'published' and not instance.published_at:
        instance.published_at = timezone.now()
        instance.save(update_fields=['published_at'])

@receiver(post_save, sender=StoryInteraction)
def update_story_counts_on_interaction(sender, instance, created, **kwargs):
    """Update story counts when interactions are created"""
    if created and instance.interaction_type == 'like':
        # Update like count
        story = instance.story
        story.like_count = StoryInteraction.objects.filter(
            story=story,
            interaction_type='like'
        ).count()
        story.save(update_fields=['like_count'])

@receiver(post_delete, sender=StoryInteraction)
def update_story_counts_on_interaction_delete(sender, instance, **kwargs):
    """Update story counts when interactions are deleted"""
    if instance.interaction_type == 'like':
        # Update like count
        story = instance.story
        story.like_count = StoryInteraction.objects.filter(
            story=story,
            interaction_type='like'
        ).count()
        story.save(update_fields=['like_count'])