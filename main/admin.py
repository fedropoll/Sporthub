from django.contrib import admin
from .models import UserProfile, PasswordResetCode

admin.site.register(UserProfile)
admin.site.register(PasswordResetCode)