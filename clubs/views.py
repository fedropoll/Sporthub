from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Club
from .serializers import ClubSerializer


class ClubViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления кружками и секциями.
    """
    queryset = Club.objects.all()
    serializer_class = ClubSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @swagger_auto_schema(
        operation_summary='Получить список кружков',
        operation_description='Возвращает список всех кружков.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Создать новый кружок',
        operation_description='Создает новый кружок. Доступно только для администраторов.'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Получить информацию о кружке',
        operation_description='Возвращает детальную информацию о конкретном кружке по его ID.'
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Обновить кружок',
        operation_description='Обновляет информацию о кружке. Доступно только для администраторов.'
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Частично обновить кружок',
        operation_description='Частично обновляет информацию о кружке. Доступно только для администраторов.'
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Удалить кружок',
        operation_description='Удаляет кружок. Доступно только для администраторов.'
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)