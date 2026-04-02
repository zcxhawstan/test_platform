from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EnvironmentViewSet, AutomationTaskViewSet, ExecutionHistoryViewSet, ReportViewSet

router = DefaultRouter()
router.register(r'environments', EnvironmentViewSet, basename='environment')
router.register(r'tasks', AutomationTaskViewSet, basename='automation-task')
router.register(r'executions', ExecutionHistoryViewSet, basename='execution')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
