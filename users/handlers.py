import logging
from django.http import JsonResponse
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status
from .exceptions import BaseAPIException
from django.conf import settings

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для стандартизации ответов API.
    """
    # Обрабатываем исключения DRF
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        # Если это наше кастомное исключение
        if isinstance(exc, BaseAPIException):
            error_data = {
                'status': 'error',
                'code': exc.default_code,
                'message': str(exc.detail) if hasattr(exc, 'detail') else exc.default_detail,
                'data': {}
            }
            return JsonResponse(error_data, status=exc.status_code)
            
        # Если это стандартное исключение DRF
        error_data = {
            'status': 'error',
            'code': getattr(exc, 'default_code', 'error'),
            'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            'data': {}
        }
        
        # Добавляем поля валидации, если они есть
        if hasattr(exc, 'get_full_details'):
            error_data['data'] = exc.get_full_details()
            
        return JsonResponse(error_data, status=response.status_code)
    
    # Обрабатываем непредвиденные исключения
    logger.error("Необработанное исключение: %s", str(exc), exc_info=True)
    
    error_data = {
        'status': 'error',
        'code': 'internal_server_error',
        'message': 'Внутренняя ошибка сервера',
        'data': {}
    }
    
    # В продакшене не показываем детали ошибки
    if settings.DEBUG:
        error_data['detail'] = str(exc)
    
    return JsonResponse(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_404_error(request, exception):
    """
    Обработчик 404 ошибок.
    """
    return JsonResponse({
        'status': 'error',
        'code': 'not_found',
        'message': 'Запрашиваемый ресурс не найден',
        'data': {}
    }, status=404)


def handle_500_error(request):
    """
    Обработчик 500 ошибок.
    """
    return JsonResponse({
        'status': 'error',
        'code': 'internal_server_error',
        'message': 'Внутренняя ошибка сервера',
        'data': {}
    }, status=500)
