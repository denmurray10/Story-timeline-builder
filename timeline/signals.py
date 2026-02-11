from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Book, Chapter, Character, Event, Tag, CharacterRelationship, ActivityLog

@receiver(post_save, sender=Book)
@receiver(post_save, sender=Chapter)
@receiver(post_save, sender=Character)
@receiver(post_save, sender=Event)
@receiver(post_save, sender=Tag)
@receiver(post_save, sender=CharacterRelationship)
def log_save_activity(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'
    model_name = sender.__name__
    
    # Try to get a user
    user = None
    if hasattr(instance, 'user'):
        user = instance.user
    elif hasattr(instance, 'book') and hasattr(instance.book, 'user'):
        user = instance.book.user
    elif hasattr(instance, 'character_a') and hasattr(instance.character_a, 'user'):
        user = instance.character_a.user
    
    if user:
        # Determine a nice object name
        object_name = str(instance)
        if hasattr(instance, 'title'):
            object_name = instance.title
        elif hasattr(instance, 'name'):
            object_name = instance.name
            
        # Create log
        ActivityLog.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_name=object_name
        )

@receiver(post_delete, sender=Book)
@receiver(post_delete, sender=Chapter)
@receiver(post_delete, sender=Character)
@receiver(post_delete, sender=Event)
@receiver(post_delete, sender=Tag)
def log_delete_activity(sender, instance, **kwargs):
    model_name = sender.__name__
    
    # Try to get a user
    user = None
    if hasattr(instance, 'user'):
        user = instance.user
    elif hasattr(instance, 'book') and hasattr(instance.book, 'user'):
        user = instance.book.user
    
    if user:
        object_name = str(instance)
        if hasattr(instance, 'title'):
            object_name = instance.title
        elif hasattr(instance, 'name'):
            object_name = instance.name
            
        ActivityLog.objects.create(
            user=user,
            action='delete',
            model_name=model_name,
            object_name=object_name
        )
