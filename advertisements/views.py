from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Advertisement
from .serializers import AdvertisementSerializer


class AdvertisementViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления рекламными объявлениями.
    """
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @swagger_auto_schema(
        operation_summary='Получить список объявлений',
        operation_description='Возвращает список всех рекламных объявлений.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Создать новое объявление',
        operation_description='Создает новое рекламное объявление. Доступно только для администраторов.'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Получить информацию об объявлении',
        operation_description='Возвращает детальную информацию о конкретном объявлении по его ID.'
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Обновить объявление',
        operation_description='Обновляет информацию об объявлении. Доступно только для администраторов.'
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Частично обновить объявление',
        operation_description='Частично обновляет информацию об объявлении. Доступно только для администраторов.'
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Удалить объявление',
        operation_description='Удаляет рекламное объявление. Доступно только для администраторов.'
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)