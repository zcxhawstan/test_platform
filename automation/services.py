import paramiko
import time
import json
import os
import functools
from .models import Environment


class SSHService:
    """SSH服务类，用于连接执行机"""
    
    def __init__(self, environment=None, host=None, port=None, username=None, password=None, execution=None):
        """
        初始化SSH服务
        支持两种方式：
        1. 传入 environment 对象（用于已保存的环境）
        2. 传入 host, port, username, password（用于新增环境时的测试）
        """
        self.client = None
        self.max_retry = 3
        self.retry_delay = 5
        self.execution = execution
        
        if environment is not None:
            # 方式1：使用环境对象
            self.environment = environment
            self._use_env_obj = True
        elif host and username and password:
            # 方式2：使用直接传入的参数
            self._host = host
            self._port = port or 22
            self._username = username
            self._password = password
            self._use_env_obj = False
        else:
            raise ValueError("必须提供 environment 对象或 host/username/password 参数")
    
    def _get_connection_params(self):
        """获取连接参数"""
        if self._use_env_obj:
            return {
                'hostname': self.environment.executor_ip,
                'port': self.environment.executor_port,
                'username': self.environment.executor_username,
                'password': self.environment.executor_password,
            }
        else:
            return {
                'hostname': self._host,
                'port': self._port,
                'username': self._username,
                'password': self._password,
            }
    
    def connect(self, retry_count=0):
        """连接到执行机，支持自动重试"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            params = self._get_connection_params()
            self.client.connect(
                hostname=params['hostname'],
                port=params['port'],
                username=params['username'],
                password=params['password'],
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
    
    def test_connection(self):
        """测试SSH连接，返回 (success, message)"""
        try:
            success = self.connect()
            if success:
                self.close()
                return True, "连接成功"
            else:
                return False, "无法建立SSH连接"
        except Exception as e:
            return False, str(e)
    
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
        # 记录命令执行开始
        print(f"[SSH] 开始执行命令: {command}")
        
        # 如果有execution对象，记录到数据库日志
        if self.execution:
            from .tasks import log_info_with_context
            log_info_with_context(
                execution=self.execution,
                message=f"开始执行SSH命令",
                context={'command': command, 'type': 'ssh_command'}
            )
        
        # 检查连接状态
        if not self.client or not self.is_connected():
            if not self.connect():
                # 记录失败日志
                if self.execution:
                    from .tasks import log_error_with_stack
                    log_error_with_stack(
                        execution=self.execution,
                        message=f"SSH命令执行失败",
                        exception=Exception("SSH连接失败"),
                        context={'command': command, 'error': "SSH连接失败", 'type': 'ssh_command'}
                    )
                print(f"[SSH] 命令执行失败")
                print(f"[SSH] 错误信息: SSH连接失败")
                return False, "SSH连接失败", ""
        
        try:
            # 为所有命令添加超时，防止卡住
            stdin, stdout, stderr = self.client.exec_command(command, timeout=120)
            stdout = stdout.read().decode('utf-8')
            stderr = stderr.read().decode('utf-8')
            
            # 记录成功日志
            print(f"[SSH] 命令执行成功")
            if stdout:
                print(f"[SSH] 标准输出: {stdout[:200]}..." if len(stdout) > 200 else f"[SSH] 标准输出: {stdout}")
            if stderr:
                print(f"[SSH] 标准错误: {stderr[:200]}..." if len(stderr) > 200 else f"[SSH] 标准错误: {stderr}")
            
            # 记录成功日志到数据库
            if self.execution:
                from .tasks import log_info_with_context
                log_info_with_context(
                    execution=self.execution,
                    message=f"SSH命令执行成功",
                    context={
                        'command': command,
                        'stdout': stdout[:300],
                        'stderr': stderr[:300],
                        'type': 'ssh_command'
                    }
                )
            
            return True, stdout, stderr
        except Exception as e:
            error_msg = f"执行命令失败: {str(e)}"
            print(f"[SSH] 命令执行失败")
            print(f"[SSH] 错误信息: {error_msg}")
            
            # 记录失败日志到数据库
            if self.execution:
                from .tasks import log_error_with_stack
                log_error_with_stack(
                    execution=self.execution,
                    message=f"SSH命令执行失败",
                    exception=e,
                    context={'command': command, 'error': error_msg, 'type': 'ssh_command'}
                )
            
            # 尝试重连
            if retry_count < self.max_retry:
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
    
    def __init__(self, environment, execution=None):
        self.environment = environment
        self.execution = execution
        self.ssh_service = SSHService(environment, execution=execution)
    
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
        
        # 确保卷目录存在
        self.ssh_service.execute_command("mkdir -p /opt/automation/repos")
        
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
        
        # 添加保持容器运行的命令（使用Python sleep，确保在Python镜像中可用）
        command += " python -c \"import time; time.sleep(999999)\""
        
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
            print(f"容器已在运行: {container_name}")
            return True, "容器已经在运行"
        
        # 检查容器是否存在（已停止）
        success, stdout, stderr = self.ssh_service.execute_command(f"docker ps -a | grep {container_name}")
        if not success or container_name not in stdout:
            # 容器不存在，创建容器
            print(f"容器不存在，创建容器: {container_name}")
            return self.create_container()
        
        # 容器存在但已停止，删除后重新创建
        print(f"容器存在但已停止，删除后重新创建: {container_name}")
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
    
    def __init__(self, environment, execution=None):
        self.environment = environment
        self.execution = execution
        self.ssh_service = SSHService(environment, execution=execution)
    
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
            command = f"git -c ssh.ConnectTimeout=30 clone {task.git_repo} {repo_path}"
            success, stdout, stderr = self.ssh_service.execute_command(command)
            if not success:
                if retry_count < max_retry:
                    print(f"克隆仓库失败，尝试重试 ({retry_count + 1}/{max_retry})...")
                    time.sleep(retry_delay)
                    return self.clone_or_pull(task, retry_count + 1)
                return False, f"克隆仓库失败: {stderr}"
        else:
            # 拉取最新代码
            command = f"cd {repo_path} && git -c ssh.ConnectTimeout=30 pull origin {task.git_branch}"
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


def execute_task_on_remote(task, environment, execution=None):
    """在远程执行机上执行任务"""
    docker_service = DockerService(environment, execution=execution)
    
    def log_info(message, context=None):
        """记录信息日志"""
        if execution:
            from .tasks import log_info_with_context
            log_info_with_context(execution, message, context)
        print(f"INFO: {message}")
    
    def log_error(message, exception=None, context=None):
        """记录错误日志"""
        if execution:
            from .tasks import log_error_with_stack
            log_error_with_stack(execution, message, exception, context)
        print(f"ERROR: {message}")
    
    def log_warning(message, context=None):
        """记录警告日志"""
        if execution:
            from .tasks import log_warning_with_context
            log_warning_with_context(execution, message, context)
        print(f"WARNING: {message}")
    
    try:
        # 确保Docker服务运行
        success, message = docker_service.ensure_docker_running()
        if not success:
            return False, message, ""
        
        # 启动容器
        success, message = docker_service.start_container()
        if not success:
            return False, message, ""
        log_info(f"容器启动成功: {message}", context={'container_message': message})
        
        # 检查容器状态
        container_name = f"automation-{environment.id}"
        check_container_cmd = f"docker ps | grep {container_name}"
        success, stdout, stderr = docker_service.ssh_service.execute_command(check_container_cmd)
        if success and container_name in stdout:
            log_info(f"容器正在运行: {stdout}", context={'container_name': container_name, 'status': 'running'})
        else:
            log_warning(f"容器可能未运行: {stderr}", context={'container_name': container_name, 'status': 'not_running'})
        
        # 检查容器内卷映射目录
        check_volume_cmd = f"docker exec {container_name} bash -c 'ls -la /opt/automation/repos'"
        success, stdout, stderr = docker_service.ssh_service.execute_command(check_volume_cmd)
        if success:
            log_info(f"容器内卷映射目录内容: {stdout}", context={'volume_path': '/opt/automation/repos', 'content': stdout[:200]})
        else:
            log_warning(f"容器内卷映射目录检查失败: {stderr}", context={'volume_path': '/opt/automation/repos', 'error': stderr})
        
        # 脚本路径信息
        script_path = task.script_path
        repo_path = None
        
        # 确保脚本路径使用Linux路径分隔符（处理Windows路径）
        if script_path:
            script_path = script_path.replace('\\', '/')
        
        log_info(f"任务脚本原始路径: {task.script_path}", context={'original_script_path': task.script_path})
        log_info(f"转换后脚本路径: {script_path}", context={'converted_script_path': script_path})
        log_info(f"任务脚本来源: {task.script_source}", context={'script_source': task.script_source})
        log_info(f"Git仓库: {task.git_repo if task.git_repo else 'N/A'}", context={'git_repo': task.git_repo})
        
        # 如果是Git仓库，拉取代码
        
        if task.git_repo and (not task.script_source or task.script_source == 'git'):
            git_service = GitService(environment, execution=execution)
            try:
                log_info(f"开始Git操作: 克隆或拉取代码", context={'git_repo': task.git_repo, 'git_branch': task.git_branch})
                success, repo_path = git_service.clone_or_pull(task)
                if not success:
                    log_error(f"Git操作失败: {repo_path}", context={'git_repo': task.git_repo, 'error': repo_path})
                    return False, repo_path, ""
                log_info(f"Git操作成功: {repo_path}", context={'repo_path': repo_path})
                
                # 更新脚本路径为仓库中的路径（使用Linux路径分隔符）
                # 如果script_path不是绝对路径，则与repo_path拼接
                if script_path.startswith('/'):
                    log_info(f"脚本路径已经是绝对路径: {script_path}", context={'script_path': script_path})
                    # 检查宿主机上文件是否存在
                    host_check_cmd = f"ls -la {script_path}"
                    success, host_stdout, host_stderr = docker_service.ssh_service.execute_command(host_check_cmd)
                    if not success or 'No such file or directory' in host_stderr:
                        log_warning(f"宿主机上脚本文件不存在: {script_path}", context={'script_path': script_path, 'error': host_stderr})
                    else:
                        log_info(f"宿主机上脚本文件存在: {host_stdout}", context={'script_path': script_path, 'file_info': host_stdout[:100]})
                else:
                    # 移除script_path开头的斜杠，然后与repo_path拼接
                    script_path = repo_path.rstrip('/') + '/' + script_path.lstrip('/')
                    log_info(f"Git仓库路径: {repo_path}", context={'repo_path': repo_path})
                    log_info(f"拼接后脚本路径: {script_path}", context={'script_path': script_path})
                    # 确保拼接后是绝对路径
                    if not script_path.startswith('/'):
                        script_path = '/' + script_path
                        log_info(f"修正为绝对路径: {script_path}", context={'script_path': script_path})
                    # 检查宿主机上文件是否存在
                    host_check_cmd = f"ls -la {script_path}"
                    success, host_stdout, host_stderr = docker_service.ssh_service.execute_command(host_check_cmd)
                    if not success or 'No such file or directory' in host_stderr:
                        log_warning(f"宿主机上脚本文件不存在: {script_path}", context={'script_path': script_path, 'error': host_stderr})
                    else:
                        log_info(f"宿主机上脚本文件存在: {host_stdout}", context={'script_path': script_path, 'file_info': host_stdout[:100]})
            finally:
                git_service.close()
        
        # 依赖管理：检查并安装依赖
        if not repo_path:
            repo_path = '.'
        requirements_path = f"{repo_path}/requirements.txt"
        
        # 对于非Git任务，确保script_path是绝对路径或正确处理
        if not task.script_source == 'git' and script_path:
            if not script_path.startswith('/'):
                # 对于非Git任务，保持相对路径，让pytest在当前工作目录中查找
                log_info(f"非Git任务，使用相对路径: {script_path}", context={'script_path': script_path, 'task_type': 'non_git'})
            else:
                log_info(f"非Git任务，使用绝对路径: {script_path}", context={'script_path': script_path, 'task_type': 'non_git'})
        
        # 检查脚本文件是否存在（在容器内检查）
        container_name = f"automation-{environment.id}"
        log_info(f"检查容器内脚本文件是否存在: {script_path}", context={'script_path': script_path, 'container_name': container_name})
        log_info(f"容器名称: {container_name}", context={'container_name': container_name})
        
        if script_path:
            # 在容器内检查文件是否存在
            check_script_cmd = f"docker exec {container_name} bash -c 'ls -la {script_path}'"
            success, stdout, stderr = docker_service.ssh_service.execute_command(check_script_cmd)
            if not success or 'No such file or directory' in stderr:
                error_msg = f"脚本文件在容器内不存在: {script_path}"
                log_error(error_msg, context={'script_path': script_path, 'container_name': container_name, 'error': stderr})
                log_error(f"容器检查错误详情: {stderr}", context={'container_name': container_name, 'error': stderr})
                
                # 检查容器内的卷映射目录
                log_info(f"检查容器内卷映射目录: /opt/automation/repos", context={'volume_path': '/opt/automation/repos'})
                check_volume_cmd = f"docker exec {container_name} bash -c 'ls -la /opt/automation/repos'"
                _, volume_stdout, volume_stderr = docker_service.ssh_service.execute_command(check_volume_cmd)
                log_info(f"容器内/opt/automation/repos目录内容: {volume_stdout}", context={'volume_path': '/opt/automation/repos', 'content': volume_stdout[:200]})
                
                # 如果是Git任务，列出仓库目录内容以帮助调试
                if task.script_source == 'git' and repo_path:
                    # 在容器内查找Python文件
                    list_repo_cmd = f"docker exec {container_name} bash -c 'find {repo_path} -type f -name \"*.py\" | head -20'"
                    _, list_stdout, _ = docker_service.ssh_service.execute_command(list_repo_cmd)
                    log_info(f"容器内仓库中的Python文件: {list_stdout}", context={'repo_path': repo_path, 'python_files': list_stdout[:200]})
                    # 列出脚本路径的父目录
                    import os
                    script_dir = os.path.dirname(script_path) if '/' in script_path else repo_path
                    list_dir_cmd = f"docker exec {container_name} bash -c 'ls -la {script_dir}'"
                    _, dir_stdout, _ = docker_service.ssh_service.execute_command(list_dir_cmd)
                    log_info(f"容器内脚本所在目录内容: {dir_stdout}", context={'script_dir': script_dir, 'content': dir_stdout[:200]})
                    
                    # 同时在宿主机上检查，对比结果
                    log_info(f"同时在宿主机上检查脚本路径: {script_path}", context={'script_path': script_path})
                    host_check_cmd = f"ls -la {script_path}"
                    _, host_stdout, host_stderr = docker_service.ssh_service.execute_command(host_check_cmd)
                    if 'No such file or directory' in host_stderr:
                        log_warning(f"宿主机上文件也不存在，可能是路径错误或代码未拉取", context={'script_path': script_path, 'error': host_stderr})
                    else:
                        log_warning(f"宿主机上文件存在，但容器内看不到，可能是卷映射问题", context={'script_path': script_path, 'host_file_info': host_stdout[:100]})
                        log_info(f"宿主机文件信息: {host_stdout}", context={'script_path': script_path, 'host_file_info': host_stdout[:100]})
                return False, error_msg, stderr
            else:
                log_info(f"容器内脚本文件存在: {stdout}", context={'script_path': script_path, 'file_info': stdout[:100]})
        else:
            log_warning("script_path为空", context={'script_path': script_path})
        
        # 检查requirements.txt文件是否存在
        check_requirements_cmd = f"docker exec {container_name} bash -c 'ls -la {requirements_path}'"
        success, stdout, stderr = docker_service.ssh_service.execute_command(check_requirements_cmd)
        
        if 'No such file or directory' not in stderr:
            log_info(f"发现依赖文件: {requirements_path}", context={'requirements_path': requirements_path})
            
            # 检查依赖是否需要更新（基于文件哈希）
            hash_file_path = f"{repo_path}/.last_install_hash"
            
            # 计算当前requirements.txt的MD5哈希
            calc_hash_cmd = f"docker exec {container_name} bash -c 'md5sum {requirements_path} 2>/dev/null || md5 {requirements_path} 2>/dev/null || echo \"no_hash\"'"
            success, hash_out, hash_err = docker_service.ssh_service.execute_command(calc_hash_cmd)
            current_hash = hash_out.split()[0] if success and hash_out.strip() and 'no_hash' not in hash_out else "unknown"
            
            # 读取上次安装的哈希值
            read_hash_cmd = f"docker exec {container_name} bash -c 'cat {hash_file_path} 2>/dev/null || echo \"\"'"
            success, last_hash_out, last_hash_err = docker_service.ssh_service.execute_command(read_hash_cmd)
            last_hash = last_hash_out.strip() if success else ""
            
            log_info(f"依赖文件哈希检查 - 当前: {current_hash}, 上次: {last_hash}", context={'current_hash': current_hash, 'last_hash': last_hash, 'requirements_path': requirements_path})
            
            # 如果哈希不同或未知，安装依赖
            if current_hash != "unknown" and current_hash != last_hash:
                log_info("依赖文件有更新，开始安装依赖包...", context={'requirements_path': requirements_path})
                install_cmd = f"docker exec {container_name} bash -c 'cd {repo_path} && pip install -r requirements.txt'"
                success, install_stdout, install_stderr = docker_service.ssh_service.execute_command(install_cmd)
                if not success:
                    error_msg = f"安装依赖失败: {install_stderr}"
                    log_error(error_msg, context={'requirements_path': requirements_path, 'error': install_stderr})
                    # 即使依赖安装失败，也继续执行测试
                    log_warning("依赖安装失败，继续执行测试", context={'requirements_path': requirements_path})
                else:
                    log_info("依赖安装完成", context={'requirements_path': requirements_path, 'output': install_stdout[:300]})
                    # 保存安装哈希
                    if current_hash != "unknown":
                        save_hash_cmd = f"docker exec {container_name} bash -c 'echo \"{current_hash}\" > {hash_file_path}'"
                        docker_service.ssh_service.execute_command(save_hash_cmd)
                        log_info(f"已保存依赖安装哈希: {current_hash}", context={'hash_file': hash_file_path, 'hash': current_hash})
                    if install_stdout:
                        print(f"[依赖安装] 输出: {install_stdout[:300]}..." if len(install_stdout) > 300 else f"[依赖安装] 输出: {install_stdout}")
            else:
                if current_hash == "unknown":
                    log_warning("无法计算依赖文件哈希，跳过依赖检查", context={'requirements_path': requirements_path})
                    # 未知哈希时仍然安装依赖以确保环境一致
                    log_info("开始安装依赖包（哈希未知）...", context={'requirements_path': requirements_path})
                    install_cmd = f"docker exec {container_name} bash -c 'cd {repo_path} && pip install -r requirements.txt'"
                    success, install_stdout, install_stderr = docker_service.ssh_service.execute_command(install_cmd)
                    if not success:
                        error_msg = f"安装依赖失败: {install_stderr}"
                        log_error(error_msg, context={'requirements_path': requirements_path, 'error': install_stderr})
                        log_warning("依赖安装失败，继续执行测试", context={'requirements_path': requirements_path})
                    else:
                        log_info("依赖安装完成", context={'requirements_path': requirements_path, 'output': install_stdout[:300]})
                else:
                    log_info("依赖文件无更新，跳过安装", context={'requirements_path': requirements_path, 'hash': current_hash})
        else:
            log_info(f"未发现依赖文件: {requirements_path}", context={'requirements_path': requirements_path})
        
        # 创建core模块以解决导入错误
        # 构建命令时避免在f-string中使用反斜杠
        core_dir = f"{repo_path}/core"
        logger_py = f"{core_dir}/logger.py"
        command_executor_py = f"{core_dir}/command_executor.py"
        
        # 构建logger.py内容
        logger_content = "import logging\nlogger = logging.getLogger(__name__)"
        
        # 构建command_executor.py内容
        executor_content = """import logging
