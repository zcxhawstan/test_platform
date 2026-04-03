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
from .services import SSHService

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
    
    def _test_ssh_connection(self, environment):
        """测试SSH连接"""
        if not environment.executor_ip or not environment.executor_username:
            return False, "请配置执行机IP和用户名"
        
        ssh_service = SSHService(environment)
        try:
            result = ssh_service.connect()
            ssh_service.close()
            return result, "连接成功" if result else "连接失败"
        except Exception as e:
            return False, str(e)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 测试SSH连接
        if request.data.get('executor_ip') and request.data.get('executor_username'):
            # 创建临时环境对象进行测试
            temp_env = Environment(
                name=request.data.get('name'),
                environment_type=request.data.get('environment_type'),
                executor_ip=request.data.get('executor_ip'),
                executor_port=request.data.get('executor_port', 22),
                executor_username=request.data.get('executor_username'),
                executor_password=request.data.get('executor_password')
            )
            
            is_connected, message = self._test_ssh_connection(temp_env)
            if not is_connected:
                return APIResponse.error(message=f'SSH连接测试失败: {message}')
        
        # 保存环境
        environment = serializer.save(created_by=request.user)
        
        # 更新连接状态
        if environment.executor_ip and environment.executor_username:
            is_connected, _ = self._test_ssh_connection(environment)
            environment.is_connected = is_connected
            environment.save()
            # 重新序列化以包含更新后的状态
            serializer = self.get_serializer(environment)
        
        return APIResponse.created(serializer.data, '环境创建成功')
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=request.method == 'PATCH')
        serializer.is_valid(raise_exception=True)
        
        # 测试SSH连接
        if request.data.get('executor_ip') or request.data.get('executor_username') or request.data.get('executor_password'):
            # 创建临时环境对象进行测试
            temp_env = Environment(
                name=instance.name,
                environment_type=instance.environment_type,
                executor_ip=request.data.get('executor_ip', instance.executor_ip),
                executor_port=request.data.get('executor_port', instance.executor_port),
                executor_username=request.data.get('executor_username', instance.executor_username),
                executor_password=request.data.get('executor_password', instance.executor_password)
            )
            
            is_connected, message = self._test_ssh_connection(temp_env)
            if not is_connected:
                return APIResponse.error(message=f'SSH连接测试失败: {message}')
        
        # 保存环境
        environment = serializer.save()
        
        # 更新连接状态
        if environment.executor_ip and environment.executor_username:
            is_connected, _ = self._test_ssh_connection(environment)
            environment.is_connected = is_connected
            environment.save()
            # 重新序列化以包含更新后的状态
            serializer = self.get_serializer(environment)
        
        return APIResponse.success(serializer.data, '环境更新成功')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='环境删除成功')
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试SSH连接"""
        environment = self.get_object()
        is_connected, message = self._test_ssh_connection(environment)
        
        # 更新连接状态
        environment.is_connected = is_connected
        environment.save()
        
        if is_connected:
            return APIResponse.success(message=f'SSH连接测试成功: {message}')
        else:
            return APIResponse.error(message=f'SSH连接测试失败: {message}')
    
    @action(detail=False, methods=['post'])
    def test_ssh(self, request):
        """测试SSH连接（不保存）"""
        # 从请求数据中获取SSH配置
        executor_ip = request.data.get('executor_ip')
        executor_port = request.data.get('executor_port', 22)
        executor_username = request.data.get('executor_username')
        executor_password = request.data.get('executor_password')
        
        if not executor_ip or not executor_username or not executor_password:
            return APIResponse.error(message='请提供完整的SSH配置信息')
        
        # 创建临时环境对象进行测试
        from .models import Environment
        temp_env = Environment(
            executor_ip=executor_ip,
            executor_port=executor_port,
            executor_username=executor_username,
            executor_password=executor_password
        )
        
        is_connected, message = self._test_ssh_connection(temp_env)
        
        if is_connected:
            return APIResponse.success(data={'is_connected': True}, message=f'SSH连接测试成功: {message}')
        else:
            return APIResponse.error(message=f'SSH连接测试失败: {message}')


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
        serializer.save(created_by=request.user, script_source='git')
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
        from .tasks import execute_automation_task
        try:
            # 尝试异步执行任务
            execute_automation_task.delay(task.id, request.user.id)
            return APIResponse.success(message='任务执行已启动')
        except Exception as e:
            # 如果异步执行失败，回退到同步执行
            print(f"异步执行失败，回退到同步执行: {str(e)}")
            execute_automation_task(task.id, request.user.id)
            return APIResponse.success(message='任务执行已启动（同步模式）')
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止任务"""
        task = self.get_object()
        # 这里将在后续实现任务停止
        return APIResponse.success(message='任务已停止')


class ExecutionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """执行历史视图集"""
    queryset = ExecutionHistory.objects.all().order_by('-created_at')
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

