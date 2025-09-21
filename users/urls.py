from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView, VerifyCodeView, LoginView,
    UserProfileViewSet, ClientViewSet,
    HallViewSet, ClubViewSet, TrainerViewSet, AdViewSet,
    ReviewViewSet, NotificationViewSet,
    ForgotPasswordView, ResetPasswordView, ResendCodeView,
    ClassScheduleView, JoinclubView, AttendanceView, GetRoleTokenView,
    AdminChangeUserRoleView, MyTokenObtainPairView
)

router = DefaultRouter()
router.register(r'clubs', ClubViewSet)
router.register(r'halls', HallViewSet)
router.register(r'trainers', TrainerViewSet)
router.register(r'ads', AdViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'notifications', NotificationViewSet, basename='notification')


urlpatterns = [
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('auth/', include([
        path('register/', RegisterView.as_view(), name='register'),
        path('verify-code/', VerifyCodeView.as_view(), name='verify_code'),
        path('login/', LoginView.as_view(), name='login'),
        path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
        path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
        path('resend-code/', ResendCodeView.as_view(), name='resend_code'),
    ])),
    path('schedules/', include([
        path('', ClassScheduleView.as_view(), name='class_schedule'),
        path('join/', JoinclubView.as_view(), name='joinclub'),
        path('attendance/', AttendanceView.as_view(), name='attendance_view'),
    ])),
    path('', include(router.urls)),
    path('profile/', UserProfileViewSet.as_view({'get': 'retrieve', 'put': 'update'}), name='profile'),
]
