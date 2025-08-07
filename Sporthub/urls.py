from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
    openapi.Info(
        title="Sporthub API",
        default_version='v1',
        description="API для проекта Sporthub. Документация",
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('api/users/', include('users.urls')),
    path('api/halls/', include('halls.urls')),
    path('api/trainers/', include('trainers.urls')),
    path('api/clubs/', include('clubs.urls')),
    path('api/advertisements/', include('advertisements.urls')),
    path('api/interaction/', include('interaction.urls')),
]