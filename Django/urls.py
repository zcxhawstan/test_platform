"""
URL configuration for Django project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/testcases/', include('test_cases.urls')),
    path('api/testplans/', include('test_plans.urls')),
    path('api/defects/', include('defects.urls')),
    path('api/apitest/', include('api_test.urls')),

    path('api/logs/', include('logs.urls')),
    path('api/automation/', include('automation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 前端SPA托管：构建产物存在时，静态资源直出 + 根路径/未匹配路径返回 index.html
_frontend_index = os.path.join(settings.FRONTEND_DIST, 'index.html')
if os.path.isfile(_frontend_index):
    urlpatterns += [
        # 前端构建产物文件（assets/xxx、favicon.ico等）优先于SPA兜底匹配
        re_path(r'^(?P<path>assets/.+|favicon\.ico|logo\.png)$',
                static_serve, {'document_root': settings.FRONTEND_DIST}),
        re_path(r'^$', static_serve, {'path': 'index.html', 'document_root': settings.FRONTEND_DIST}),
        # SPA history 路由兜底：非 /api /admin /media /static /assets 开头的路径回退到 index.html
        re_path(r'^(?!api/|admin/|media/|static/|assets/).*$', static_serve, {'path': 'index.html', 'document_root': settings.FRONTEND_DIST}),
    ]
