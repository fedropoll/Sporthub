from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Review, Notification

@receiver(post_save, sender=Review)
def create_review_notification(sender, instance, created, **kwargs):
    if created:
        message = f"Новый отзыв от {instance.user.username}."
        Notification.objects.create(
            user=instance.user,
            message=message,
            type='review'
        )

@receiver(post_save, sender=User)
def create_registration_notification(sender, instance, created, **kwargs):
    if created:
        message = f"Новый пользователь {instance.username} зарегистрировался."
        Notification.objects.create(
            user=instance,
            message=message,
            type='registration'
        )