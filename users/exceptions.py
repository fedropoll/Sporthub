from rest_framework.exceptions import APIException
from rest_framework import status


class BaseAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Произошла ошибка'
    default_code = 'error'

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail, code)


class ValidationError(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Ошибка валидации'
    default_code = 'validation_error'


class AuthenticationFailed(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Неверные учетные данные'
    default_code = 'authentication_failed'


class NotAuthenticated(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Пользователь не аутентифицирован'
    default_code = 'not_authenticated'


class PermissionDenied(BaseAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'У вас нет прав для выполнения этого действия'
    default_code = 'permission_denied'


class NotFound(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Запрашиваемый ресурс не найден'
    default_code = 'not_found'


class MethodNotAllowed(BaseAPIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = 'Метод не разрешен'
    default_code = 'method_not_allowed'


class InternalServerError(BaseAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Внутренняя ошибка сервера'
    default_code = 'internal_server_error'