logger = logging.getLogger(__name__)

class CommandExecutor:
    def connect(self):
        logger.info("Connected to executor")
    def disconnect(self):
        logger.info("Disconnected from executor")
    def run(self, command):
        logger.info(f"Running command: {command}")
        # 返回模拟结果
        return {"code": 0, "stdout": "test", "stderr": ""}
"""
        
        # 构建完整的命令
        # 分开执行命令，避免here-document的语法问题
        create_core_dir_cmd = f"docker exec {container_name} bash -c 'mkdir -p {core_dir}'"
        
        # 使用echo命令的不同格式来避免引号冲突
        create_logger_cmd = f"docker exec {container_name} bash -c 'cat > {logger_py} << EOF\n{logger_content}\nEOF'"
        create_executor_cmd = f"docker exec {container_name} bash -c 'cat > {command_executor_py} << EOF\n{executor_content}\nEOF'"
        
        # 执行命令
        success, create_stdout, create_stderr = docker_service.ssh_service.execute_command(create_core_dir_cmd)
        if success:
            success, create_stdout, create_stderr = docker_service.ssh_service.execute_command(create_logger_cmd)
            if success:
                success, create_stdout, create_stderr = docker_service.ssh_service.execute_command(create_executor_cmd)
        if success:
            log_info("创建core模块成功", context={'repo_path': repo_path})
        else:
            log_warning("创建core模块失败", context={'repo_path': repo_path, 'error': create_stderr})
        
        # 构建执行命令（平台内部处理）
        log_info(f"最终repo_path: {repo_path}", context={'repo_path': repo_path})
        log_info(f"最终script_path: {script_path}", context={'script_path': script_path})
        
        # 调试：检查容器内当前目录和文件
        debug_cmd1 = f"docker exec {container_name} bash -c 'pwd && ls -la'"
        success, debug_out1, debug_err1 = docker_service.ssh_service.execute_command(debug_cmd1)
        log_info(f"容器内当前目录: {debug_out1}", context={'container_name': container_name, 'current_dir': debug_out1[:100]})
        
        debug_cmd2 = f"docker exec {container_name} bash -c 'ls -la {script_path}'"
        success, debug_out2, debug_err2 = docker_service.ssh_service.execute_command(debug_cmd2)
        if success:
            log_info(f"脚本文件存在: {debug_out2}", context={'script_path': script_path, 'file_info': debug_out2[:100]})
        else:
            log_error(f"脚本文件不存在: {debug_err2}", context={'script_path': script_path, 'error': debug_err2})
            
        debug_cmd3 = f"docker exec {container_name} bash -c 'find {repo_path} -name \"*.py\" | head -5'"
        success, debug_out3, debug_err3 = docker_service.ssh_service.execute_command(debug_cmd3)
        if success:
            log_info(f"仓库内Python文件: {debug_out3}", context={'repo_path': repo_path, 'python_files': debug_out3[:200]})
        
        # 确保pytest从仓库根目录执行
        # 直接在仓库根目录执行pytest，确保工作目录正确
        # 使用相对路径，确保pytest能正确找到测试文件
        # 计算相对路径
        if script_path.startswith('/'):
            # 绝对路径，计算相对于repo_path的路径
            if script_path.startswith(repo_path):
                relative_script_path = script_path[len(repo_path):].lstrip('/')
            else:
                # 使用os.path.relpath作为备选
                relative_script_path = os.path.relpath(script_path, repo_path)
        else:
            # 已经是相对路径
            relative_script_path = script_path
        
        log_info(f"相对脚本路径: {relative_script_path}", context={'relative_script_path': relative_script_path})
        
        # 调试：检查pytest.ini文件
        debug_pytest_ini_cmd = f"docker exec {container_name} bash -c 'find {repo_path} -name pytest.ini -type f 2>/dev/null | head -5'"
        success, debug_out, debug_err = docker_service.ssh_service.execute_command(debug_pytest_ini_cmd)
        if success and debug_out.strip():
            log_info(f"找到pytest.ini文件: {debug_out}", context={'pytest_ini_files': debug_out})
            # 读取每个pytest.ini文件的内容
            for file_path in debug_out.strip().split('\n'):
                if file_path.strip():
                    read_cmd = f"docker exec {container_name} bash -c 'cat {file_path.strip()}'"
                    success, content, err = docker_service.ssh_service.execute_command(read_cmd)
                    if success:
                        log_info(f"pytest.ini文件内容 ({file_path}): {content[:500]}", context={'pytest_ini_path': file_path, 'content_preview': content[:500]})
                    else:
                        log_warning(f"无法读取pytest.ini文件: {file_path}", context={'pytest_ini_path': file_path, 'error': err})
        else:
            log_info("未找到pytest.ini文件", context={'repo_path': repo_path})
        
        # 确保在仓库根目录创建pytest.ini文件，设置正确的rootdir
        pytest_ini_path = f"{repo_path}/pytest.ini"
        create_pytest_ini_cmd = f"docker exec {container_name} bash -c 'printf \"[pytest]\\nrootdir = .\" > {pytest_ini_path}'"
        success, create_out, create_err = docker_service.ssh_service.execute_command(create_pytest_ini_cmd)
        if success:
            log_info(f"已创建pytest.ini文件: {pytest_ini_path}", context={'pytest_ini_path': pytest_ini_path})
        else:
            log_warning(f"创建pytest.ini文件失败: {create_err}", context={'pytest_ini_path': pytest_ini_path, 'error': create_err})
        
        # 清理可能干扰的pytest配置和缓存
        # 1. 查找并删除test_cases目录中的pytest.ini文件（如果存在）
        test_cases_pytest_ini = f"{repo_path}/test_cases/pytest.ini"
        remove_test_cases_ini_cmd = f"docker exec {container_name} bash -c 'rm -f {test_cases_pytest_ini}'"
        success, remove_out, remove_err = docker_service.ssh_service.execute_command(remove_test_cases_ini_cmd)
        if success:
            log_info(f"已清理test_cases目录中的pytest.ini文件", context={'pytest_ini_path': test_cases_pytest_ini})
        else:
            log_info(f"test_cases目录中无pytest.ini文件或清理失败: {remove_err}", context={'pytest_ini_path': test_cases_pytest_ini, 'error': remove_err})
        
        # 2. 清理pytest缓存
        clean_cache_cmd = f"docker exec {container_name} bash -c 'cd {repo_path} && rm -rf .pytest_cache'"
        docker_service.ssh_service.execute_command(clean_cache_cmd)
        log_info("已清理pytest缓存", context={'repo_path': repo_path})
        
        # 3. 验证我们创建的pytest.ini文件
        verify_ini_cmd = f"docker exec {container_name} bash -c 'cat {pytest_ini_path}'"
        success, verify_out, verify_err = docker_service.ssh_service.execute_command(verify_ini_cmd)
        if success:
            log_info(f"验证pytest.ini文件内容: {verify_out}", context={'pytest_ini_path': pytest_ini_path, 'content': verify_out})
        else:
            log_warning(f"无法验证pytest.ini文件: {verify_err}", context={'pytest_ini_path': pytest_ini_path, 'error': verify_err})
        
        # 构建详细的执行命令，添加-v选项获取更详细的输出
        execution_command = f"cd {repo_path} && export PYTHONPATH={repo_path} && python -m pytest {relative_script_path} --alluredir=./result --clean-alluredir --rootdir={repo_path} --override-ini=rootdir={repo_path} -v"
        
        # 添加调试信息：直接尝试导入测试文件
        log_info("开始执行调试导入命令", context={'repo_path': repo_path})
        debug_import_cmd = f"cd {repo_path} && export PYTHONPATH={repo_path} && python -c \"import sys, os; print('Python path:', sys.path); print('Current directory:', os.getcwd()); import importlib, traceback; print('Attempting to import test file...'); try: importlib.import_module('test_cases.system_test.test_home_file'); print('Import successful!'); except Exception as e: print('Import error:', str(e)); traceback.print_exc()\""
        log_info(f"调试导入命令: {debug_import_cmd}", context={'debug_import_cmd': debug_import_cmd})
        
        # 执行调试导入命令
        log_info("执行调试导入命令", context={'container_name': container_name})
        success, import_stdout, import_stderr = docker_service.ssh_service.execute_command(f"docker exec {container_name} bash -c '{debug_import_cmd}'")
        
        if success:
            log_info(f"调试导入成功: {import_stdout}", context={'import_stdout': import_stdout})
        else:
            log_error(f"调试导入失败: {import_stderr}", context={'import_stderr': import_stderr, 'import_stdout': import_stdout})
        
        # 额外的调试：检查test_cases目录结构
        log_info("检查test_cases目录结构", context={'repo_path': repo_path})
        check_dir_cmd = f"docker exec {container_name} bash -c 'ls -la {repo_path}/test_cases'"
        success, dir_stdout, dir_stderr = docker_service.ssh_service.execute_command(check_dir_cmd)
        if success:
            log_info(f"test_cases目录结构: {dir_stdout}", context={'dir_stdout': dir_stdout})
        else:
            log_error(f"检查test_cases目录失败: {dir_stderr}", context={'dir_stderr': dir_stderr})
        
        # 检查test_cases目录是否有__init__.py文件
        log_info("检查test_cases目录是否有__init__.py文件", context={'repo_path': repo_path})
        check_init_cmd = f"docker exec {container_name} bash -c 'ls -la {repo_path}/test_cases/__init__.py 2>/dev/null || echo \"No __init__.py file\"'"
        success, init_stdout, init_stderr = docker_service.ssh_service.execute_command(check_init_cmd)
        if success:
            log_info(f"test_cases目录__init__.py文件检查: {init_stdout}", context={'init_stdout': init_stdout})
        else:
            log_error(f"检查test_cases目录__init__.py文件失败: {init_stderr}", context={'init_stderr': init_stderr})
        
        # 检查system_test目录结构
        log_info("检查system_test目录结构", context={'repo_path': repo_path})
        check_system_test_cmd = f"docker exec {container_name} bash -c 'ls -la {repo_path}/test_cases/system_test'"
        success, system_test_stdout, system_test_stderr = docker_service.ssh_service.execute_command(check_system_test_cmd)
        if success:
            log_info(f"system_test目录结构: {system_test_stdout}", context={'system_test_stdout': system_test_stdout})
        else:
            log_error(f"检查system_test目录失败: {system_test_stderr}", context={'system_test_stderr': system_test_stderr})
        
        # 检查system_test目录是否有__init__.py文件
        log_info("检查system_test目录是否有__init__.py文件", context={'repo_path': repo_path})
        check_system_test_init_cmd = f"docker exec {container_name} bash -c 'ls -la {repo_path}/test_cases/system_test/__init__.py 2>/dev/null || echo \"No __init__.py file\"'"
        success, system_test_init_stdout, system_test_init_stderr = docker_service.ssh_service.execute_command(check_system_test_init_cmd)
        if success:
            log_info(f"system_test目录__init__.py文件检查: {system_test_init_stdout}", context={'system_test_init_stdout': system_test_init_stdout})
        else:
            log_error(f"检查system_test目录__init__.py文件失败: {system_test_init_stderr}", context={'system_test_init_stderr': system_test_stderr})
        
        # 检查test_home_file.py文件内容
        log_info("检查test_home_file.py文件内容", context={'repo_path': repo_path})
        check_file_cmd = f"docker exec {container_name} bash -c 'cat {repo_path}/test_cases/system_test/test_home_file.py'"
        success, file_stdout, file_stderr = docker_service.ssh_service.execute_command(check_file_cmd)
        if success:
            log_info(f"test_home_file.py文件内容: {file_stdout[:500]}", context={'file_stdout': file_stdout[:500]})
        else:
            log_error(f"检查test_home_file.py文件失败: {file_stderr}", context={'file_stderr': file_stderr})
        
        # 直接在容器中执行调试命令，获取详细的导入错误信息
        log_info("执行调试导入命令", context={'repo_path': repo_path})
        # 使用简单的命令来测试导入
        debug_cmd = f'docker exec {container_name} bash -c "cd {repo_path} && export PYTHONPATH={repo_path} && python -c \"import sys, os, importlib, traceback; print(\\\"Python path:\\\\", sys.path); print(\\\"Current directory:\\\\", os.getcwd()); print(\\\"Attempting to import test file...\\\"); try: importlib.import_module(\\\"test_cases.system_test.test_home_file\\\"); print(\\\"Import successful!\\\"); except Exception as e: print(\\\"Import error:\\\\", str(e)); traceback.print_exc()\""'
        # 执行调试命令
        success, debug_stdout, debug_stderr = docker_service.ssh_service.execute_command(debug_cmd)
        if success:
            log_info(f"调试导入命令执行成功: {debug_stdout}", context={'debug_stdout': debug_stdout})
        else:
            log_error(f"调试导入命令执行失败: {debug_stderr}", context={'debug_stderr': debug_stderr, 'debug_stdout': debug_stdout})
        
        log_info(f"执行命令: {execution_command}", context={'execution_command': execution_command})
        
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