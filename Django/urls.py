"""
URL configuration for Django project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/testcases/', include('test_cases.urls')),
    path('api/testplans/', include('test_plans.urls')),
    path('api/defects/', include('defects.urls')),
    path('api/apitest/', include('api_test.urls')),
    path('api/environments/', include('environments.urls')),
    path('api/logs/', include('logs.urls')),
    path('api/automation/', include('automation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
