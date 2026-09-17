"""
自动化执行服务。

四对象职责：
- SSHService：远程执行机连接与命令执行
- DockerService：容器生命周期与容器内命令执行
- GitService：测试仓库克隆/拉取/切分支
- TaskExecutor：任务编排（拉代码→起容器→装依赖→跑pytest）

所有拼入远程shell的变量一律经 shlex.quote 包裹；
输入侧白名单校验见 automation/serializers.py。
"""

import logging
import os
import shlex
import time

import paramiko

from .models import Environment

logger = logging.getLogger(__name__)

# 远程执行机的代码仓库根目录（宿主机与容器通过卷映射共享）
REPOS_ROOT = '/opt/automation/repos'


class SSHService:
    """SSH服务类，用于连接执行机"""

    def __init__(self, environment=None, host=None, port=None, username=None, password=None, execution=None):
        """
        初始化SSH服务，支持两种方式：
        1. 传入 environment 对象（用于已保存的环境，密码自动解密）
        2. 传入 host, port, username, password（用于新增环境时的测试）
        """
        self.client = None
        self.max_retry = 3
        self.retry_delay = 5
        self.execution = execution

        if environment is not None:
            self.environment = environment
            self._use_env_obj = True
        elif host and username and password:
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
                'password': self.environment.get_executor_password(),
            }
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
            logger.error('SSH连接失败: %s', e)
            if retry_count < self.max_retry:
                logger.info('尝试重连 (%d/%d)...', retry_count + 1, self.max_retry)
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
            return False, "无法建立SSH连接"
        except Exception as e:
            return False, str(e)

    def is_connected(self):
        """检查连接状态"""
        if not self.client:
            return False
        try:
            self.client.exec_command('echo ping')
            return True
        except Exception:
            return False

    def execute_command(self, command, retry_count=0):
        """在执行机上执行命令，支持自动重连"""
        logger.debug('[SSH] 执行命令: %s', command)

        if self.execution:
            from .tasks import log_info_with_context
            log_info_with_context(
                execution=self.execution,
                message='开始执行SSH命令',
                context={'command': command, 'type': 'ssh_command'}
            )

        if not self.client or not self.is_connected():
            if not self.connect():
                if self.execution:
                    from .tasks import log_error_with_stack
                    log_error_with_stack(
                        execution=self.execution,
                        message='SSH命令执行失败',
                        exception=Exception("SSH连接失败"),
                        context={'error': "SSH连接失败", 'type': 'ssh_command'}
                    )
                logger.error('[SSH] 命令执行失败: SSH连接失败')
                return False, "SSH连接失败", ""

        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=120)
            stdout = stdout.read().decode('utf-8')
            stderr = stderr.read().decode('utf-8')

            logger.debug('[SSH] 命令执行成功 stdout=%s...', stdout[:200])

            if self.execution:
                from .tasks import log_info_with_context
                log_info_with_context(
                    execution=self.execution,
                    message='SSH命令执行成功',
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
            logger.error('[SSH] 命令执行失败: %s', error_msg)

            if self.execution:
                from .tasks import log_error_with_stack
                log_error_with_stack(
                    execution=self.execution,
                    message='SSH命令执行失败',
                    exception=e,
                    context={'command': command, 'error': error_msg, 'type': 'ssh_command'}
                )

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
                logger.warning('关闭SSH连接失败: %s', e)
            finally:
                self.client = None


class DockerService:
    """Docker服务类，用于管理Docker容器"""

    def __init__(self, environment, execution=None):
        self.environment = environment
        self.execution = execution
        self.ssh_service = SSHService(environment, execution=execution)

    @property
    def container_name(self):
        return f"automation-{self.environment.id}"

    def ensure_docker_running(self):
        """确保Docker服务运行"""
        success, stdout, stderr = self.ssh_service.execute_command('systemctl status docker')
        if not success:
            return False, "无法检查Docker状态"

        if 'Active: active (running)' not in stdout:
            success, stdout, stderr = self.ssh_service.execute_command('sudo systemctl start docker')
            if not success:
                return False, "无法启动Docker服务"
            time.sleep(2)

        return True, "Docker服务运行正常"

    def get_available_port(self):
        """获取可用端口"""
        for port in range(8000, 9000):
            success, stdout, stderr = self.ssh_service.execute_command(f"netstat -tuln | grep :{port}")
            if not success or str(port) not in stdout:
                return port
        return 8000

    def create_container(self):
        """创建Docker容器"""
        success, message = self.ensure_docker_running()
        if not success:
            return False, message

        container_name = self.container_name

        # 容器已存在则删除重建（保证环境干净）
        success, stdout, stderr = self.ssh_service.execute_command(f"docker ps -a | grep {shlex.quote(container_name)}")
        if success and container_name in stdout:
            self.ssh_service.execute_command(f"docker rm -f {shlex.quote(container_name)}")
            time.sleep(2)

        available_port = self.get_available_port()
        self.ssh_service.execute_command(f"mkdir -p {shlex.quote(REPOS_ROOT)}")

        command = f"docker run -d --name {shlex.quote(container_name)}"
        command += f" -p {available_port}:8000"
        command += f" -v {shlex.quote(REPOS_ROOT)}:{shlex.quote(REPOS_ROOT)}"
        # 环境变量值已过serializer白名单校验，此处仍做quote防御
        if self.environment.variables:
            for key, value in self.environment.variables.items():
                command += f" -e {shlex.quote(f'{key}={value}')}"
        command += f" {shlex.quote(self.environment.docker_image)}"
        command += " python -c \"import time; time.sleep(999999)\""

        success, stdout, stderr = self.ssh_service.execute_command(command)
        if not success:
            return False, f"创建容器失败: {stderr}"

        logger.info('容器创建成功: %s', container_name)
        return True, container_name

    def start_container(self):
        """启动Docker容器（不存在则创建，已停止则重建）"""
        container_name = self.container_name

        success, stdout, stderr = self.ssh_service.execute_command(f"docker ps | grep {shlex.quote(container_name)}")
        if success and container_name in stdout:
            return True, "容器已经在运行"

        success, stdout, stderr = self.ssh_service.execute_command(f"docker ps -a | grep {shlex.quote(container_name)}")
        if not success or container_name not in stdout:
            return self.create_container()

        self.ssh_service.execute_command(f"docker rm -f {shlex.quote(container_name)}")
        time.sleep(2)
        return self.create_container()

    def exec_in_container(self, inner_command):
        """在容器内用bash执行命令（inner_command为完整shell语句），返回 (success, stdout, stderr)"""
        docker_command = (
            f"docker exec {shlex.quote(self.container_name)} "
            f"bash -c {shlex.quote(inner_command)}"
        )
        return self.ssh_service.execute_command(docker_command)

    def execute_in_container(self, command):
        """在容器内执行命令，解析尾部EXIT_CODE标记作为退出码"""
        success, message = self.start_container()
        if not success:
            return False, message, ""

        # 确保pytest可用（幂等，已安装时很快返回）
        self.ssh_service.execute_command(
            f"docker exec {shlex.quote(self.container_name)} bash -c 'pip install pytest allure-pytest -q'"
        )

        max_retries = 3
        retry_delay = 3

        for attempt in range(max_retries):
            success, stdout, stderr = self.exec_in_container(command + '; echo EXIT_CODE:$?')

            # 容器未运行时等待重试（可能是执行中被外部停止）
            if not success and 'container' in stderr.lower() and 'not running' in stderr.lower():
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    restart_success, restart_msg = self.start_container()
                    if not restart_success:
                        return False, f"容器重启失败: {restart_msg}", stderr
                    continue
                return False, "容器未运行，重试次数已用完", stderr

            if not success:
                return False, f"执行命令失败: {stderr}", ""

            break

        # 从输出末尾提取退出码标记
        exit_code = 0
        lines = stdout.split('\n')
        for line in reversed(lines):
            if line.startswith('EXIT_CODE:'):
                try:
                    exit_code = int(line.split(':')[1].strip())
                    stdout = '\n'.join([l for l in lines if not l.startswith('EXIT_CODE:')])
                except ValueError:
                    pass
                break

        if exit_code != 0:
            return False, stdout, stderr

        # pytest统计行里有failed则视为失败
        if self._parse_pytest_summary(stdout, stderr).get('failed', 0) > 0:
            return False, stdout, stderr

        return True, stdout, stderr

    @staticmethod
    def _parse_pytest_summary(stdout, stderr):
        """从pytest输出统计行解析用例结果计数"""
        summary = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
        import re
        for line in (stdout + '\n' + stderr).split('\n'):
            if 'passed' in line or 'failed' in line or 'skipped' in line:
                matches = re.findall(r'(\d+)\s+(passed|failed|skipped)', line)
                for count, status in matches:
                    summary[status] = int(count)
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

    @staticmethod
    def get_repo_path(task):
        """获取代码仓库路径：{REPOS_ROOT}/{仓库名}"""
        repo_name = task.git_repo.split('/')[-1].replace('.git', '')
        return f"{REPOS_ROOT}/{repo_name}"

    def clone_or_pull(self, task, retry_count=0):
        """克隆或拉取代码并切到指定分支，支持失败重试，返回 (success, repo_path|错误信息)"""
        repo_path = self.get_repo_path(task)
        max_retry = 3
        retry_delay = 5

        success, stdout, stderr = self.ssh_service.execute_command(f"mkdir -p {shlex.quote(REPOS_ROOT)}")
        if not success:
            return False, f"创建目录失败: {stderr}"

        def _retry(action):
            if retry_count < max_retry:
                logger.warning('%s失败，重试 (%d/%d)...', action, retry_count + 1, max_retry)
                time.sleep(retry_delay)
                return self.clone_or_pull(task, retry_count + 1)
            return None

        success, stdout, stderr = self.ssh_service.execute_command(f"ls -la {shlex.quote(repo_path)}")

        if 'No such file or directory' in stderr:
            command = f"git -c ssh.ConnectTimeout=30 clone {shlex.quote(task.git_repo)} {shlex.quote(repo_path)}"
            success, stdout, stderr = self.ssh_service.execute_command(command)
            if not success:
                retried = _retry('克隆仓库')
                if retried is not None:
                    return retried
                return False, f"克隆仓库失败: {stderr}"
        else:
            command = f"cd {shlex.quote(repo_path)} && git -c ssh.ConnectTimeout=30 pull origin {shlex.quote(task.git_branch)}"
            success, stdout, stderr = self.ssh_service.execute_command(command)
            if not success:
                retried = _retry('拉取代码')
                if retried is not None:
                    return retried
                return False, f"拉取代码失败: {stderr}"

        command = f"cd {shlex.quote(repo_path)} && git checkout {shlex.quote(task.git_branch)}"
        success, stdout, stderr = self.ssh_service.execute_command(command)
        if not success:
            retried = _retry('切换分支')
            if retried is not None:
                return retried
            return False, f"切换分支失败: {stderr}"

        return True, repo_path

    def close(self):
        """关闭SSH连接"""
        self.ssh_service.close()


class TaskExecutor:
    """任务执行编排：拉代码→起容器→装依赖→执行pytest→收集结果"""

    def __init__(self, environment, execution=None):
        self.environment = environment
        self.execution = execution
        self.docker_service = DockerService(environment, execution=execution)

    def _log(self, level, message, context=None, exception=None):
        """同时输出到执行日志（DB）与python logging"""
        if self.execution:
            from .tasks import log_with_context
            log_with_context(self.execution, level.upper(), message, exception=exception, context=context)
        getattr(logger, level)(message)

    def _log_info(self, message, context=None):
        self._log('info', message, context)

    def _log_warning(self, message, context=None):
        self._log('warning', message, context)

    def _log_error(self, message, context=None, exception=None):
        self._log('error', message, context, exception=exception)

    def _resolve_script_path(self, task, repo_path):
        """把任务配置的script_path解析为容器内绝对路径"""
        script_path = (task.script_path or '').replace('\\', '/')

        if script_path.startswith('/'):
            return script_path

        if repo_path:
            # 相对路径拼接到仓库根
            return repo_path.rstrip('/') + '/' + script_path.lstrip('/')
        return script_path

    def _install_requirements(self, repo_path):
        """依赖安装：requirements.txt内容变化时才重装（按MD5哈希判断）"""
        container = self.docker_service.container_name
        requirements_path = f"{repo_path}/requirements.txt"
        hash_file = f"{repo_path}/.last_install_hash"

        success, stdout, stderr = self.docker_service.exec_in_container('ls ' + shlex.quote(requirements_path))
        if not success or 'No such file or directory' in stderr:
            self._log_info(f"未发现依赖文件: {requirements_path}",
                           context={'requirements_path': requirements_path})
            return

        calc_inner = ('md5sum ' + shlex.quote(requirements_path) + ' 2>/dev/null || md5 '
                      + shlex.quote(requirements_path) + ' 2>/dev/null || echo no_hash')
        success, hash_out, _ = self.docker_service.exec_in_container(calc_inner)
        current_hash = hash_out.split()[0] if success and hash_out.strip() and 'no_hash' not in hash_out else "unknown"

        read_inner = 'cat ' + shlex.quote(hash_file) + ' 2>/dev/null || echo ""'
        success, last_hash_out, _ = self.docker_service.exec_in_container(read_inner)
        last_hash = last_hash_out.strip() if success else ""

        self._log_info(f"依赖文件哈希检查 - 当前: {current_hash}, 上次: {last_hash}",
                       context={'current_hash': current_hash, 'last_hash': last_hash})

        if current_hash == 'unknown':
            # 无法计算哈希时直接安装，保证环境一致
            self._log_info("无法计算依赖文件哈希，开始安装依赖包...",
                           context={'requirements_path': requirements_path})
        elif current_hash == last_hash:
            self._log_info("依赖文件无更新，跳过安装",
                           context={'requirements_path': requirements_path})
            return
        else:
            self._log_info("依赖文件有更新，开始安装依赖包...",
                           context={'requirements_path': requirements_path})

        install_inner = 'cd ' + shlex.quote(repo_path) + ' && pip install -r requirements.txt'
        success, install_stdout, install_stderr = self.docker_service.exec_in_container(install_inner)
        if not success:
            # 依赖装不上时继续跑测试，让失败信息暴露在测试输出里
            self._log_error(f"安装依赖失败: {install_stderr}",
                            context={'requirements_path': requirements_path, 'error': install_stderr})
            self._log_warning("依赖安装失败，继续执行测试",
                              context={'requirements_path': requirements_path})
            return

        self._log_info("依赖安装完成",
                       context={'requirements_path': requirements_path, 'output': install_stdout[:300]})
        if current_hash != 'unknown':
            save_inner = 'echo ' + shlex.quote(current_hash) + ' > ' + shlex.quote(hash_file)
            self.docker_service.exec_in_container(save_inner)
            self._log_info(f"已保存依赖安装哈希: {current_hash}",
                           context={'hash_file': hash_file})

    def _prepare_pytest_env(self, repo_path):
        """写pytest.ini固定rootdir、清pytest缓存，避免仓库内其他配置干扰"""
        container = self.docker_service.container_name
        pytest_ini = f"{repo_path}/pytest.ini"

        create_ini_inner = 'printf "[pytest]\\nrootdir = ." > ' + shlex.quote(pytest_ini)
        success, _, err = self.docker_service.exec_in_container(create_ini_inner)
        if success:
            self._log_info(f"已创建pytest.ini: {pytest_ini}", context={'pytest_ini_path': pytest_ini})
        else:
            self._log_warning(f"创建pytest.ini失败: {err}",
                              context={'pytest_ini_path': pytest_ini, 'error': err})

        clean_inner = 'cd ' + shlex.quote(repo_path) + ' && rm -rf .pytest_cache'
        self.docker_service.exec_in_container(clean_inner)

    def _relative_script_path(self, script_path, repo_path):
        """计算pytest用的相对脚本路径（相对仓库根，保证rootdir语义正确）"""
        if not script_path.startswith('/'):
            return script_path
        if repo_path and script_path.startswith(repo_path):
            return script_path[len(repo_path):].lstrip('/')
        return os.path.relpath(script_path, repo_path or '.')

    def execute(self, task):
        """执行任务主流程，返回 (success, stdout, stderr)"""
        docker_service = self.docker_service
        try:
            # 1. Docker就绪
            success, message = docker_service.ensure_docker_running()
            if not success:
                return False, message, ""

            # 2. 容器就绪
            success, message = docker_service.start_container()
            if not success:
                return False, message, ""
            self._log_info(f"容器就绪: {message}", context={'container': docker_service.container_name})

            # 3. 拉取代码（Git任务）
            script_path = (task.script_path or '').replace('\\', '/')
            repo_path = None
            if task.git_repo and (not task.script_source or task.script_source == 'git'):
                git_service = GitService(self.environment, execution=self.execution)
                try:
                    self._log_info("开始Git操作: 克隆或拉取代码",
                                   context={'git_repo': task.git_repo, 'git_branch': task.git_branch})
                    success, repo_path = git_service.clone_or_pull(task)
                    if not success:
                        self._log_error(f"Git操作失败: {repo_path}",
                                        context={'git_repo': task.git_repo, 'error': repo_path})
                        return False, repo_path, ""
                    self._log_info(f"Git操作成功: {repo_path}", context={'repo_path': repo_path})
                finally:
                    git_service.close()

            script_path = self._resolve_script_path(task, repo_path)
            self._log_info(f"脚本路径: {script_path}",
                           context={'script_path': script_path, 'repo_path': repo_path})

            if not repo_path:
                repo_path = '.'

            # 4. 容器内校验脚本存在（快速失败，输出目录内容辅助定位）
            if script_path and script_path.startswith('/'):
                check_inner = 'ls ' + shlex.quote(script_path)
                success, stdout, stderr = docker_service.exec_in_container(check_inner)
                if not success or 'No such file or directory' in stderr:
                    self._log_error(f"脚本文件在容器内不存在: {script_path}",
                                    context={'script_path': script_path, 'error': stderr})
                    list_inner = 'ls -la ' + shlex.quote(os.path.dirname(script_path) or REPOS_ROOT)
                    _, dir_stdout, _ = docker_service.exec_in_container(list_inner)
                    self._log_info(f"脚本所在目录内容: {dir_stdout[:300]}",
                                   context={'script_dir': os.path.dirname(script_path)})
                    return False, f"脚本文件在容器内不存在: {script_path}", stderr

            # 5. 依赖安装（哈希判断增量）
            self._install_requirements(repo_path if repo_path != '.' else REPOS_ROOT)

            # 6. pytest环境准备
            if repo_path != '.':
                self._prepare_pytest_env(repo_path)

            # 7. 构建并执行pytest命令
            # Allure结果目录按execution隔离，避免同一容器并发执行时互相清结果
            result_dir_name = f'result_{self.execution.id}' if self.execution else 'result'
            relative_script = self._relative_script_path(script_path, repo_path if repo_path != '.' else None)
            report_dir = f"{repo_path}/{result_dir_name}"
            junit_xml = f"{repo_path}/junit_{result_dir_name}.xml"

            exec_inner = (
                'cd ' + shlex.quote(repo_path)
                + ' && export PYTHONPATH=' + shlex.quote(repo_path)
                + ' && python -m pytest ' + shlex.quote(relative_script)
                + ' --alluredir=' + shlex.quote(report_dir)
                + ' --clean-alluredir'
                + ' --junitxml=' + shlex.quote(junit_xml)
                + ' --rootdir=' + shlex.quote(repo_path)
                + ' --override-ini=rootdir=' + shlex.quote(repo_path)
                + ' -v'
            )
            self._log_info(f"执行命令: {exec_inner}", context={'execution_command': exec_inner})

            success, stdout, stderr = docker_service.execute_in_container(exec_inner)
            if not success:
                error_message = stdout if stdout else (stderr if stderr else '未知错误')
                # 失败也要尝试解析junitxml（部分用例已执行完）
                self._collect_test_summary(junit_xml)
                return False, error_message, stderr

            # 8. 解析junitxml用例统计
            self._collect_test_summary(junit_xml)

            # 9. 确认Allure结果已生成（仅记录，不阻断）
            success, stdout, stderr = docker_service.exec_in_container('ls ' + shlex.quote(report_dir))
            if not success:
                self._log_warning(f"Allure结果目录不存在: {report_dir}",
                                  context={'report_dir': report_dir, 'error': stderr})

            return True, stdout, stderr
        finally:
            docker_service.close()

    def _collect_test_summary(self, junit_xml_path):
        """拉取并解析容器内的junitxml，把用例统计写到execution.test_summary"""
        if not self.execution:
            return
        import json
        import xml.etree.ElementTree as ET

        success, xml_content, stderr = self.docker_service.exec_in_container(
            'cat ' + shlex.quote(junit_xml_path))
        if not success or not xml_content.strip():
            self._log_warning(f"junitxml不存在，跳过用例统计: {junit_xml_path}",
                              context={'junit_path': junit_xml_path, 'error': stderr})
            return

        try:
            root = ET.fromstring(xml_content)
            suites = root.findall('.//testsuite')
            if not suites:
                return
            summary = {
                'total': sum(int(s.get('tests', 0)) for s in suites),
                'failed': sum(int(s.get('failures', 0)) for s in suites),
                'errors': sum(int(s.get('errors', 0)) for s in suites),
                'skipped': sum(int(s.get('skipped', 0)) for s in suites),
                'time': round(sum(float(s.get('time', 0)) for s in suites), 3),
            }
            summary['passed'] = summary['total'] - summary['failed'] - summary['errors'] - summary['skipped']

            # ORM直写，避免依赖调用方save顺序
            from .models import ExecutionHistory
            ExecutionHistory.objects.filter(id=self.execution.id).update(test_summary=summary)
            self._log_info(f"用例统计: {json.dumps(summary, ensure_ascii=False)}",
                           context={'test_summary': summary})
        except ET.ParseError as e:
            self._log_warning(f"junitxml解析失败: {e}",
                              context={'junit_path': junit_xml_path})


def execute_task_on_remote(task, environment, execution=None):
    """在远程执行机上执行任务（兼容旧调用入口）"""
    executor = TaskExecutor(environment, execution=execution)
    return executor.execute(task)
