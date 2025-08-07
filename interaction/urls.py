from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, PaymentViewSet, NotificationViewSet

router = DefaultRouter()
router.register('reviews', ReviewViewSet, basename='review')
router.register('payments', PaymentViewSet, basename='payment')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]