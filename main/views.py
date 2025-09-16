from django.db.models import Avg, Count
from rest_framework import viewsets, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from django_filters.rest_framework import DjangoFilterBackend

from .models import Hall, Club, Review
from .serializers import (
    HallSerializer, ClubSerializer, ReviewSerializer,
    HallDetailSerializer, ClubDetailSerializer
)
from .permissions import IsAuthorOrReadOnly  # Предполагается, что у вас есть такой класс


class HallViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для публичного доступа к залам.

    Методы: `list`, `retrieve`, `reviews`.
    Доступен для всех пользователей, включая незарегистрированных.
    """
    queryset = Hall.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['hall_type', 'coating', 'dressing_room', 'shower', 'lighting']
    search_fields = ['name', 'address', 'inventory']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return HallDetailSerializer
        return HallSerializer

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Получить список залов',
        operation_description='Возвращает список всех залов с возможностью фильтрации и поиска.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Получить детали зала',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Залы'],
        operation_summary='Получить отзывы зала',
    )
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        hall = self.get_object()
        reviews = hall.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ClubViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для публичного доступа к клубам.

    Методы: `list`, `retrieve`, `reviews`.
    Доступен для всех пользователей, включая незарегистрированных.
    """
    queryset = Club.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    serializer_class = ClubSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['hall']
    search_fields = ['name', 'description', 'coach']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClubDetailSerializer
        return ClubSerializer

    @swagger_auto_schema(
        tags=['🏀 Клубы'],
        operation_summary='Получить список клубов',
        operation_description='Возвращает список всех баскетбольных клубов.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏀 Клубы'],
        operation_summary='Получить детали клуба',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏀 Клубы'],
        operation_summary='Получить отзывы клуба',
    )
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        club = self.get_object()
        reviews = club.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API для управления отзывами.

    - Просмотр (`list`, `retrieve`): Доступно всем.
    - Создание (`create`): Только для аутентифицированных пользователей.
    - Редактирование/удаление (`update`, `destroy`): Только для автора отзыва или администратора.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        # Разрешения зависят от действия
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAuthorOrReadOnly()]

    def perform_create(self, serializer):
        # Автоматически связывает отзыв с аутентифицированным пользователем
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        # Добавляем фильтрацию, как в вашем предыдущем коде
        hall_id = self.request.query_params.get('hall_id')
        club_id = self.request.query_params.get('club_id')

        if hall_id:
            queryset = queryset.filter(hall_id=hall_id)
        if club_id:
            queryset = queryset.filter(club_id=club_id)
        return queryset

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Получить список отзывов',
        operation_description='Возвращает список всех отзывов. Доступно всем.',
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Оставить новый отзыв',
        operation_description='Создает новый отзыв. **Требуется авторизация.**',
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Получить детали отзыва',
        operation_description='Возвращает детальную информацию об отзыве. Доступно всем.',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Обновить отзыв (только для автора)',
        operation_description='Полное обновление отзыва. **Доступно только автору или администратору.**',
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Частично обновить отзыв (только для автора)',
        operation_description='Частичное обновление отзыва. **Доступно только автору или администратору.**',
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Удалить отзыв (только для автора)',
        operation_description='Удаляет отзыв. **Доступно только автору или администратору.**',
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)