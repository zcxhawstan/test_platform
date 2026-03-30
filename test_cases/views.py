"""
Test case views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from utils.response import APIResponse
from utils.permissions import IsOwnerOrReadOnly, IsAdminUser
from .models import TestCase
from .serializers import TestCaseSerializer, TestCaseImportSerializer
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment
from io import BytesIO


class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['module', 'priority', 'status']
    search_fields = ['title', 'description', 'module']
    ordering_fields = ['created_at', 'priority', 'title']
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
    def import_excel(self, request):
        serializer = TestCaseImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = pd.read_excel(file)
            created_count = 0
            for _, row in df.iterrows():
                TestCase.objects.create(
                    title=row.get('标题', ''),
                    description=row.get('描述', ''),
                    module=row.get('模块', ''),
                    priority=row.get('优先级', 'medium'),
                    status=row.get('状态', 'draft'),
                    preconditions=row.get('前置条件', ''),
                    steps=[],
                    expected_result=row.get('预期结果', ''),
                    created_by=request.user
                )
                created_count += 1
            return APIResponse.success({'count': created_count}, f'成功导入{created_count}条用例')
        except Exception as e:
            return APIResponse.error(f'导入失败: {str(e)}', 400)

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = '测试用例'
        
        headers = ['标题', '描述', '模块', '优先级', '状态', '前置条件', '预期结果', '创建人', '创建时间']
        ws.append(headers)
        
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        for case in queryset:
            ws.append([
                case.title,
                case.description or '',
                case.module,
                case.get_priority_display(),
                case.get_status_display(),
                case.preconditions or '',
                case.expected_result,
                case.created_by.username,
                case.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        from django.http import HttpResponse
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=test_cases.xlsx'
        return response
