"""
Environment views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from utils.response import APIResponse
from utils.permissions import IsOwnerOrReadOnly, IsAdminUser
from .models import Environment, EnvironmentVariable
from .serializers import EnvironmentSerializer, EnvironmentCreateSerializer, EnvironmentVariableSerializer
from .services import EnvironmentService


class EnvironmentViewSet(viewsets.ModelViewSet):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['env_type', 'status']
    search_fields = ['name', 'description', 'host']
    ordering_fields = ['created_at', 'name', 'env_type']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminUser()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrReadOnly()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EnvironmentCreateSerializer
        return EnvironmentSerializer

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
        serializer.validated_data['created_by'] = request.user
        self.perform_create(serializer)
        return APIResponse.created(EnvironmentSerializer(serializer.instance).data, '环境创建成功')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return APIResponse.success(EnvironmentSerializer(instance).data, '环境更新成功')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='环境删除成功')

    @action(detail=True, methods=['post'])
    def add_variable(self, request, pk=None):
        env = self.get_object()
        key = request.data.get('key')
        value = request.data.get('value')
        description = request.data.get('description', '')
        
        if not key or not value:
            return APIResponse.error('变量名和变量值不能为空', 400)
        
        variable = EnvironmentService.add_variable(env.id, key, value, description)
        if not variable:
            return APIResponse.error('环境不存在', 404)
        
        return APIResponse.success(EnvironmentVariableSerializer(variable).data, '变量添加成功')

    @action(detail=True, methods=['delete'], url_path='variables/(?P<variable_id>[^/.]+)')
    def delete_variable(self, request, pk=None, variable_id=None):
        success = EnvironmentService.delete_variable(pk, variable_id)
        if not success:
            return APIResponse.error('变量不存在', 404)
        return APIResponse.success(message='变量删除成功')

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        stats = EnvironmentService.get_statistics()
        return APIResponse.success(stats, '统计数据获取成功')
