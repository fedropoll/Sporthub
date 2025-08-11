from django.db.models import Avg, Count
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Hall, Club, Review
from .serializers import (
    HallSerializer, ClubSerializer, ReviewSerializer,
    HallDetailSerializer, ClubDetailSerializer
)
from .permissions import IsAuthorOrReadOnly


class HallViewSet(viewsets.ReadOnlyModelViewSet):
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
        operation_description='Возвращает краткий список всех залов с возможностью фильтрации и поиска.',
        manual_parameters=[
            openapi.Parameter('hall_type', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Тип зала (indoor, outdoor, mixed)'),
            openapi.Parameter('coating', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Покрытие'),
            openapi.Parameter('dressing_room', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Наличие раздевалки'),
            openapi.Parameter('shower', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Наличие душа'),
            openapi.Parameter('lighting', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='Наличие освещения'),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Поиск по названию, адресу, инвентарю')
        ]
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
    queryset = Club.objects.all().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['hall']
    search_fields = ['name', 'description', 'coach']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClubDetailSerializer
        return ClubSerializer

    @swagger_auto_schema(
        tags=['🏀Клубы'],
        operation_summary='Получить список клубов',
        operation_description='Возвращает краткий список всех баскетбольных клубов. Можно фильтровать по `hall_id` и искать по `name`, `description`, `coach`.',
        manual_parameters=[
            openapi.Parameter('hall', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='ID зала, где находится клуб'),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Поиск по названию, описанию, тренеру')
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏀Клубы'],
        operation_summary='Получить детали клуба',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['🏀Клубы'],
        operation_summary='Получить отзывы клуба',
    )
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        club = self.get_object()
        reviews = club.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
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
        manual_parameters=[
            openapi.Parameter('hall_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description='ID зала для фильтрации отзывов'),
            openapi.Parameter('club_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description='ID клуба для фильтрации отзывов')
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Оставить новый отзыв',
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Получить детали отзыва',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Обновить отзыв (PUT)',
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Частично обновить отзыв (PATCH)',
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['📝 Отзывы'],
        operation_summary='Удалить отзыв',
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)