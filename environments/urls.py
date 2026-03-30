"""
Environment URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EnvironmentViewSet

router = DefaultRouter()
router.register(r'', EnvironmentViewSet, basename='environment')

urlpatterns = [
    path('', include(router.urls)),
]
