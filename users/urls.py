from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, VerifyCodeView, LoginView, UserProfileViewSet,
    PasswordChangeView, PasswordResetView, ClientViewSet,
    HallViewSet, ClubViewSet, TrainerViewSet, AdViewSet,
    ReviewViewSet, NotificationViewSet,
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
router.register(r'change-password', PasswordChangeView, basename='change-password')
router.register(r'reset-password', PasswordResetView, basename='reset-password')

urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('', include(router.urls)),
]