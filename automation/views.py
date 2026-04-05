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
    queryset = AutomationTask.objects.select_related('environment').order_by('-created_at')
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


class ExecutionHistoryViewSet(viewsets.ModelViewSet):
    """执行历史视图集"""
    queryset = ExecutionHistory.objects.all().order_by('-created_at')
    serializer_class = ExecutionHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        """获取执行历史列表（带分页）"""
        # 获取分页参数
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        task_name = request.query_params.get('task_name', '')
        status = request.query_params.get('status', '')
        
        # 构建查询集
        queryset = self.get_queryset()
        
        # 添加搜索条件
        if task_name:
            queryset = queryset.filter(task__name__icontains=task_name)
        if status:
            queryset = queryset.filter(status=status)
        
        # 计算总数
        total = queryset.count()
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        queryset = queryset[start:end]
        
        # 序列化
        serializer = self.get_serializer(queryset, many=True)
        
        # 返回分页响应
        return APIResponse.success({
            'count': total,
            'results': serializer.data,
            'page': page,
            'page_size': page_size
        })
    
    def destroy(self, request, *args, **kwargs):
        """删除执行历史（只有管理员可以删除）"""
        # 检查用户是否是管理员
        if not request.user.is_admin:
            return APIResponse.error(message='权限不足，只有管理员可以删除执行历史')
        
        # 获取执行历史对象
        execution = self.get_object()
        
        # 删除相关的日志
        execution.logs.all().delete()
        
        # 删除相关的报告
        for report in execution.reports.all():
            # 删除报告文件（如果存在）
            if os.path.exists(report.report_path):
                try:
                    import shutil
                    shutil.rmtree(report.report_path)
                except Exception as e:
                    print(f"删除报告文件失败: {str(e)}")
            report.delete()
        
        # 删除执行历史
        self.perform_destroy(execution)
        
        return APIResponse.success(message='执行历史删除成功')
    
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
    
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """批量删除执行历史（只有管理员可以删除）"""
        # 检查用户是否是管理员
        if not request.user.is_admin:
            return APIResponse.error(message='权限不足，只有管理员可以删除执行历史')
        
        # 获取要删除的执行历史ID列表
        ids = request.data.get('ids', [])
        if not ids:
            return APIResponse.error(message='请提供要删除的执行历史ID')
        
        # 批量删除
        try:
            executions = ExecutionHistory.objects.filter(id__in=ids)
            for execution in executions:
                # 删除相关的日志
                execution.logs.all().delete()
                
                # 删除相关的报告
                for report in execution.reports.all():
                    # 删除报告文件（如果存在）
                    if os.path.exists(report.report_path):
                        try:
                            import shutil
                            shutil.rmtree(report.report_path)
                        except Exception as e:
                            print(f"删除报告文件失败: {str(e)}")
                    report.delete()
                
                # 删除执行历史
                execution.delete()
            
            return APIResponse.success(message=f'成功删除 {len(executions)} 条执行历史')
        except Exception as e:
            return APIResponse.error(message=f'删除执行历史失败: {str(e)}')


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """报告视图集"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载报告"""
        report = self.get_object()
        import os
        if not os.path.exists(report.report_path):
            return APIResponse.error(message='报告文件不存在')
        
        # 实现文件下载逻辑
        from django.http import FileResponse
        import zipfile
        import tempfile
        try:
            # 创建临时 ZIP 文件
            temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
            temp_zip_path = temp_zip.name
            temp_zip.close()
            
            # 将报告目录压缩成 ZIP 文件
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(report.report_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, report.report_path)
                        zipf.write(file_path, arcname)
            
            # 定义清理函数
            def cleanup(temp_path):
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            
            # 返回 ZIP 文件
            response = FileResponse(
                open(temp_zip_path, 'rb'),
                as_attachment=True,
                filename=f'report_{report.id}.zip'
            )
            
            # 添加清理回调
            response['X-Temp-File'] = temp_zip_path
            
            # 在响应完成后清理临时文件
            from django.db import close_old_connections
            def post_response_handler(sender, **kwargs):
                cleanup(temp_zip_path)
                close_old_connections()
            
            from django.core.signals import request_finished
            request_finished.connect(post_response_handler, weak=False)
            
            return response
        except Exception as e:
            # 清理临时文件
            if 'temp_zip_path' in locals() and os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
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
            # 重定向到报告的 HTML 页面
            from django.shortcuts import redirect
            url = '/media/reports/allure/' + str(report.execution.id) + '/index.html'
            return redirect(url)
        else:
            return APIResponse.error(message='报告主文件不存在')
