from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile, UserProfileExtension

@receiver(post_save, sender=UserProfile)
def create_profile_extension(sender, instance, created, **kwargs):
    if created:
        UserProfileExtension.objects.create(user_profile=instance)
