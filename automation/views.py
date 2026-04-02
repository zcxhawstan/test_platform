import os
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from utils.response import APIResponse
from utils.permissions import IsAdminUser
from .models import Environment, AutomationTask, ExecutionHistory, Log, Report
from .serializers import EnvironmentSerializer, AutomationTaskSerializer, ExecutionHistorySerializer, LogSerializer, ReportSerializer

User = get_user_model()


class EnvironmentViewSet(viewsets.ModelViewSet):
    """环境配置视图集"""
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return APIResponse.created(serializer.data, '环境创建成功')
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=request.method == 'PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse.success(serializer.data, '环境更新成功')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='环境删除成功')


class AutomationTaskViewSet(viewsets.ModelViewSet):
    """自动化任务视图集"""
    queryset = AutomationTask.objects.all()
    serializer_class = AutomationTaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return APIResponse.created(serializer.data, '任务创建成功')
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=request.method == 'PATCH')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse.success(serializer.data, '任务更新成功')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='任务删除成功')
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行任务"""
        task = self.get_object()
        # 调用Celery任务执行自动化测试
        from .tasks import execute_automation_task
        execute_automation_task.delay(task.id, request.user.id)
        return APIResponse.success(message='任务执行已启动')
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止任务"""
        task = self.get_object()
        # 这里将在后续实现任务停止
        return APIResponse.success(message='任务已停止')


class ExecutionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """执行历史视图集"""
    queryset = ExecutionHistory.objects.all()
    serializer_class = ExecutionHistorySerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取执行日志"""
        execution = self.get_object()
        logs = execution.logs.all()
        serializer = LogSerializer(logs, many=True)
        return APIResponse.success(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reports(self, request, pk=None):
        """获取执行报告"""
        execution = self.get_object()
        reports = execution.reports.all()
        serializer = ReportSerializer(reports, many=True)
        return APIResponse.success(serializer.data)


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """报告视图集"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载报告"""
        report = self.get_object()
        # 构建报告文件路径
        report_dir = report.report_path
        if not os.path.exists(report_dir):
            return APIResponse.error(message='报告文件不存在')
        
        # 压缩报告目录
        import zipfile
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            zip_path = tmp_file.name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(report_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, report_dir)
                    zipf.write(file_path, arcname)
        
        # 返回文件下载响应
        response = FileResponse(open(zip_path, 'rb'))
        response['Content-Type'] = 'application/zip'
        response['Content-Disposition'] = f'attachment; filename="{report.execution.task.name}_report.zip"'
        
        # 清理临时文件
        import atexit
        import os
        atexit.register(lambda: os.remove(zip_path) if os.path.exists(zip_path) else None)
        
        return response
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """在线预览报告"""
        report = self.get_object()
        # 这里可以实现报告的在线预览功能
        # 由于Allure报告是静态HTML，需要配置静态文件服务
        return APIResponse.success(data={'report_url': report.report_url}, message='报告预览功能开发中')

