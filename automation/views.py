from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import AutomationTask, ExecutionHistory, Environment, Report
from .serializers import (
    AutomationTaskSerializer, ExecutionHistorySerializer,
    EnvironmentSerializer, ReportSerializer, LogSerializer
)
from utils.response import APIResponse
import os


class EnvironmentViewSet(viewsets.ModelViewSet):
    """执行环境视图集"""
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """创建环境"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        environment = serializer.save(created_by=request.user)
        return APIResponse.success(
            data=EnvironmentSerializer(environment).data,
            message='环境创建成功'
        )
    
    def update(self, request, *args, **kwargs):
        """更新环境"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        environment = serializer.save()
        return APIResponse.success(
            data=EnvironmentSerializer(environment).data,
            message='环境更新成功'
        )
    
    def destroy(self, request, *args, **kwargs):
        """删除环境"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='环境删除成功')
    
    def retrieve(self, request, *args, **kwargs):
        """获取单个环境"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return APIResponse.success(
            data=serializer.data,
            message='获取环境信息成功'
        )
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试已有环境的连接（针对已保存的环境）"""
        environment = self.get_object()
        try:
            from .services import SSHService
            ssh = SSHService(environment=environment)
            success, message = ssh.test_connection()
            if success:
                # 更新环境连接状态
                environment.is_connected = True
                environment.save()
                return APIResponse.success(
                    data={'is_connected': True, 'message': message},
                    message='环境连接测试成功'
                )
            else:
                environment.is_connected = False
                environment.save()
                return APIResponse.error(
                    message=f'环境连接测试失败: {message}',
                    data={'is_connected': False, 'message': message}
                )
        except Exception as e:
            environment.is_connected = False
            environment.save()
            return APIResponse.error(
                message=f'环境连接测试失败: {str(e)}',
                data={'is_connected': False, 'message': str(e)}
            )
    
    @action(detail=False, methods=['post'])
    def test_ssh(self, request):
        """测试SSH连接（针对新增环境时的临时配置测试）"""
        from .services import SSHService
        
        data = request.data
        # 支持两种参数命名方式：前端传递executor_ip等，也支持host等
        executor_ip = data.get('executor_ip') or data.get('host')
        executor_port = data.get('executor_port') or data.get('port', 22)
        executor_username = data.get('executor_username') or data.get('username')
        executor_password = data.get('executor_password') or data.get('password')
        
        # 检查必要参数
        if not executor_ip or not executor_username or not executor_password:
            return APIResponse.error(
                message='缺少必要参数：需要提供执行机IP、用户名和密码',
                data={'is_connected': False, 'message': '缺少必要参数'}
            )
        
        try:
            ssh = SSHService(
                host=executor_ip,
                port=executor_port,
                username=executor_username,
                password=executor_password
            )
            success, message = ssh.test_connection()
            if success:
                return APIResponse.success(
                    data={'is_connected': True, 'message': message},
                    message='SSH连接测试成功'
                )
            else:
                return APIResponse.error(
                    message=f'SSH连接测试失败: {message}',
                    data={'is_connected': False, 'message': message}
                )
        except Exception as e:
            return APIResponse.error(
                message=f'SSH连接测试失败: {str(e)}',
                data={'is_connected': False, 'message': str(e)}
            )


class AutomationTaskViewSet(viewsets.ModelViewSet):
    """自动化任务视图集"""
    queryset = AutomationTask.objects.all().order_by('-created_at')
    serializer_class = AutomationTaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 添加搜索功能
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        return queryset
    
    def create(self, request, *args, **kwargs):
        """创建任务"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(created_by=request.user)
        return APIResponse.success(
            data=AutomationTaskSerializer(task).data,
            message='任务创建成功'
        )
    
    def update(self, request, *args, **kwargs):
        """更新任务"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return APIResponse.success(
            data=AutomationTaskSerializer(task).data,
            message='任务更新成功'
        )
    
    def destroy(self, request, *args, **kwargs):
        """删除任务"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse.success(message='任务删除成功')
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行任务"""
        # 调试日志
        print("execute called, pk=" + str(pk) + ", user=" + str(request.user) + ", auth=" + str(request.auth))
        task = self.get_object()
        from .tasks import execute_automation_task
        
        # 检查任务是否已经在执行中
        if task.status == 'running':
            return APIResponse.error(message='任务正在执行中，不能重复执行')
        
        try:
            # 尝试异步执行任务
            result = execute_automation_task.delay(task.id, request.user.id)
            print("异步任务已提交，任务ID: " + str(result.id))
            return APIResponse.success(message='任务执行已启动', data={'task_id': result.id})
        except Exception as e:
            # 如果异步执行失败，回退到同步执行
            import traceback
            error_msg = "异步执行失败，回退到同步执行: " + str(e)
            print(error_msg)
            traceback.print_exc()
            
            try:
                # 尝试同步执行
                execute_automation_task(task.id, request.user.id)
                return APIResponse.success(message='任务执行已启动（同步模式）')
            except Exception as sync_error:
                error_msg = "同步执行也失败: " + str(sync_error)
                print(error_msg)
                traceback.print_exc()
                return APIResponse.error(message='启动任务失败: ' + str(sync_error))
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止任务"""
        from .tasks import stop_automation_task
        
        task = self.get_object()
        
        # 检查任务是否正在执行
        if task.status != 'running':
            return APIResponse.error(message='任务未在执行中，无法停止')
        
        try:
            # 调用停止任务
            result = stop_automation_task.delay(task.id, request.user.id)
            return APIResponse.success(message='停止请求已发送，任务正在停止中')
        except Exception as e:
            return APIResponse.error(message='停止任务失败: ' + str(e))


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
        if not os.path.exists(report.report_path):
            return APIResponse.error(message='报告文件不存在')
        
        # 实现文件下载逻辑
        from django.http import FileResponse
        try:
            response = FileResponse(
                open(report.report_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(report.report_path)
            )
            return response
        except Exception as e:
            return APIResponse.error(message='下载报告失败: ' + str(e))
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """在线预览报告"""
        report = self.get_object()
        if not os.path.exists(report.report_path):
            return APIResponse.error(message='报告文件不存在')
        
        # 构建报告URL
        report_index = os.path.join(report.report_path, 'index.html')
        if os.path.exists(report_index):
            # 返回报告URL，前端可以通过iframe或新窗口打开
            url = '/media/reports/allure/' + str(report.execution.id) + '/index.html'
            return APIResponse.success(data={'report_url': url}, message='报告预览URL生成成功')
        else:
            return APIResponse.error(message='报告主文件不存在')
