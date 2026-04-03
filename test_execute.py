#!/usr/bin/env python
"""
测试任务执行
"""
import os
import sys
import django
import time
import traceback

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django.settings')
django.setup()

from automation.models import AutomationTask, ExecutionHistory, Log
from automation.tasks import execute_automation_task
from django.contrib.auth import get_user_model

User = get_user_model()

def test_task_execution():
    """测试任务执行"""
    print("=" * 80)
    print("测试任务执行")
    print("=" * 80)
    
    try:
        # 获取第一个任务和第一个用户
        task = AutomationTask.objects.first()
        user = User.objects.first()
        
        if not task:
            print("没有找到任务，请先创建任务")
            return
        if not user:
            print("没有找到用户")
            return
            
        print(f"任务: {task.name} (ID: {task.id})")
        print(f"用户: {user.username} (ID: {user.id})")
        print(f"环境: {task.environment.name if task.environment else '无'}")
        if task.environment:
            print(f"执行机IP: {task.environment.executor_ip}")
            print(f"SSH端口: {task.environment.executor_port}")
            print(f"SSH用户名: {task.environment.executor_username}")
        
        # 检查之前的执行记录数量
        prev_count = ExecutionHistory.objects.count()
        print(f"执行前的执行记录数量: {prev_count}")
        
        # 同步执行任务
        print("\n开始同步执行任务...")
        start_time = time.time()
        
        try:
            # 直接调用任务函数（同步执行）
            execute_automation_task(task.id, user.id)
            print("任务执行调用完成")
        except Exception as e:
            print(f"任务执行异常: {str(e)}")
            traceback.print_exc()
        
        # 等待一下，让任务有时间执行
        time.sleep(3)
        
        # 检查执行记录
        new_count = ExecutionHistory.objects.count()
        print(f"执行后的执行记录数量: {new_count}")
        
        if new_count > prev_count:
            print(f"✓ 成功创建了 {new_count - prev_count} 条执行记录")
            # 获取最新的执行记录
            latest_execution = ExecutionHistory.objects.order_by('-created_at').first()
            print(f"最新执行记录:")
            print(f"  ID: {latest_execution.id}")
            print(f"  状态: {latest_execution.status}")
            print(f"  开始时间: {latest_execution.start_time}")
            print(f"  结束时间: {latest_execution.end_time}")
            print(f"  退出码: {latest_execution.exit_code}")
            
            # 获取相关日志
            logs = latest_execution.logs.all().order_by('timestamp')
            print(f"  日志数量: {logs.count()}")
            
            for log in logs[:10]:  # 最多显示10条日志
                print(f"    [{log.timestamp}] {log.level}: {log.message[:200]}...")
        else:
            print("✗ 没有创建新的执行记录")
            print("可能的原因:")
            print("1. 任务执行函数没有创建执行记录")
            print("2. 任务执行过程中发生了异常")
            print("3. 任务执行被跳过")
        
        elapsed_time = time.time() - start_time
        print(f"\n测试完成，耗时: {elapsed_time:.2f}秒")
        
    except Exception as e:
        print(f"测试过程中发生异常: {str(e)}")
        traceback.print_exc()

if __name__ == '__main__':
    test_task_execution()