"""
Defect views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from utils.response import APIResponse
from utils.permissions import IsOwnerOrReadOnly, IsAdminUser
from .models import Defect, DefectComment
from .serializers import (
    DefectSerializer, DefectUpdateSerializer,
    DefectCommentSerializer, DefectStatusUpdateSerializer
)
from .services import DefectService


class DefectViewSet(viewsets.ModelViewSet):
    queryset = Defect.objects.all()
    serializer_class = DefectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'severity', 'priority', 'module', 'assigned_to']
    search_fields = ['title', 'description', 'module']
    ordering_fields = ['created_at', 'priority', 'severity', 'title']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminUser()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return DefectUpdateSerializer
        return DefectSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return APIResponse.success({
                'results': serializer.data,
                'count': self.paginator.page.paginator.count,
                'next': self.paginator.get_next_link(),
                'previous': self.paginator.get_previous_link()
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
        return APIResponse.created(serializer.data, '缺陷创建成功')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse.success(serializer.data, '缺陷更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='缺陷删除成功')

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        defect = self.get_object()
        serializer = DefectStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_defect = DefectService.update_defect_status(
            defect.id,
            serializer.validated_data['status'],
            request.user,
            serializer.validated_data.get('comment', '')
        )
        
        if not updated_defect:
            return APIResponse.error('缺陷不存在', 404)
        
        return APIResponse.success({'status': updated_defect.status}, '状态更新成功')

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        defect = self.get_object()
        serializer = DefectCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        comment = DefectService.add_comment(
            defect.id,
            serializer.validated_data['content'],
            request.user
        )
        
        if not comment:
            return APIResponse.error('缺陷不存在', 404)
        
        return APIResponse.success(DefectCommentSerializer(comment).data, '评论添加成功')

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = DefectService.get_statistics()
        return APIResponse.success(stats, '统计数据获取成功')
