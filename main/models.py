from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Hall(models.Model):
    HALL_TYPES = [
        ('indoor', 'Крытый'),
        ('outdoor', 'Открытый'),
        ('mixed', 'Смешанный')
    ]

    name = models.CharField('Название', max_length=100)
    address = models.TextField('Адрес')
    phone = models.CharField('Телефон', max_length=20)
    working_hours = models.JSONField('Часы работы', default=dict, blank=True)
    images = models.JSONField('Изображения', default=list, blank=True)
    video_url = models.URLField('URL видео', blank=True, null=True)
    advantages = models.JSONField('Преимущества', default=list, blank=True)

    size = models.CharField('Размер', max_length=50, blank=True)
    hall_type = models.CharField('Тип зала', max_length=50, choices=HALL_TYPES, blank=True)
    coating = models.CharField('Покрытие', max_length=50, blank=True)
    inventory = models.CharField('Инвентарь', max_length=100, blank=True)
    price_per_hour = models.DecimalField(
        'Цена за час',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    dressing_room = models.BooleanField('Раздевалка', default=False)
    lighting = models.BooleanField('Освещение', default=False)
    shower = models.BooleanField('Душ', default=False)
    capacity = models.PositiveIntegerField('Вместимость', null=True, blank=True)

    latitude = models.FloatField('Широта', null=True, blank=True)
    longitude = models.FloatField('Долгота', null=True, blank=True)

    class Meta:
        verbose_name = 'Зал'
        verbose_name_plural = 'Залы'

    def __str__(self):
        return self.name

class Club(models.Model):
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    coach = models.CharField('Тренер', max_length=100)
    contact_phone = models.CharField('Контактный телефон', max_length=20)
    training_schedule = models.JSONField('Расписание тренировок', default=dict)
    age_groups = models.JSONField('Возрастные группы', default=list)
    price_per_month = models.DecimalField(
        'Цена за месяц',
        max_digits=10,
        decimal_places=2
    )
    hall = models.ForeignKey(
        Hall,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clubs'
    )
    logo = models.ImageField('Логотип', upload_to='club_logos/', null=True, blank=True)
    video_url = models.URLField('URL видео', blank=True, null=True)

    class Meta:
        verbose_name = 'Клуб'
        verbose_name_plural = 'Клубы'

    def __str__(self):
        return self.name

class Review(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='main_reviews'
    )
    hall = models.ForeignKey(
        Hall,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True
    )
    rating = models.PositiveSmallIntegerField(
        'Рейтинг',
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField('Текст отзыва')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.CheckConstraint(
                check=models.Q(hall__isnull=False) | models.Q(club__isnull=False),
                name='not_both_null'
            )
        ]

    def __str__(self):
        return f"Отзыв от {self.author} ({self.rating}/5)"