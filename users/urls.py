from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, VerifyCodeView, LoginView,
    UserProfileViewSet, ClientViewSet,
    HallViewSet, ClubViewSet, TrainerViewSet, AdViewSet,
    ReviewViewSet, NotificationViewSet,
    ForgotPasswordView, ResetPasswordView, ResendCodeView,
    ClassScheduleView, JoinclubView, PaymentView, AttendanceView,
)

router = DefaultRouter()

# Основные ViewSet'ы
router.register(r'clubs', ClubViewSet)
router.register(r'halls', HallViewSet)
router.register(r'trainers', TrainerViewSet)
router.register(r'ads', AdViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'clients', ClientViewSet, basename='clients')

urlpatterns = [
    # Аутентификация
    path('auth/', include([
        path('register/', RegisterView.as_view(), name='register'),
        path('verify-code/', VerifyCodeView.as_view(), name='verify_code'),
        path('login/', LoginView.as_view(), name='login'),
        path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
        path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
        path('resend-code/', ResendCodeView.as_view(), name='resend_code'),
    ])),

    # Тренировки и расписание
    path('schedules/', include([
        path('', ClassScheduleView.as_view(), name='class_schedule'),
        path('join/', JoinclubView.as_view(), name='joinclub'),
        path('payments/<int:joinclub_id>/', PaymentView.as_view(), name='payment'),
        path('attendance/<int:joinclub_id>/', AttendanceView.as_view(), name='attendance_view'),
    ])),

    # Основное API
    path('', include(router.urls)),
]
