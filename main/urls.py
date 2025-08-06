from django.urls import path
from .views import (
    RegisterView,
    VerifyCodeView,
    LoginView,
    ForgotPasswordView,
    ResetPasswordView,
    ResendCodeView
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
]
