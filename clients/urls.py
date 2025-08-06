from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, PaymentViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
