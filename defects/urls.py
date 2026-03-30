"""
Defect URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DefectViewSet

router = DefaultRouter()
router.register(r'', DefectViewSet, basename='defect')

urlpatterns = [
    path('', include(router.urls)),
]
