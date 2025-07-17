from django.urls import path
from .views import RegisterAPIView, RequestPasswordResetAPIView, ConfirmPasswordResetAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('request-reset/', RequestPasswordResetAPIView.as_view(), name='request-reset'),
    path('confirm-reset/', ConfirmPasswordResetAPIView.as_view(), name='confirm-reset'),
]
