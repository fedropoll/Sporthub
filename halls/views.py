from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Hall
from .serializers import HallSerializer

class HallViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления спортивными залами.
    """
    queryset = Hall.objects.all()
    serializer_class = HallSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @swagger_auto_schema(
        operation_summary='Получить список залов',
        operation_description='Возвращает список всех спортивных залов.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Создать новый зал',
        operation_description='Создает новый спортивный зал. Доступно только для администраторов.'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Получить информацию о зале',
        operation_description='Возвращает детальную информацию о конкретном спортивном зале по его ID.'
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Обновить зал',
        operation_description='Обновляет информацию о конкретном зале. Доступно только для администраторов.'
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Частично обновить зал',
        operation_description='Частично обновляет информацию о зале. Доступно только для администраторов.'
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Удалить зал',
        operation_description='Удаляет спортивный зал. Доступно только для администраторов.'
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)