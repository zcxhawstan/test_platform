import paramiko
import time
import json
import os
from .models import Environment


class SSHService:
    """SSH服务类，用于连接执行机"""
    
    def __init__(self, environment):
        self.environment = environment
        self.client = None
        self.max_retry = 3
        self.retry_delay = 5
    
    def connect(self, retry_count=0):
        """连接到执行机，支持自动重试"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.environment.executor_ip,
                port=self.environment.executor_port,
                username=self.environment.executor_username,
                password=self.environment.executor_password,
                timeout=30
            )
            return True
        except Exception as e:
            error_msg = f"SSH连接失败: {str(e)}"
            print(error_msg)
            if retry_count < self.max_retry:
                print(f"尝试重连 ({retry_count + 1}/{self.max_retry})...")
                time.sleep(self.retry_delay)
                return self.connect(retry_count + 1)
            return False
    
    def is_connected(self):
        """检查连接状态"""
        if not self.client:
            return False
        try:
            # 发送一个简单的命令来测试连接
            stdin, stdout, stderr = self.client.exec_command('echo ping')
            return True
        except Exception:
            return False
    
    def execute_command(self, command, retry_count=0):
        """在执行机上执行命令，支持自动重连"""
        # 检查连接状态
        if not self.client or not self.is_connected():
            if not self.connect():
                return False, "SSH连接失败", ""
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=60)
            stdout = stdout.read().decode('utf-8')
            stderr = stderr.read().decode('utf-8')
            return True, stdout, stderr
        except Exception as e:
            error_msg = f"执行命令失败: {str(e)}"
            print(error_msg)
            # 尝试重连
            if retry_count < self.max_retry:
                print(f"尝试重连并重新执行 ({retry_count + 1}/{self.max_retry})...")
                if self.connect():
                    return self.execute_command(command, retry_count + 1)
            return False, error_msg, ""
    
    def close(self):
        """关闭SSH连接"""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                print(f"关闭SSH连接失败: {str(e)}")
            finally:
                self.client = None


class DockerService:
    """Docker服务类，用于管理Docker容器"""
    
    def __init__(self, environment):
        self.environment = environment
        self.ssh_service = SSHService(environment)
    
    def ensure_docker_running(self):
        """确保Docker服务运行"""
        success, stdout, stderr = self.ssh_service.execute_command('systemctl status docker')
        if not success:
            return False, "无法检查Docker状态"
        
        if 'Active: active (running)' not in stdout:
            # 尝试启动Docker服务
            success, stdout, stderr = self.ssh_service.execute_command('sudo systemctl start docker')
            if not success:
                return False, "无法启动Docker服务"
            time.sleep(2)
        
        return True, "Docker服务运行正常"
    
    def get_available_port(self):
        """获取可用端口"""
        # 检查常用端口是否可用
        for port in range(8000, 9000):
            success, stdout, stderr = self.ssh_service.execute_command(f"netstat -tuln | grep :{port}")
            if not success or str(port) not in stdout:
                return port
        return 8000
    
    def create_container(self):
        """创建Docker容器"""
        # 确保Docker服务运行
        success, message = self.ensure_docker_running()
        if not success:
            return False, message
        
        # 生成容器名称
        container_name = f"automation-{self.environment.id}"
        
        # 检查容器是否已存在
        success, stdout, stderr = self.ssh_service.execute_command(f"docker ps -a | grep {container_name}")
        if success and container_name in stdout:
            # 删除已存在的容器
            self.ssh_service.execute_command(f"docker rm -f {container_name}")
            import time
            time.sleep(2)
        
        # 获取可用端口
        available_port = self.get_available_port()
        
        # 构建Docker run命令
        command = f"docker run -d --name {container_name}"
        
        # 自动添加端口映射（使用可用端口）
        command += f" -p {available_port}:8000"
        
        # 自动添加卷映射（代码仓库路径）
        command += " -v /opt/automation/repos:/opt/automation/repos"
        
        # 添加环境变量
        if self.environment.variables:
            for key, value in self.environment.variables.items():
                command += f" -e {key}={value}"
        
        # 添加镜像
        command += f" {self.environment.docker_image}"
        
        # 添加保持容器运行的命令
        command += " tail -f /dev/null"
        
        # 执行命令
        success, stdout, stderr = self.ssh_service.execute_command(command)
        if not success:
            return False, f"创建容器失败: {stderr}"
        
        # 检查容器是否创建成功并正在运行
        import time
        time.sleep(3)  # 等待容器启动
        success, stdout, stderr = self.ssh_service.execute_command(f"docker ps | grep {container_name}")
        if not success or container_name not in stdout:
            return False, f"容器创建后未运行: {stderr}"
        
        return True, f"容器 {container_name} 创建成功（映射端口: {available_port}）"
    
    def start_container(self):
        """启动Docker容器"""
        container_name = f"automation-{self.environment.id}"
        
        # 检查容器是否正在运行
        success, stdout, stderr = self.ssh_service.execute_command(f"docker ps | grep {container_name}")
        if success and container_name in stdout:
            return True, "容器已经在运行"
        
        # 检查容器是否存在（已停止）
        success, stdout, stderr = self.ssh_service.execute_command(f"docker ps -a | grep {container_name}")
        if not success or container_name not in stdout:
            # 容器不存在，创建容器
            return self.create_container()
        
        # 容器存在但已停止，删除后重新创建
        self.ssh_service.execute_command(f"docker rm -f {container_name}")
        import time
        time.sleep(2)
        return self.create_container()
    
    def execute_in_container(self, command):
        """在Docker容器中执行命令"""
        container_name = f"automation-{self.environment.id}"
        
        # 确保容器正在运行
        success, message = self.start_container()
        if not success:
            return False, message, ""
        
        # 首先安装pytest（如果尚未安装）
        install_cmd = f"docker exec {container_name} bash -c 'pip install pytest allure-pytest -q'"
        self.ssh_service.execute_command(install_cmd)
        
        # 在容器中执行命令（带重试机制）
        import time
        max_retries = 3
        retry_delay = 3
        
        for attempt in range(max_retries):
            docker_command = f"docker exec {container_name} bash -c '{command}; echo EXIT_CODE:$?'"
            success, stdout, stderr = self.ssh_service.execute_command(docker_command)
            
            # 检查是否是容器未运行的错误
            if not success and 'container' in stderr.lower() and 'not running' in stderr.lower():
                if attempt < max_retries - 1:
                    # 等待后重试
                    time.sleep(retry_delay)
                    # 尝试重新启动容器
                    restart_success, restart_msg = self.start_container()
                    if not restart_success:
                        return False, f"容器重启失败: {restart_msg}", stderr
                    continue
                else:
                    return False, "容器未运行，重试次数已用完", stderr
            
            if not success:
                return False, f"执行命令失败: {stderr}", ""
            
            # 成功执行，跳出重试循环
            break
        
        # 提取退出码
        exit_code = 0
        lines = stdout.split('\n')
        for line in reversed(lines):
            if line.startswith('EXIT_CODE:'):
                try:
                    exit_code = int(line.split(':')[1].strip())
                    # 移除退出码行
                    stdout = '\n'.join([l for l in lines if not l.startswith('EXIT_CODE:')])
                    break
                except ValueError:
                    pass
        
        # 如果退出码非零，返回失败
        if exit_code != 0:
            return False, stdout, stderr
        
        # 分析pytest输出，统计测试用例结果
        test_summary = self._parse_pytest_output(stdout, stderr)
        if test_summary['failed'] > 0:
            return False, stdout, stderr
        
        return True, stdout, stderr
    
    def _parse_pytest_output(self, stdout, stderr):
        """分析pytest输出，统计测试用例结果"""
        summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # 合并stdout和stderr进行分析
        output = stdout + '\n' + stderr
        lines = output.split('\n')
        
        # 查找pytest总结行
        for line in lines:
            line = line.strip()
            # 匹配pytest总结格式，例如："3 passed, 1 failed, 2 skipped in 1.23s"
            if 'passed' in line or 'failed' in line or 'skipped' in line:
                # 提取数字
                import re
                # 匹配数字和状态的组合
                matches = re.findall(r'(\d+)\s+(passed|failed|skipped)', line)
                for count, status in matches:
                    count = int(count)
                    if status == 'passed':
                        summary['passed'] = count
                    elif status == 'failed':
                        summary['failed'] = count
                    elif status == 'skipped':
                        summary['skipped'] = count
                # 计算总数
                summary['total'] = summary['passed'] + summary['failed'] + summary['skipped']
                break
        
        return summary
    
    def close(self):
        """关闭SSH连接"""
        self.ssh_service.close()


class GitService:
    """Git服务类，用于拉取代码"""
    
    def __init__(self, environment):
        self.environment = environment
        self.ssh_service = SSHService(environment)
    
    def get_repo_path(self, task):
        """获取代码仓库路径"""
        # 生成仓库目录名
        repo_name = task.git_repo.split('/')[-1].replace('.git', '')
        # 代码保存路径：/opt/automation/repos/{repo_name}
        repo_path = f"/opt/automation/repos/{repo_name}"
        return repo_path
    
    def clone_or_pull(self, task, retry_count=0):
        """克隆或拉取代码，支持失败重试"""
        repo_path = self.get_repo_path(task)
        max_retry = 3
        retry_delay = 5
        
        # 确保目录存在
        success, stdout, stderr = self.ssh_service.execute_command(f"mkdir -p /opt/automation/repos")
        if not success:
            return False, f"创建目录失败: {stderr}"
        
        # 检查仓库是否已存在
        success, stdout, stderr = self.ssh_service.execute_command(f"ls -la {repo_path}")
        
        if 'No such file or directory' in stderr:
            # 克隆仓库
            command = f"git clone {task.git_repo} {repo_path}"
            success, stdout, stderr = self.ssh_service.execute_command(command)
            if not success:
                if retry_count < max_retry:
                    print(f"克隆仓库失败，尝试重试 ({retry_count + 1}/{max_retry})...")
                    time.sleep(retry_delay)
                    return self.clone_or_pull(task, retry_count + 1)
                return False, f"克隆仓库失败: {stderr}"
        else:
            # 拉取最新代码
            command = f"cd {repo_path} && git pull origin {task.git_branch}"
            success, stdout, stderr = self.ssh_service.execute_command(command)
            if not success:
                if retry_count < max_retry:
                    print(f"拉取代码失败，尝试重试 ({retry_count + 1}/{max_retry})...")
                    time.sleep(retry_delay)
                    return self.clone_or_pull(task, retry_count + 1)
                return False, f"拉取代码失败: {stderr}"
        
        # 切换到指定分支
        command = f"cd {repo_path} && git checkout {task.git_branch}"
        success, stdout, stderr = self.ssh_service.execute_command(command)
        if not success:
            if retry_count < max_retry:
                print(f"切换分支失败，尝试重试 ({retry_count + 1}/{max_retry})...")
                time.sleep(retry_delay)
                return self.clone_or_pull(task, retry_count + 1)
            return False, f"切换分支失败: {stderr}"
        
        return True, repo_path
    
    def close(self):
        """关闭SSH连接"""
        self.ssh_service.close()


def execute_task_on_remote(task, environment):
    """在远程执行机上执行任务"""
    docker_service = DockerService(environment)
    
    try:
        # 确保Docker服务运行
        success, message = docker_service.ensure_docker_running()
        if not success:
            return False, message, ""
        
        # 启动容器
        success, message = docker_service.start_container()
        if not success:
            return False, message, ""
        
        # 如果是Git仓库，拉取代码
        script_path = task.script_path
        repo_path = None
        
        if task.script_source == 'git' and task.git_repo:
            git_service = GitService(environment)
            try:
                success, repo_path = git_service.clone_or_pull(task)
                if not success:
                    return False, repo_path, ""
                # 更新脚本路径为仓库中的路径（使用Linux路径分隔符）
                # 移除script_path开头的斜杠，然后与repo_path拼接
                script_path = repo_path.rstrip('/') + '/' + script_path.lstrip('/')
            finally:
                git_service.close()
        
        # 依赖管理：检查并安装依赖
        if not repo_path:
            repo_path = '.'
        requirements_path = f"{repo_path}/requirements.txt"
        
        # 检查requirements.txt文件是否存在
        container_name = f"automation-{environment.id}"
        check_requirements_cmd = f"docker exec {container_name} bash -c 'ls -la {requirements_path}'"
        success, stdout, stderr = docker_service.ssh_service.execute_command(check_requirements_cmd)
        
        if 'No such file or directory' not in stderr:
            print(f"发现依赖文件: {requirements_path}")
            # 安装依赖
            print("安装依赖包...")
            install_cmd = f"docker exec {container_name} bash -c 'cd {repo_path} && pip install -r requirements.txt'"
            success, _, install_stderr = docker_service.ssh_service.execute_command(install_cmd)
            if not success:
                error_msg = f"安装依赖失败: {install_stderr}"
                print(error_msg)
                # 即使依赖安装失败，也继续执行测试
                print("依赖安装失败，继续执行测试")
            else:
                print("依赖安装完成")
        else:
            print(f"未发现依赖文件: {requirements_path}")
        
        # 构建执行命令（平台内部处理）
        execution_command = f"cd {repo_path} && pytest {script_path} --alluredir=./result"
        
        # 在容器中执行命令
        success, stdout, stderr = docker_service.execute_in_container(execution_command)
        if not success:
            # 如果是执行失败，stdout 可能包含错误信息
            error_message = stdout if stdout else (stderr if stderr else '未知错误')
            return False, error_message, stderr
        
        # 收集Allure报告
        report_dir = f"{repo_path}/result"
        check_report_cmd = f"docker exec {container_name} bash -c 'ls -la {report_dir}'"
        docker_service.ssh_service.execute_command(check_report_cmd)
        
        # 返回执行结果和报告信息
        return True, stdout, stderr
    finally:
        docker_service.close()
