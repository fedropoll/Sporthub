from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenRefreshView, # Используем только TokenRefreshView
)

schema_view = get_schema_view(
    openapi.Info(
        title="Sporthub API",
        default_version='v1',
        description="API для спортивного приложения",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API
    path('api/', include('main.urls')),
    path('', include('users.urls')),

    # JWT Authentication Endpoints
    path('api/token/', TokenRefreshView.as_view(), name='token_refresh'), # Эндпоинт для refresh-токена

    # Swagger Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]