from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HallViewSet

router = DefaultRouter()
router.register('', HallViewSet, basename='hall')

urlpatterns = [
    path('', include(router.urls)),
]