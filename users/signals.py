# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """
    Создаёт UserProfile для нового пользователя и сохраняет существующий профиль.
    """
    if created:
        # Создаем профиль только для нового пользователя
        UserProfile.objects.create(user=instance)
    else:
        # Сохраняем существующий профиль
        try:
            instance.userprofile.save()
        except UserProfile.DoesNotExist:
            # Если профиль отсутствует, создаём его
            UserProfile.objects.create(user=instance)
