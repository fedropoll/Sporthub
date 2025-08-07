from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterOrLoginView,
    VerifyCodeView,
    ForgotPasswordView,
    ResetPasswordView,
    ResendCodeView,
    AdViewSet,
)
from rest_framework_simplejwt.views import TokenObtainPairView

router = DefaultRouter()
router.register(r'ads', AdViewSet, basename='ads')

urlpatterns = [
    path('auth/register/', RegisterOrLoginView.as_view(), name='auth/register'),
    path('auth/verify-code/', VerifyCodeView.as_view(), name='auth/verify-code'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='auth/forgot-password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='auth/reset-password'),
    path('auth/resend-code/', ResendCodeView.as_view(), name='auth/resend-code'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('', include(router.urls)),
]
