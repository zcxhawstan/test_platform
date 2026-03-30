"""
Test case URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestCaseViewSet

router = DefaultRouter()
router.register(r'', TestCaseViewSet, basename='testcase')

urlpatterns = [
    path('', include(router.urls)),
]
