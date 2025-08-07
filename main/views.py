from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Hall, Club, Review
from .serializers import (
    HallSerializer, ClubSerializer, ReviewSerializer,
    HallDetailSerializer, ClubDetailSerializer
)
from .permissions import IsAuthorOrReadOnly


class HallViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для управления баскетбольными залами.
    """
    queryset = Hall.objects.all()
    permission_classes = [AllowAny]  # Разрешение для всех (публичный доступ)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return HallDetailSerializer
        return HallSerializer

    @swagger_auto_schema(
        tags=['🏟️ Баскетбольные залы'],
        operation_summary='Получить список залов',
        operation_description='Возвращает краткий список всех баскетбольных залов. Содержит основную информацию о каждом зале, такую как название, адрес и рейтинг. Идеально подходит для отображения на главной странице.',
        responses={200: HallSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Баскетбольные залы'],
        operation_summary='Получить детали зала',
        operation_description='Возвращает полную информацию о конкретном баскетбольном зале по его ID. Включает в себя подробные данные, такие как часы работы, инвентарь, цены и список всех отзывов.',
        responses={200: HallDetailSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏟️ Баскетбольные залы'],
        operation_summary='Получить отзывы зала',
        operation_description='Возвращает список всех отзывов, оставленных для конкретного зала. Полезно для отображения секции с отзывами на странице деталей зала.',
        responses={200: ReviewSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        hall = self.get_object()
        reviews = hall.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ClubViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для управления баскетбольными клубами.
    """
    queryset = Club.objects.all()
    permission_classes = []  # Разрешение для всех (публичный доступ)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClubDetailSerializer
        return ClubSerializer

    @swagger_auto_schema(
        tags=['🏀 Баскетбольные клубы'],
        operation_summary='Получить список клубов',
        operation_description='Возвращает краткий список всех баскетбольных клубов. Показывает основную информацию: название, описание, тренера и рейтинг. Подходит для общего списка клубов.',
        responses={200: ClubSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏀 Баскетбольные клубы'],
        operation_summary='Получить детали клуба',
        operation_description='Возвращает полную информацию о конкретном клубе по его ID. Включает расписание, возрастные группы, цену и все отзывы, связанные с клубом.',
        responses={200: ClubDetailSerializer()}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏀 Баскетбольные клубы'],
        operation_summary='Получить отзывы клуба',
        operation_description='Возвращает список всех отзывов, оставленных для конкретного клуба. Идеально для секции отзывов на странице клуба.',
        responses={200: ReviewSerializer(many=True)}
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
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        queryset = Review.objects.all()
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
        operation_description='Возвращает список всех отзывов. Можно фильтровать отзывы по `hall_id` (ID зала) или `club_id` (ID клуба), передав их в качестве query-параметров. Например, `/reviews/?hall_id=1`.',
        manual_parameters=[
            openapi.Parameter('hall_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description='ID зала для фильтрации отзывов'),
            openapi.Parameter('club_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description='ID клуба для фильтрации отзывов')
        ],
        responses={200: ReviewSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Оставить новый отзыв',
        operation_description='Создает новый отзыв для зала или клуба. **Требуется авторизация.** В теле запроса нужно указать `hall` или `club`, `rating` и `text`.',
        request_body=ReviewSerializer,
        responses={201: ReviewSerializer(), 401: 'Не авторизован', 400: 'Неверные данные'}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Получить детали отзыва',
        operation_description='Возвращает полную информацию о конкретном отзыве по его ID.',
        responses={200: ReviewSerializer(), 404: 'Отзыв не найден'}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Обновить отзыв (PUT)',
        operation_description='Полностью обновляет существующий отзыв по его ID. **Доступно только автору отзыва.**',
        request_body=ReviewSerializer,
        responses={200: ReviewSerializer(), 401: 'Не авторизован', 403: 'Доступ запрещен', 404: 'Отзыв не найден'}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Частично обновить отзыв (PATCH)',
        operation_description='Частично обновляет существующий отзыв по его ID. Можно изменить только некоторые поля. **Доступно только автору отзыва.**',
        request_body=ReviewSerializer,
        responses={200: ReviewSerializer(), 401: 'Не авторизован', 403: 'Доступ запрещен', 404: 'Отзыв не найден'}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Удалить отзыв',
        operation_description='Удаляет отзыв по его ID. **Доступно только автору отзыва.**',
        responses={204: 'Успешно удалено', 401: 'Не авторизован', 403: 'Доступ запрещен', 404: 'Отзыв не найден'}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
