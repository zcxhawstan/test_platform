from celery import shared_task
import subprocess
import os
import time
import json
from datetime import datetime
from .models import AutomationTask, ExecutionHistory, Log, Report
from .services import execute_task_on_remote
from django.contrib.auth import get_user_model

User = get_user_model()

import traceback

def log_with_context(execution, level, message, exception=None, context=None):
    """记录带上下文信息的日志"""
    log_data = {
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'level': level,
    }
    
    if exception:
        log_data['exception'] = {
            'type': type(exception).__name__,
            'message': str(exception),
            'traceback': traceback.format_exc()
        }
    
    if context:
        log_data['context'] = context
    
    # 将日志数据转换为JSON格式，便于解析
    log_message = json.dumps(log_data, ensure_ascii=False, indent=2)
    
    # 创建日志记录
    Log.objects.create(
        execution=execution,
        level=level,
        message=log_message
    )
    
    # 同时在控制台输出（便于调试）
    print(f"[{level}] {message}")
    if exception:
        print(f"异常: {type(exception).__name__}: {str(exception)}")
        traceback.print_exc()

def log_error_with_stack(execution, message, exception, context=None):
    """记录错误信息（包含堆栈跟踪）"""
    log_with_context(execution, 'ERROR', message, exception, context)

def log_info_with_context(execution, message, context=None):
    """记录信息日志（带上下文）"""
    log_with_context(execution, 'INFO', message, context=context)

def log_warning_with_context(execution, message, context=None):
    """记录警告日志（带上下文）"""
    log_with_context(execution, 'WARNING', message, context=context)


@shared_task
def generate_allure_report(execution_id):
    """生成Allure报告"""
    try:
        execution = ExecutionHistory.objects.get(id=execution_id)
        
        # 记录开始生成报告
        log_info_with_context(
            execution=execution,
            message='开始生成Allure报告',
            context={'execution_id': execution_id, 'report_type': 'allure'}
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
            log_warning_with_context(
                execution=execution,
                message='Allure结果目录不存在，跳过报告生成',
                context={'result_dir': result_dir, 'execution_id': execution_id}
            )
            
    except Exception as e:
        if 'execution' in locals():
            log_error_with_stack(
                execution=execution,
                message=f'生成Allure报告异常',
                exception=e,
                context={'execution_id': execution_id, 'report_type': 'allure'}
            )


@shared_task
def execute_automation_task(task_id, user_id):
    """执行自动化测试任务"""
    try:
        # 获取任务和用户
        task = AutomationTask.objects.get(id=task_id)
        user = User.objects.get(id=user_id)
        
        # 更新任务状态为执行中
        task.status = 'running'
        task.save()
        
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
        log_info_with_context(
            execution=execution,
            message=f'开始执行任务: {task.name}',
            context={
                'task_id': task_id,
                'task_name': task.name,
                'user_id': user_id,
                'script_path': task.script_path,
                'environment_id': task.environment.id if task.environment else None
            }
        )
        
        # 构建执行命令（平台内部处理）
        script_path = task.script_path
        execution_command = f"pytest {script_path} --alluredir=./result"
        
        # 设置执行环境
        env = os.environ.copy()
        if task.environment and task.environment.variables:
            env.update(task.environment.variables)
        
        # 检查是否配置了执行机信息
        if task.environment and task.environment.executor_ip and task.environment.executor_username:
            # 使用远程执行
            log_info_with_context(
                execution=execution,
                message=f'开始在远程执行机 {task.environment.executor_ip} 上执行任务',
                context={
                    'executor_ip': task.environment.executor_ip,
                    'executor_port': task.environment.executor_port,
                    'executor_username': task.environment.executor_username,
                    'docker_image': task.environment.docker_image,
                    'environment_id': task.environment.id
                }
            )
            
            try:
                success, stdout, stderr = execute_task_on_remote(task, task.environment)
                if success:
                    exit_code = 0
                    log_info_with_context(
                        execution=execution,
                        message=f'远程执行成功',
                        context={'success': True, 'exit_code': 0, 'has_stdout': bool(stdout), 'has_stderr': bool(stderr)}
                    )
                    # 记录远程执行的输出
                    if stdout:
                        log_info_with_context(
                            execution=execution,
                            message=f'远程执行输出（截断）',
                            context={'stdout_preview': stdout[:500] if stdout else '', 'stdout_length': len(stdout) if stdout else 0}
                        )
                else:
                    exit_code = 1
                    error_message = stdout if stdout else stderr if stderr else '未知错误'
                    log_with_context(
                        execution=execution,
                        level='ERROR',
                        message=f'远程执行失败',
                        context={'error_message': error_message, 'stdout': stdout if stdout else '', 'stderr': stderr if stderr else '', 'exit_code': exit_code}
                    )
            except Exception as e:
                exit_code = 1
                stdout = ''
                stderr = str(e)
                log_error_with_stack(
                    execution=execution,
                    message=f'远程执行异常',
                    exception=e,
                    context={'executor_ip': task.environment.executor_ip, 'executor_username': task.environment.executor_username, 'exit_code': exit_code}
                )
        else:
            # 使用本地执行
            try:
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
                
                # 记录本地执行的输出
                if stdout:
                    log_info_with_context(
                        execution=execution,
                        message=f'本地执行输出（截断）',
                        context={'stdout_preview': stdout[:500] if stdout else '', 'stdout_length': len(stdout) if stdout else 0}
                    )
            except Exception as e:
                exit_code = 1
                stdout = ''
                stderr = str(e)
                log_error_with_stack(
                    execution=execution,
                    message=f'本地执行异常',
                    exception=e,
                    context={'execution_command': execution_command, 'exit_code': exit_code}
                )
        
        # 记录执行日志
        if stdout:
            lines = [line.strip() for line in stdout.split('\n') if line.strip()]
            if lines:
                log_info_with_context(
                    execution=execution,
                    message=f'标准输出日志（共{len(lines)}行）',
                    context={
                        'stdout_line_count': len(lines),
                        'stdout_preview': lines[:5],  # 前5行预览
                        'stdout_total_length': len(stdout)
                    }
                )
        
        if stderr:
            lines = [line.strip() for line in stderr.split('\n') if line.strip()]
            if lines:
                log_with_context(
                    execution=execution,
                    level='ERROR',
                    message=f'错误输出日志（共{len(lines)}行）',
                    context={
                        'stderr_line_count': len(lines),
                        'stderr_preview': lines[:5],  # 前5行预览
                        'stderr_total_length': len(stderr)
                    }
                )
        
        # 更新执行状态
        if exit_code == 0:
            execution.status = 'success'
            log_info_with_context(
                execution=execution,
                message=f'任务执行成功，退出码: {exit_code}',
                context={'exit_code': exit_code, 'status': execution.status, 'duration': execution.duration if hasattr(execution, 'duration') else None}
            )
        else:
            execution.status = 'failed'
            log_with_context(
                execution=execution,
                level='ERROR',
                message=f'任务执行失败，退出码: {exit_code}',
                context={'exit_code': exit_code, 'status': execution.status, 'duration': execution.duration if hasattr(execution, 'duration') else None}
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
            log_error_with_stack(
                execution=execution,
                message=f'任务执行异常',
                exception=e,
                context={'task_id': task_id, 'user_id': user_id, 'status': 'error'}
            )
            execution.status = 'error'
            execution.save()
            task.status = 'error'
            task.save()
        return {'status': 'error', 'message': str(e)}
