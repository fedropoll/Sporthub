from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Review, Notification, UserProfile

# Сигнал для создания уведомления при добавлении нового отзыва
@receiver(post_save, sender=Review)
def create_review_notification(sender, instance, created, **kwargs):
    """
    Создает уведомление, когда пользователь оставляет новый отзыв.
    """
    if created:
        message = f"Новый отзыв от {instance.user.username}."
        Notification.objects.create(
            user=instance.user,
            message=message,
            type='review'
        )

# Сигнал для создания профиля пользователя и уведомления о регистрации
@receiver(post_save, sender=User)
def create_user_profile_and_notification(sender, instance, created, **kwargs):
    """
    Автоматически создает профиль UserProfile и уведомление о регистрации
    для каждого нового пользователя.
    """
    if created:
        # Создаем профиль пользователя UserProfile
        UserProfile.objects.get_or_create(user=instance)

        # Создаем уведомление о регистрации
        message = f"Новый пользователь {instance.username} зарегистрировался."
        Notification.objects.create(
            user=instance,
            message=message,
            type='registration'
        )