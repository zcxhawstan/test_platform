"""
Log views.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from utils.response import APIResponse
from utils.permissions import IsAdminUser
from .models import OperationLog, ErrorLog
from .serializers import OperationLogSerializer, ErrorLogSerializer
from .services import LogService


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OperationLog.objects.all()
    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user', 'action', 'module']
    search_fields = ['description', 'request_url']
    ordering_fields = ['created_at', 'execution_time']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = LogService.get_statistics()
        return APIResponse.success(stats, '统计数据获取成功')


class ErrorLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ErrorLog.objects.all()
    serializer_class = ErrorLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['level', 'module', 'user']
    search_fields = ['message', 'module']
    ordering_fields = ['created_at', 'level']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = LogService.get_statistics()
        return APIResponse.success(stats, '统计数据获取成功')
