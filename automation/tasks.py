from celery import shared_task
import subprocess
import os
import time
import json
from datetime import datetime
from .models import AutomationTask, ExecutionHistory, Log, Report
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def execute_automation_task(task_id, user_id):
    """执行自动化测试任务"""
    try:
        # 获取任务和用户
        task = AutomationTask.objects.get(id=task_id)
        user = User.objects.get(id=user_id)
        
        # 创建执行历史记录
        execution = ExecutionHistory.objects.create(
            task=task,
            environment=task.environment,
            executor=user,
            status='running'
        )
        execution.start_time = datetime.now()
        execution.save()
        
        # 记录开始日志
        Log.objects.create(
            execution=execution,
            level='INFO',
            message=f'开始执行任务: {task.name}'
        )
        
        # 构建执行命令
        script_path = task.script_path
        execution_command = task.execution_command.replace('{script}', script_path)
        
        # 设置执行环境
        env = os.environ.copy()
        if task.environment and task.environment.variables:
            env.update(task.environment.variables)
        
        # 执行脚本
        process = subprocess.Popen(
            execution_command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            env=env
        )
        
        # 实时捕获输出
        stdout, stderr = process.communicate()
        exit_code = process.returncode
        
        # 记录执行日志
        if stdout:
            for line in stdout.split('\n'):
                if line.strip():
                    Log.objects.create(
                        execution=execution,
                        level='INFO',
                        message=line
                    )
        
        if stderr:
            for line in stderr.split('\n'):
                if line.strip():
                    Log.objects.create(
                        execution=execution,
                        level='ERROR',
                        message=line
                    )
        
        # 更新执行状态
        if exit_code == 0:
            execution.status = 'success'
            Log.objects.create(
                execution=execution,
                level='INFO',
                message=f'任务执行成功，退出码: {exit_code}'
            )
        else:
            execution.status = 'failed'
            Log.objects.create(
                execution=execution,
                level='ERROR',
                message=f'任务执行失败，退出码: {exit_code}'
            )
        
        # 更新执行历史
        execution.end_time = datetime.now()
        execution.duration = (execution.end_time - execution.start_time).total_seconds()
        execution.exit_code = exit_code
        execution.save()
        
        # 更新任务状态
        task.status = execution.status
        task.save()
        
        # 生成Allure报告（如果启用）
        if task.enable_allure:
            generate_allure_report.delay(execution.id)
        
        return {'status': execution.status, 'exit_code': exit_code}
        
    except Exception as e:
        # 记录异常
        if 'execution' in locals():
            Log.objects.create(
                execution=execution,
                level='ERROR',
                message=f'任务执行异常: {str(e)}'
            )
            execution.status = 'error'
            execution.save()
            task.status = 'error'
            task.save()
        return {'status': 'error', 'message': str(e)}


@shared_task
def generate_allure_report(execution_id):
    """生成Allure报告"""
    try:
        execution = ExecutionHistory.objects.get(id=execution_id)
        
        # 记录开始生成报告
        Log.objects.create(
            execution=execution,
            level='INFO',
            message='开始生成Allure报告'
        )
        
        # 构建报告路径
        report_dir = f'reports/allure/{execution.id}'
        os.makedirs(report_dir, exist_ok=True)
        
        # 生成报告（这里需要根据实际的Allure结果目录进行调整）
        # 假设Allure结果在./result目录
        result_dir = 'result'
        if os.path.exists(result_dir):
            # 执行Allure命令生成报告
            subprocess.run(
                f'allure generate {result_dir} -o {report_dir} --clean',
                shell=True,
                capture_output=True,
                text=True
            )
            
            # 创建报告记录
            Report.objects.create(
                execution=execution,
                report_type='allure',
                report_path=report_dir,
                report_url=f'/api/automation/reports/{execution.id}/download/',
                summary={
                    'generated_at': datetime.now().isoformat(),
                    'report_path': report_dir
                }
            )
            
            Log.objects.create(
                execution=execution,
                level='INFO',
                message=f'Allure报告生成成功: {report_dir}'
            )
        else:
            Log.objects.create(
                execution=execution,
                level='WARNING',
                message='Allure结果目录不存在，跳过报告生成'
            )
            
    except Exception as e:
        if 'execution' in locals():
            Log.objects.create(
                execution=execution,
                level='ERROR',
                message=f'生成Allure报告异常: {str(e)}'
            )
