"""
Test plan views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from utils.response import APIResponse
from utils.permissions import IsOwnerOrReadOnly, IsAdminUser
from .models import TestPlan, TestPlanCase
from .serializers import (
    TestPlanSerializer, TestPlanDetailSerializer,
    AddCaseToPlanSerializer, ExecuteCaseSerializer
)
from .services import TestPlanService


class TestPlanViewSet(viewsets.ModelViewSet):
    queryset = TestPlan.objects.all()
    serializer_class = TestPlanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'start_date', 'name']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminUser()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TestPlanDetailSerializer
        return TestPlanSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return APIResponse.success({
                'results': serializer.data,
                'count': self.paginator.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            })
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success({
            'results': serializer.data,
            'count': len(serializer.data)
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse.success(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse.created(serializer.data, '测试计划创建成功')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse.success(serializer.data, '测试计划更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='测试计划删除成功')

    @action(detail=True, methods=['post'])
    def add_cases(self, request, pk=None):
        plan = self.get_object()
        serializer = AddCaseToPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        count = TestPlanService.add_cases_to_plan(plan.id, serializer.validated_data['test_case_ids'])
        if count is None:
            return APIResponse.error('测试计划不存在', 404)
        
        return APIResponse.success({'count': count}, f'成功添加{count}条用例')

    @action(detail=True, methods=['delete'])
    def remove_case(self, request, pk=None, case_id=None):
        success = TestPlanService.remove_case_from_plan(pk, case_id)
        if not success:
            return APIResponse.error('用例不存在', 404)
        return APIResponse.success(message='用例移除成功')

    @action(detail=True, methods=['post'], url_path='cases/(?P<case_id>[^/.]+)/execute')
    def execute_case(self, request, pk=None, case_id=None):
        serializer = ExecuteCaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        plan_case = TestPlanService.execute_case(
            pk, case_id,
            serializer.validated_data['execution_status'],
            serializer.validated_data.get('actual_result', ''),
            request.user
        )
        
        if not plan_case:
            return APIResponse.error('用例不存在', 404)
        
        return APIResponse.success({'plan_case_id': plan_case.id}, '用例执行成功')

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = TestPlanService.get_statistics()
        return APIResponse.success(stats, '统计数据获取成功')
