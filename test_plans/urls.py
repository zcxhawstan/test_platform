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
    path('<int:pk>/remove_case/<int:case_id>/', TestPlanViewSet.as_view({'delete': 'remove_case'}), name='testplan-remove-case'),
]
