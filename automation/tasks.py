from celery import shared_task
import subprocess
import os
import time
import json
import signal
import threading
from datetime import datetime, timedelta
from django.utils import timezone
from .models import AutomationTask, ExecutionHistory, Log, Report
from .services import execute_task_on_remote
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

import traceback

# 全局字典，用于存储正在执行的任务进程
task_processes = {}
task_locks = {}
stop_flags = {}  # 用于标记任务是否需要停止

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

def acquire_task_lock(task_id):
    """获取任务执行锁"""
    if task_id in task_locks:
        return False
    task_locks[task_id] = True
    return True

def release_task_lock(task_id):
    """释放任务执行锁"""
    if task_id in task_locks:
        del task_locks[task_id]

def set_stop_flag(task_id):
    """设置停止标志"""
    stop_flags[task_id] = True

def clear_stop_flag(task_id):
    """清除停止标志"""
    if task_id in stop_flags:
        del stop_flags[task_id]

def should_stop(task_id):
    """检查是否需要停止"""
    return stop_flags.get(task_id, False)

def kill_process_tree(pid):
    """终止进程树"""
    try:
        import psutil
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        parent.terminate()
        gone, alive = psutil.wait_procs(children + [parent], timeout=3)
        for p in alive:
            p.kill()
    except Exception as e:
        print(f"终止进程失败: {e}")

