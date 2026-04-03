#!/usr/bin/env python
"""
检查最新的执行历史和日志
"""
import os
import sys
import django
import json
from datetime import datetime

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')
django.setup()

from automation.models import ExecutionHistory, Log, AutomationTask
from django.contrib.auth.models import User

def check_latest_executions():
    """检查最新的执行历史"""
    print("=" * 80)
    print("最新的执行历史记录（按创建时间倒序，最多10条）")
    print("=" * 80)
    
    executions = ExecutionHistory.objects.all().order_by('-created_at')[:10]
    
    if not executions:
        print("没有找到执行历史记录")
        return
    
    for i, execution in enumerate(executions, 1):
        print(f"\n[{i}] 执行ID: {execution.id}")
        print(f"   任务: {execution.task.name}")
        print(f"   状态: {execution.status}")
        print(f"   执行人: {execution.executor.username}")
        print(f"   开始时间: {execution.start_time}")
        print(f"   结束时间: {execution.end_time}")
        print(f"   持续时间: {execution.duration}秒")
        print(f"   退出码: {execution.exit_code}")
        print(f"   创建时间: {execution.created_at}")
        
        # 获取关联的日志
        logs = execution.logs.all().order_by('timestamp')
        print(f"   日志数量: {logs.count()}")
        
        # 显示最新的几条日志
        recent_logs = logs[:5]
        for log in recent_logs:
            try:
                # 尝试解析JSON格式的日志
                log_data = json.loads(log.message)
                print(f"     [{log.timestamp}] {log.level}: {log_data.get('message', '无消息')}")
                if 'exception' in log_data:
                    exc = log_data['exception']
                    print(f"        异常: {exc.get('type')} - {exc.get('message')}")
            except json.JSONDecodeError:
                # 如果不是JSON格式，直接显示
                print(f"     [{log.timestamp}] {log.level}: {log.message[:200]}...")
        
        print("-" * 60)
    
    return executions

def check_celery_status():
    """检查Celery相关状态"""
    print("\n" + "=" * 80)
    print("Celery任务状态检查")
    print("=" * 80)
    
    # 检查是否有正在运行或失败的任务
    running_tasks = ExecutionHistory.objects.filter(status='running')
    failed_tasks = ExecutionHistory.objects.filter(status__in=['failed', 'error'])
    
    print(f"正在运行的任务数量: {running_tasks.count()}")
    print(f"失败的任务数量: {failed_tasks.count()}")
    
    if failed_tasks.exists():
        print("\n最近失败的任务:")
        for task in failed_tasks.order_by('-created_at')[:5]:
            print(f"  - {task.task.name} (ID: {task.id}) - 创建时间: {task.created_at}")
    
    # 检查任务的exit_code
    error_exit_codes = ExecutionHistory.objects.filter(exit_code__isnull=False).exclude(exit_code=0)
    if error_exit_codes.exists():
        print(f"\n有非零退出码的任务数量: {error_exit_codes.count()}")
        for exec in error_exit_codes.order_by('-created_at')[:3]:
            print(f"  - 任务: {exec.task.name}, 退出码: {exec.exit_code}")

def check_structured_logs():
    """检查结构化日志内容"""
    print("\n" + "=" * 80)
    print("结构化日志详情检查")
    print("=" * 80)
    
    # 获取最新的ERROR级别日志
    error_logs = Log.objects.filter(level='ERROR').order_by('-timestamp')[:10]
    
    if not error_logs:
        print("没有找到ERROR级别的日志")
        return
    
    print(f"找到 {error_logs.count()} 条ERROR日志:")
    
    for i, log in enumerate(error_logs, 1):
        print(f"\n[{i}] 执行ID: {log.execution.id}, 时间: {log.timestamp}")
        
        try:
            log_data = json.loads(log.message)
            print(f"   消息: {log_data.get('message', '无消息')}")
            
            if 'exception' in log_data:
                exc = log_data['exception']
                print(f"   异常类型: {exc.get('type')}")
                print(f"   异常消息: {exc.get('message')}")
                print(f"   堆栈跟踪: {exc.get('traceback', '无堆栈')[:500]}...")
            
            if 'context' in log_data:
                context = log_data['context']
                print(f"   上下文信息:")
                for key, value in context.items():
                    print(f"     {key}: {value}")
        except json.JSONDecodeError:
            print(f"   原始日志: {log.message[:500]}...")

if __name__ == '__main__':
    print(f"当前时间: {datetime.now()}")
    print(f"Python路径: {sys.executable}")
    
    executions = check_latest_executions()
    check_celery_status()
    check_structured_logs()
    
    if executions:
        latest_execution = executions[0]
        print(f"\n最新执行的ID: {latest_execution.id}")
        print(f"最新执行的状态: {latest_execution.status}")
        
        # 如果有失败的任务，提供诊断建议
        if latest_execution.status in ['failed', 'error']:
            print("\n⚠️  最新执行失败，建议检查以下问题:")
            print("1. Celery worker是否正在运行?")
            print("2. SSH连接配置是否正确?")
            print("3. 环境配置是否有误?")
            print("4. 查看上面的结构化日志详情")
    else:
        print("\n没有找到执行历史，可能的原因:")
        print("1. 从未执行过任务")
        print("2. 任务执行请求未到达后端")
        print("3. Celery未运行导致异步任务未执行")
    
    print("\n检查完成!")