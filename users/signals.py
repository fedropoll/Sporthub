from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """
        Создаёт UserProfile для нового пользователя или сохраняет существующий профиль.
    """
    if created:
        # Создаём профиль для нового пользователя
        UserProfile.objects.create(user=instance)
    else:
        # Проверяем, существует ли профиль
        try:
            user_profile = UserProfile.objects.get(user=instance)
            user_profile.save()  # Сохраняем существующий профиль
        except UserProfile.DoesNotExist:
            # Если профиль не существует, создаём его
            UserProfile.objects.create(user=instance)