@shared_task(bind=True, max_retries=0)
def execute_automation_task(self, task_id, user_id):
    """执行自动化测试任务（带超时控制和执行锁）"""
    execution = None
    task = None
    
    try:
        # 1. 检查任务执行锁
        if not acquire_task_lock(task_id):
            return {'status': 'failed', 'message': '任务正在执行中，请等待上一次执行完成'}
        
        # 获取任务和用户
        task = AutomationTask.objects.get(id=task_id)
        user = User.objects.get(id=user_id)
        
        # 2. 检查任务是否已经在执行中
        if task.status == 'running':
            release_task_lock(task_id)
            return {'status': 'failed', 'message': '任务正在执行中，不能重复执行'}
        
        # 3. 更新任务状态为执行中
        task.status = 'running'
        task.save()
        
        # 4. 创建执行历史记录
        execution = ExecutionHistory.objects.create(
            task=task,
            environment=task.environment,
            executor=user,
            status='running'
        )
        execution.start_time = timezone.now()
        execution.save()
        
        # 5. 记录开始日志
        log_info_with_context(
            execution=execution,
            message=f'开始执行任务: {task.name}',
            context={
                'task_id': task_id,
                'task_name': task.name,
                'user_id': user_id,
                'script_path': task.script_path,
                'environment_id': task.environment.id if task.environment else None,
                'timeout': task.timeout
            }
        )
        
        # 6. 获取超时时间
        timeout_seconds = task.timeout if task.timeout else 1800  # 默认30分钟
        log_info_with_context(
            execution=execution,
            message=f'任务超时时间设置为: {timeout_seconds} 秒',
            context={'timeout': timeout_seconds}
        )
        
        # 7. 构建执行命令
        script_path = task.script_path
        execution_command = f"pytest {script_path} --alluredir=./result --clean-alluredir -v"
        
        # 设置执行环境
        env = os.environ.copy()
        if task.environment and task.environment.variables:
            env.update(task.environment.variables)
        
        exit_code = None
        stdout = ''
        stderr = ''
        
        # 8. 执行命令（带超时控制）
        try:
            if task.environment and task.environment.executor_ip and task.environment.executor_username:
                # 远程执行
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
                
                # 远程执行（带超时）
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(execute_task_on_remote, task, task.environment, execution)
                    try:
                        success, stdout, stderr = future.result(timeout=timeout_seconds)
                        if success:
                            exit_code = 0
                            log_info_with_context(
                                execution=execution,
                                message=f'远程执行成功',
                                context={'success': True, 'exit_code': 0}
                            )
                        else:
                            exit_code = 1
                            log_error_with_stack(
                                execution=execution,
                                message=f'远程执行失败',
                                exception=Exception(stderr if stderr else '未知错误'),
                                context={'stdout': stdout[:500] if stdout else '', 'stderr': stderr[:500] if stderr else ''}
                            )
                    except concurrent.futures.TimeoutError:
                        exit_code = -1
                        log_error_with_stack(
                            execution=execution,
                            message=f'任务执行超时（{timeout_seconds}秒）',
                            exception=Exception('任务执行超时'),
                            context={'timeout': timeout_seconds}
                        )
            else:
                # 本地执行（带超时）
                log_info_with_context(
                    execution=execution,
                    message=f'开始本地执行任务',
                    context={'execution_command': execution_command}
                )
                
                process = subprocess.Popen(
                    execution_command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )
                
                # 存储进程ID，用于可能的终止操作
                task_processes[execution.id] = process
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout_seconds)
                    exit_code = process.returncode
                    
                    log_info_with_context(
                        execution=execution,
                        message=f'本地执行完成',
                        context={'exit_code': exit_code, 'stdout_length': len(stdout), 'stderr_length': len(stderr)}
                    )
                except subprocess.TimeoutExpired:
                    # 超时处理
                    kill_process_tree(process.pid)
                    exit_code = -1
                    stdout = ''
                    stderr = f'任务执行超时（{timeout_seconds}秒）'
                    
                    log_error_with_stack(
                        execution=execution,
                        message=f'任务执行超时（{timeout_seconds}秒）',
                        exception=Exception('任务执行超时'),
                        context={'timeout': timeout_seconds}
                    )
        except Exception as e:
            exit_code = 1
            stderr = str(e)
            log_error_with_stack(
                execution=execution,
                message=f'执行过程异常',
                exception=e,
                context={'error': str(e)}
            )
        
        # 9. 记录输出日志
        if stdout:
            # 按行分割并记录
            lines = [line.strip() for line in stdout.split('\n') if line.strip()]
            if lines:
                log_info_with_context(
                    execution=execution,
                    message=f'标准输出日志（共{len(lines)}行）',
                    context={
                        'stdout_line_count': len(lines),
                        'stdout_preview': lines[:10],  # 前10行预览
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
                        'stderr_preview': lines[:10],  # 前10行预览
                        'stderr_total_length': len(stderr)
                    }
                )
        
        # 10. 更新执行状态
        if exit_code == 0:
            final_status = 'success'
            log_info_with_context(
                execution=execution,
                message=f'任务执行成功，退出码: {exit_code}',
                context={'exit_code': exit_code, 'status': final_status}
            )
        elif exit_code == -1:
            final_status = 'timeout'
            log_warning_with_context(
                execution=execution,
                message=f'任务执行超时，退出码: {exit_code}',
                context={'exit_code': exit_code, 'status': final_status, 'timeout': timeout_seconds}
            )
        else:
            final_status = 'failed'
            log_error_with_stack(
                execution=execution,
                message=f'任务执行失败，退出码: {exit_code}',
                exception=Exception(stderr),
                context={'exit_code': exit_code, 'status': final_status}
            )
        
        # 11. 更新执行历史
        execution.status = final_status
        execution.end_time = timezone.now()
        if execution.start_time:
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
        execution.exit_code = exit_code
        execution.save()
        
        # 12. 更新任务状态
        task.status = final_status
        task.save()
        
        # 13. 生成Allure报告（如果启用）
        if task.enable_allure and final_status == 'success':
            generate_allure_report.delay(execution.id)
        
        # 14. 记录完成日志
        log_info_with_context(
            execution=execution,
            message=f'任务执行流程完成，状态: {final_status}',
            context={
                'status': final_status,
                'exit_code': exit_code,
                'duration': execution.duration,
                'has_report': task.enable_allure and final_status == 'success'
            }
        )
        
        return {'status': final_status, 'exit_code': exit_code, 'duration': execution.duration}
        
    except Exception as e:
        # 记录异常
        if execution:
            log_error_with_stack(
                execution=execution,
                message=f'任务执行流程异常',
                exception=e,
                context={'task_id': task_id, 'user_id': user_id, 'status': 'error'}
            )
            execution.status = 'error'
            execution.end_time = timezone.now()
            execution.save()
        
        if task:
            task.status = 'error'
            task.save()
        
        return {'status': 'error', 'message': str(e)}
    
    finally:
        # 15. 清理资源
        if task_id in task_processes:
            del task_processes[task_id]
        clear_stop_flag(task_id)
        release_task_lock(task_id)


