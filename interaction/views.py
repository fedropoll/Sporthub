from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Review, Payment, Notification
from .serializers import ReviewSerializer, PaymentSerializer, NotificationSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления отзывами.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary='Получить список отзывов',
        operation_description='Возвращает список всех отзывов.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Создать новый отзыв',
        operation_description='Создает новый отзыв. Доступно для авторизованных пользователей.'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления платежами.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        operation_summary='Получить список платежей',
        operation_description='Возвращает список всех платежей. Доступно только для администраторов.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Создать новый платеж',
        operation_description='Создает новый платеж. Доступно только для администраторов.'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления уведомлениями.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_summary='Получить список уведомлений',
        operation_description='Возвращает список уведомлений текущего пользователя.'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Создать новое уведомление',
        operation_description='Создает новое уведомление. Доступно только для администраторов.'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary='Удалить уведомление',
        operation_description='Удаляет уведомление. Доступно только для администраторов.'
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)