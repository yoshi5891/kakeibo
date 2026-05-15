from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Family

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        family = Family.objects.create(name=f"{instance.username}家")
        Profile.objects.create(user=instance, family=family)
