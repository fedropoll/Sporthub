from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    RegisterView, VerifyCodeView, LoginView, UserProfileViewSet,
     PasswordResetView, ClientViewSet,
    HallViewSet, ClubViewSet, TrainerViewSet, AdViewSet,
    ReviewViewSet, NotificationViewSet,
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
    UserProfileView,
)

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'halls', HallViewSet, basename='halls')
router.register(r'clubs', ClubViewSet, basename='clubs')
router.register(r'trainers', TrainerViewSet, basename='trainers')
router.register(r'ads', AdViewSet, basename='ads')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'register', RegisterView, basename='register')
router.register(r'verify', VerifyCodeView, basename='verify')
router.register(r'reset-password', PasswordResetView, basename='reset-password')
# from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-code/', VerifyCodeView.as_view(), name='verify_code'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('auth/resend-code/', ResendCodeView.as_view(), name='resend_code'),
    # path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schedules/', ClassScheduleView.as_view(), name='class_schedule'),
    path('joinclubs/', JoinclubView.as_view(), name='joinclub'),
    path('payments/<int:joinclub_id>/', PaymentView.as_view(), name='payment'),
    path('attendance/<int:joinclub_id>/', AttendanceView.as_view(), name='attendance_view'),
    path('profile/', UserProfileView.as_view(), name='profile_view'),
]
