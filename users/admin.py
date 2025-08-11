from django.contrib import admin
from .models import UserProfile, PasswordResetCode, ClassSchedule, Joinclub, Payment, Attendance

admin.site.register(UserProfile)
admin.site.register(PasswordResetCode)
admin.site.register(ClassSchedule)
admin.site.register(Joinclub)
admin.site.register(Payment)
admin.site.register(Attendance)