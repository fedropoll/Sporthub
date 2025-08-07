from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

# Setting up Swagger/OpenAPI documentation
schema_view = get_schema_view(
    openapi.Info(
        title="Sporthub API",
        default_version='v1',
        description="API для проекта Sporthub",
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Swagger documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/basketball/', include('main.urls')),  # Corrected path for the main app's URLs
]