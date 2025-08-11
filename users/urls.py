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

# Создание роутера для ViewSet'ов
router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'halls', HallViewSet, basename='halls')
router.register(r'clubs', ClubViewSet, basename='clubs')
router.register(r'trainers', TrainerViewSet, basename='trainers')
router.register(r'ads', AdViewSet, basename='ads')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    # Маршруты для DRF ViewSet'ов
    path('', include(router.urls)),

    # Маршруты для обычных APIView
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-code/', VerifyCodeView.as_view(), name='verify_code'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('auth/resend-code/', ResendCodeView.as_view(), name='resend_code'),

    # Маршруты для других APIView
    path('schedules/', ClassScheduleView.as_view(), name='class_schedule'),
    path('joinclubs/', JoinclubView.as_view(), name='joinclub'),
    path('payments/<int:joinclub_id>/', PaymentView.as_view(), name='payment'),
    path('attendance/<int:joinclub_id>/', AttendanceView.as_view(), name='attendance_view'),
]