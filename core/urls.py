from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HallViewSet, TrainerViewSet, ClubViewSet

router = DefaultRouter()
router.register(r'halls', HallViewSet, basename='hall')
router.register(r'trainers', TrainerViewSet, basename='trainer')
router.register(r'clubs', ClubViewSet, basename='club')

urlpatterns = [
    path('', include(router.urls)),
]