@shared_task
def stop_automation_task(task_id, user_id):
    """停止自动化测试任务"""
    try:
        task = AutomationTask.objects.get(id=task_id)
        user = User.objects.get(id=user_id)
        
        # 检查任务是否正在执行
        if task.status != 'running':
            return {'status': 'failed', 'message': '任务未在执行中，无法停止'}
        
        # 设置停止标志
        set_stop_flag(task_id)
        
        # 获取正在执行的进程
        execution = ExecutionHistory.objects.filter(
            task=task,
            status='running'
        ).first()
        
        if execution:
            # 记录停止日志
            log_info_with_context(
                execution=execution,
                message=f'用户 {user.username} 请求停止任务',
                context={'task_id': task_id, 'user_id': user_id, 'username': user.username}
            )
            
            # 终止进程
            if execution.id in task_processes:
                process = task_processes[execution.id]
                try:
                    kill_process_tree(process.pid)
                    log_info_with_context(
                        execution=execution,
                        message='进程已终止',
                        context={'pid': process.pid}
                    )
                except Exception as e:
                    log_error_with_stack(
                        execution=execution,
                        message='终止进程失败',
                        exception=e
                    )
            
            # 更新执行历史
            execution.status = 'stopped'
            execution.end_time = timezone.now()
            if execution.start_time:
                execution.duration = (execution.end_time - execution.start_time).total_seconds()
            execution.exit_code = -2  # 停止状态码
            execution.save()
            
            # 记录停止完成日志
            log_info_with_context(
                execution=execution,
                message='任务已停止',
                context={'duration': execution.duration}
            )
        
        # 更新任务状态
        task.status = 'stopped'
        task.save()
        
        # 释放锁
        release_task_lock(task_id)
        clear_stop_flag(task_id)
        
        return {'status': 'success', 'message': '任务已停止'}
        
    except AutomationTask.DoesNotExist:
        return {'status': 'failed', 'message': '任务不存在'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task

def generate_allure_report(execution_id):
    """生成Allure报告"""
    try:
        execution = ExecutionHistory.objects.get(id=execution_id)
        task = execution.task
        environment = execution.environment
        
        # 记录开始生成报告
        log_info_with_context(
            execution=execution,
            message='开始生成Allure报告',
            context={'execution_id': execution_id, 'report_type': 'allure'}
        )
        
        # 构建报告路径（存储在media目录下，便于Web访问）
        report_dir = f'media/reports/allure/{execution.id}'
        # 确保os模块可用
        import os
        os.makedirs(report_dir, exist_ok=True)
        
        # 生成报告（根据执行环境选择不同的方式）
        if environment and environment.executor_ip and environment.executor_username:
            # 远程执行，需要从远程复制Allure结果
            log_info_with_context(
                execution=execution,
                message='远程执行环境，开始从远程复制Allure结果',
                context={'executor_ip': environment.executor_ip, 'execution_id': execution_id}
            )
            
            # 构建远程Allure结果目录路径
            repo_name = task.git_repo.split('/')[-1].replace('.git', '') if task.git_repo else 'Auto_Test'
            remote_result_dir = f'/opt/automation/repos/{repo_name}/result'
            
            # 连接到远程执行机
            from .services import SSHService
            ssh_service = SSHService(environment=environment, execution=execution)
            
            if ssh_service.connect():
                try:
                    # 检查远程Allure结果目录是否存在
                    check_cmd = f'ls -la {remote_result_dir}'
                    success, stdout, stderr = ssh_service.execute_command(check_cmd)
                    
                    if success and 'No such file or directory' not in stderr:
                        # 压缩远程Allure结果
                        remote_zip = f'allure_result_{execution.id}.zip'
                        # 在Docker容器中执行zip命令，这样只会压缩本次执行的结果
                        container_name = f'automation-{execution.environment.id}'
                        zip_cmd = f'docker exec {container_name} bash -c "cd {remote_result_dir} && zip -r {remote_zip} ."'
                        success, stdout, stderr = ssh_service.execute_command(zip_cmd)
                        
                        if success:
                            # 下载压缩文件到本地
                            import tempfile
                            import os
                            # 使用临时目录来存储下载的文件
                            with tempfile.TemporaryDirectory() as temp_dir:
                                local_zip = os.path.join(temp_dir, f'allure_result_{execution.id}.zip')
                                from scp import SCPClient
                                scp = SCPClient(ssh_service.client.get_transport())
                                # 从容器中复制文件到宿主机
                                copy_cmd = f'docker cp {container_name}:{remote_result_dir}/{remote_zip} {remote_result_dir}/'
                                success_copy, stdout_copy, stderr_copy = ssh_service.execute_command(copy_cmd)
                                if success_copy:
                                    # 从宿主机下载文件
                                    scp.get(f'{remote_result_dir}/{remote_zip}', local_zip)
                                else:
                                    raise Exception(f'从容器复制文件失败: {stderr_copy}')
                                scp.close()
                                
                                # 解压到本地临时目录
                                import zipfile
                                with zipfile.ZipFile(local_zip, 'r') as zip_ref:
                                    zip_ref.extractall(temp_dir)
                                
                                # 执行Allure命令生成报告
                                subprocess.run(
                                    f'allure generate {temp_dir} -o {report_dir} --clean',
                                    shell=True,
                                    capture_output=True,
                                    text=True
                                )
                            
                            # 删除远程临时文件
                            ssh_service.execute_command(f'rm -f {remote_result_dir}/{remote_zip}')
                            
                            # 创建报告记录
                            report = Report.objects.create(
                                execution=execution,
                                report_type='allure',
                                report_path=report_dir,
                                report_url=f'/api/automation/reports/{execution.id}/download/',  # 临时URL，稍后更新
                                summary={
                                    'generated_at': datetime.now().isoformat(),
                                    'report_path': report_dir
                                }
                            )
                            
                            # 更新报告URL为正确的预览URL
                            report.report_url = f'/api/automation/reports/{report.id}/preview/'
                            report.save()
                            
                            Log.objects.create(
                                execution=execution,
                                level='INFO',
                                message=json.dumps({
                                    'message': f'Allure报告生成成功（远程执行）',
                                    'timestamp': datetime.now().isoformat(),
                                    'level': 'INFO',
                                    'context': {'report_dir': report_dir, 'executor_ip': environment.executor_ip}
                                }, ensure_ascii=False)
                            )
                        else:
                            log_warning_with_context(
                                execution=execution,
                                message='压缩远程Allure结果失败',
                                context={'remote_result_dir': remote_result_dir, 'error': stderr}
                            )
                    else:
                        log_warning_with_context(
                            execution=execution,
                            message='远程Allure结果目录不存在，跳过报告生成',
                            context={'remote_result_dir': remote_result_dir, 'error': stderr}
                        )
                finally:
                    ssh_service.close()
            else:
                log_warning_with_context(
                    execution=execution,
                    message='无法连接到远程执行机，跳过报告生成',
                    context={'executor_ip': environment.executor_ip}
                )
        else:
            # 本地执行，直接使用本地Allure结果
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
                report = Report.objects.create(
                    execution=execution,
                    report_type='allure',
                    report_path=report_dir,
                    report_url=f'/api/automation/reports/{execution.id}/download/',  # 临时URL，稍后更新
                    summary={
                        'generated_at': datetime.now().isoformat(),
                        'report_path': report_dir
                    }
                )
                
                # 更新报告URL为正确的预览URL
                report.report_url = f'/api/automation/reports/{report.id}/preview/'
                report.save()
                
                Log.objects.create(
                    execution=execution,
                    level='INFO',
                    message=json.dumps({
                        'message': f'Allure报告生成成功（本地执行）',
                        'timestamp': datetime.now().isoformat(),
                        'level': 'INFO',
                        'context': {'report_dir': report_dir}
                    }, ensure_ascii=False)
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
