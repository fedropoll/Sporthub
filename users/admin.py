from django.contrib import admin
from .models import UserProfile, PasswordResetCode, ClassSchedule, Joinclub, Attendance

admin.site.register(UserProfile)
admin.site.register(PasswordResetCode)
admin.site.register(ClassSchedule)
admin.site.register(Joinclub)
admin.site.register(Attendance)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number')
    list_editable = ('role',)
