"""
API test views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from utils.response import APIResponse
from utils.permissions import IsOwnerOrReadOnly, IsAdminUser
from .models import ApiEnvironment, ApiTestCase, ApiTestExecution
from .serializers import (
    ApiEnvironmentSerializer, ApiTestCaseSerializer,
    ApiTestExecutionSerializer, ExecuteApiTestSerializer
)
from .services import ApiTestService


class ApiEnvironmentViewSet(viewsets.ModelViewSet):
    queryset = ApiEnvironment.objects.all()
    serializer_class = ApiEnvironmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminUser()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse.created(serializer.data, '环境创建成功')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse.success(serializer.data, '环境更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='环境删除成功')


class ApiTestCaseViewSet(viewsets.ModelViewSet):
    queryset = ApiTestCase.objects.all()
    serializer_class = ApiTestCaseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['method', 'environment']
    search_fields = ['name', 'description', 'path']
    ordering_fields = ['created_at', 'name', 'method']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminUser()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse.created(serializer.data, '用例创建成功')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse.success(serializer.data, '用例更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='用例删除成功')

    @action(detail=False, methods=['post'])
    def execute(self, request):
        serializer = ExecuteApiTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            execution = ApiTestService.execute_test_case(
                serializer.validated_data['test_case_id'],
                request.user
            )
            return APIResponse.success(
                ApiTestExecutionSerializer(execution).data,
                '测试执行完成'
            )
        except Exception as e:
            return APIResponse.error(f'执行失败: {str(e)}', 400)


class ApiTestExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApiTestExecution.objects.all()
    serializer_class = ApiTestExecutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'test_case']
    ordering_fields = ['executed_at', 'response_time']
    ordering = ['-executed_at']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = ApiTestService.get_statistics()
        return APIResponse.success(stats, '统计数据获取成功')
