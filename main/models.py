from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.db.models.signals import post_save
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    birth_date = models.DateField()

class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

# class CustomUserManager(BaseUserManager):
#     def create_user(self, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError('The Email field must be set')
#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, email, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('is_active', True)
#
#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')
#         return self.create_user(email, password, **extra_fields)
#
#
# class CustomUser(AbstractUser):
#     username = models.CharField(max_length=150, unique=True, null=True, blank=True)
#     email = models.EmailField(unique=True, null=False, blank=False)
#
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = []
#
#     objects = CustomUserManager()
#
#     def __str__(self):
#         return self.email
#
#
# class UserProfile(models.Model):
#     ROLES = (
#         ('patient', 'Пациент'),
#         ('doctor', 'Врач'),
#         ('admin', 'Администратор'),
#         ('director', 'Директор'),
#         ('staff', 'Персонал'),
#     )
#     user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_profile')
#     role = models.CharField(max_length=10, choices=ROLES, default='patient')  # default добавлен
#
#     def __str__(self):
#         return f"{self.user.email} - {self.get_role_display()}"
# class ClientProfile(models.Model):
#     user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='client_profile')
#     full_name = models.CharField(max_length=255, blank=True, null=True)
#     phone = models.CharField(max_length=20, blank=True, null=True)
#     birth_date = models.DateField(blank=True, null=True)
#     GENDER_CHOICES = [
#         ('M', 'Мужской'),
#         ('F', 'Женский'),
#         ('O', 'Другой'),
#     ]
#     gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
#     address = models.CharField(max_length=255, blank=True, null=True)
#     about = models.TextField(blank=True, null=True)
#     is_email_verified = models.BooleanField(default=False)
#     confirmation_code = models.CharField(max_length=6, blank=True, null=True)
#     code_created_at = models.DateTimeField(blank=True, null=True)
#
#     def __str__(self):
#         return self.full_name or self.user.email

# @receiver(post_save, sender=CustomUser)
# def create_or_update_user_profiles(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)
#         ClientProfile.objects.create(user=instance)
#         if instance.user_profile.role in ['doctor', 'director']:
#             Doctor.objects.create(user_profile=instance.user_profile)
#     else:
#         if hasattr(instance, 'user_profile'):
#             instance.user_profile.save()
#             if instance.user_profile.role in ['doctor', 'director'] and not hasattr(instance.user_profile, 'doctor_profile'):
#                 Doctor.objects.create(user_profile=instance.user_profile)
#             elif instance.user_profile.role not in ['doctor', 'director'] and hasattr(instance.user_profile, 'doctor_profile'):
#                 instance.user_profile.doctor_profile.delete()
#         if hasattr(instance, 'client_profile'):
#             instance.client_profile.save()
#
#
# class IsDoctor(IsInRole):
#     allowed_roles = ['doctor']
#
#
# class IsDoctorOrDirector(IsInRole):
#     allowed_roles = ['doctor', 'director']
