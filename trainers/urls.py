from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrainerViewSet

router = DefaultRouter()
router.register('', TrainerViewSet, basename='trainer')

urlpatterns = [
    path('', include(router.urls)),
]