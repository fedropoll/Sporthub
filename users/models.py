from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    birth_date = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=50)
    gender = models.CharField(max_length=10,  choices=(('Мужской', 'Male'), ('Женский', 'Female')), null=True, blank=True)
    email = models.EmailField(unique=True)

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

    def __str__(self):
        return f"{self.title} - {self.day_of_week} ({self.start_time} - {self.end_time})"

class Joinclub(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    age_group = models.CharField(max_length=10, choices=(
        ('Adult', 'Взрослые'),
        ('Teen', 'Подростков'),
        ('Child', 'Детей'),
    ), default='Adult')  # Выбор возраста при записи

    class Meta:
        unique_together = ('user', 'schedule')  # Предотвращает дублирование записей

    def __str__(self):
        return f"{self.user} - {self.schedule.title} ({self.age_group})"

class Payment(models.Model):
    joinclub = models.OneToOneField(Joinclub, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.joinclub.user} - {self.amount} сом"

class Attendance(models.Model):
    joinclub = models.ForeignKey(Joinclub, on_delete=models.CASCADE)
    attendance_date = models.DateField(default=timezone.now)
    is_present = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Attendances"

    def __str__(self):
        return f"{self.joinclub.user} - {self.joinclub.schedule.title} on {self.attendance_date}"

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