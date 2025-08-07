from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HallViewSet, ClubViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r'halls', HallViewSet, basename='hall')
router.register(r'clubs', ClubViewSet, basename='club')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]