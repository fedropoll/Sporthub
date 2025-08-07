from django.db import models
from django.contrib.auth import get_user_model
from halls.models import Hall

User = get_user_model()

class Trainer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    hall = models.ForeignKey(
        Hall,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Зал"
    )
    bio = models.TextField(blank=True, verbose_name="Биография")
    sport = models.CharField(max_length=100, blank=True, verbose_name="Специализация")
    photo = models.ImageField(upload_to='trainer_photos/', blank=True, null=True, verbose_name="Фото")

    def __str__(self):
        return self.user.get_full_name() or self.user.email