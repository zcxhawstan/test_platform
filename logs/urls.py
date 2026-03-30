"""
Log URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OperationLogViewSet, ErrorLogViewSet

router = DefaultRouter()
router.register(r'operations', OperationLogViewSet, basename='operationlog')
router.register(r'errors', ErrorLogViewSet, basename='errorlog')

urlpatterns = [
    path('', include(router.urls)),
]
