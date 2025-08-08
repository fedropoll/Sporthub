from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.contrib.postgres.fields import ArrayField


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    trainer = models.ForeignKey('Trainer', on_delete=models.SET_NULL, null=True, blank=True)
    sport = models.CharField(max_length=50, blank=True, null=True)
    has_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)


class Ad(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    image = models.URLField()

    working_days = models.JSONField(default=dict)

    installment_plan = ArrayField(
        base_field=models.IntegerField(),
        default=list,
        help_text="Список месяцев: [6, 9, 12]"
    )

    site_name = models.CharField(max_length=100)
    site_url = models.URLField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Hall(models.Model):
    title = models.CharField(max_length=100)
    sport = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=200)
    price_per_hour = models.PositiveIntegerField()

    schedule = models.JSONField(blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    count = models.PositiveIntegerField(blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    coating = models.CharField(max_length=50, blank=True, null=True)
    inventory = models.TextField(blank=True, null=True)

    has_locker_room = models.BooleanField(default=False)
    has_lighting = models.BooleanField(default=False)
    has_shower = models.BooleanField(default=False)

    images = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.title


class Club(models.Model):
    title = models.CharField(max_length=100)
    sport = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=200)
    price_per_hour = models.PositiveIntegerField()

    schedule_adults = models.JSONField(blank=True, null=True)
    schedule_teens = models.JSONField(blank=True, null=True)
    schedule_kids = models.JSONField(blank=True, null=True)

    size = models.CharField(max_length=50, blank=True, null=True)
    count = models.PositiveIntegerField(blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    coating = models.CharField(max_length=50, blank=True, null=True)
    inventory = models.TextField(blank=True, null=True)

    has_locker_room = models.BooleanField(default=False)
    has_lighting = models.BooleanField(default=False)
    has_shower = models.BooleanField(default=False)

    images = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.title

class Trainer(models.Model):
    first_name = models.CharField(max_length=100, blank=False, null=False)
    last_name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    sport = models.CharField(max_length=50, blank=False, null=False)
    photo = models.ImageField(upload_to='trainers/', blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True)
    club = models.ForeignKey('Club', on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.user.username}"


class Notification(models.Model):
    MESSAGE_TYPES = (
        ('review', 'Отзыв'),
        ('payment', 'Оплата'),
        ('registration', 'Регистрация'),
        ('login', 'Вход в аккаунт'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_type_display()}] - {self.message}"