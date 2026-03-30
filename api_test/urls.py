"""
API test URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiEnvironmentViewSet, ApiTestCaseViewSet, ApiTestExecutionViewSet

router = DefaultRouter()
router.register(r'environments', ApiEnvironmentViewSet, basename='apienvironment')
router.register(r'cases', ApiTestCaseViewSet, basename='apitestcase')
router.register(r'executions', ApiTestExecutionViewSet, basename='apitestexecution')

urlpatterns = [
    path('', include(router.urls)),
]
