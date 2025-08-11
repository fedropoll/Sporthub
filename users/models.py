from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.contrib.postgres.fields import ArrayField


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.IntegerField(max_length=20, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(max_length=10,  choices=(('Мужской', 'Male'), ('Женский', 'Female')), null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
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

class ClassSchedule(models.Model):

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
    day_of_week = models.CharField(max_length=10, choices=(
        ('Monday', 'Понедельник'),
        ('Tuesday', 'Вторник'),
        ('Wednesday', 'Среда'),
        ('Thursday', 'Четверг'),
        ('Friday', 'Пятница'),
        ('Saturday', 'Суббота'),
        ('Sunday', 'Воскресенье'),
    ))
    start_time = models.TimeField()
    end_time = models.TimeField()
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
        return f"{self.title} - {self.day_of_week} ({self.start_time} - {self.end_time})"
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

class Joinclub(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    age_group = models.CharField(max_length=10, choices=(
        ('Adult', 'Взрослые'),
        ('Teen', 'Подростков'),
        ('Child', 'Детей'),
    ), default='Adult')  # Выбор возраста при записи
    size = models.CharField(max_length=50, blank=True, null=True)
    count = models.PositiveIntegerField(blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    coating = models.CharField(max_length=50, blank=True, null=True)
    inventory = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'schedule')  # Предотвращает дублирование записей
    has_locker_room = models.BooleanField(default=False)
    has_lighting = models.BooleanField(default=False)
    has_shower = models.BooleanField(default=False)

    images = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.schedule.title} ({self.age_group})"
        return self.title

class Payment(models.Model):
    joinclub = models.OneToOneField(Joinclub, on_delete=models.CASCADE)
    stripe_payment_intent_id = models.CharField(max_length=50, null=True, blank=True)  # Идентификатор от Stripe
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
class Trainer(models.Model):
    first_name = models.CharField(max_length=100, blank=False, null=False)
    last_name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    sport = models.CharField(max_length=50, blank=False, null=False)
    photo = models.ImageField(upload_to='trainers/', blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.joinclub.user} - {self.amount} сом"
        return f"{self.first_name} {self.last_name}"

class Attendance(models.Model):
    joinclub = models.ForeignKey(Joinclub, on_delete=models.CASCADE)
    attendance_date = models.DateField(default=timezone.now)
    is_present = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Attendances"
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, null=True, blank=True)
    club = models.ForeignKey('Club', on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.joinclub.user} - {self.joinclub.schedule.title} on {self.attendance_date}"
        return f"Отзыв от {self.user.username}"


    @property
    def get_attendance_summary(self):
        # Подсчет посещенных и пропущенных дней для пользователя за последний месяц
        from django.utils import timezone
        one_month_ago = timezone.now() - timedelta(days=30)
        attendances = Attendance.objects.filter(joinclub=self.joinclub, attendance_date__gte=one_month_ago)
        present_count = attendances.filter(is_present=True).count()
        absent_count = attendances.filter(is_present=False).count()
        return {
            'present': present_count,
            'absent': absent_count,
            'total': present_count + absent_count
        }
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