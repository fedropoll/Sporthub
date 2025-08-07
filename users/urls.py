from django.urls import path
from .views import (
    RegisterView,
    VerifyCodeView,
    LoginView,
    ForgotPasswordView,
    ResetPasswordView,
    ResendCodeView,
    ClassScheduleView,
    JoinclubView,
    PaymentView,
    AttendanceView,
    UserProfileEditView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify_code'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('resend-code/', ResendCodeView.as_view(), name='resend_code'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schedules/', ClassScheduleView.as_view(), name='class_schedule'),
    path('joinclubs/', JoinclubView.as_view(), name='joinclub'),
    path('payments/<int:joinclub_id>/', PaymentView.as_view(), name='payment'),
    path('attendance/<int:joinclub_id>/', AttendanceView.as_view(), name='attendance_view'),
    path('profile/edit/', UserProfileEditView.as_view(), name='profile_edit'),
]
