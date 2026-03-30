"""
Test plan URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestPlanViewSet

router = DefaultRouter()
router.register(r'', TestPlanViewSet, basename='testplan')

urlpatterns = [
    path('', include(router.urls)),
]
