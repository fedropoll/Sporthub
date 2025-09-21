from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import RedirectView
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
    openapi.Info(
        title="Baha brat 'не' ГЕЙ",
        default_version='v1',
        description="МИРБА натурал",
    ),
    public=True,
    permission_classes=(AllowAny,),  # разрешаем всем
    url="https://sporthub-production.up.railway.app"  # <<< важно

)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API
    path('api/', include('main.urls')),
    path('', include('users.urls')),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
]