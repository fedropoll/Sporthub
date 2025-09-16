from django.db.models import Avg, Count
from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from users.models import Hall, Club, Review
from users.permissions import IsOwnerOrAdmin
from .serializers import (
    HallSerializer, ClubSerializer, ReviewSerializer,
    HallDetailSerializer, ClubDetailSerializer, AdminReviewSerializer
)


from drf_yasg.utils import swagger_auto_schema

class HallViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hall.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type', 'coating', 'has_locker_room', 'has_shower', 'has_lighting']
    search_fields = ['title', 'address', 'inventory']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return HallDetailSerializer
        return HallSerializer

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Список залов',
        operation_description='Возвращает список всех залов с мини-описаниями, характеристиками и средней оценкой.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Детали зала',
        operation_description='Возвращает подробную информацию о выбранном зале, включая все отзывы.'
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Отзывы зала',
        operation_description='Возвращает список всех отзывов данного зала.'
    )
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        hall = self.get_object()
        serializer = ReviewSerializer(hall.reviews.all(), many=True)
        return Response(serializer.data)


class ClubViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Club.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['hall']
    search_fields = ['title', 'description', 'sport']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClubDetailSerializer
        return ClubSerializer

    @swagger_auto_schema(
        tags=['🏀 Клубы'],
        operation_summary='Список клубов',
        operation_description='Возвращает список всех клубов с мини-описаниями и залами, к которым они относятся.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏀 Клубы'],
        operation_summary='Детали клуба',
        operation_description='Возвращает полную информацию о выбранном клубе, включая все отзывы.'
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏀 Клубы'],
        operation_summary='Отзывы клуба',
        operation_description='Возвращает список всех отзывов данного клуба.'
    )
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        club = self.get_object()
        serializer = ReviewSerializer(club.reviews.all(), many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrAdmin()]

    def get_serializer_class(self):
        user = self.request.user
        if user.is_staff:
            return AdminReviewSerializer
        return ReviewSerializer

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Список отзывов',
        operation_description='Возвращает список всех отзывов. Для админов видны все поля.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Детали отзыва',
        operation_description='Возвращает полную информацию о выбранном отзыве. Для админов видны все поля.'
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Создать отзыв',
        operation_description='Создает новый отзыв. Для админов доступны все поля.'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Обновить отзыв',
        operation_description='Полное обновление отзыва. Доступно только админам.'
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Частично обновить отзыв',
        operation_description='Частичное обновление отзыва. Доступно только админам.'
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Удалить отзыв',
        operation_description='Удаляет отзыв. Доступно только администраторам.'
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
