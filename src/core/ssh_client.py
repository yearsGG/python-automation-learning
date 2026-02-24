import paramiko
import time
import os
import sys
import re
import textfsm  # 引入 TextFSM 库
from colorama import init, Fore

# 引入日志模块
from utils.logger import setup_logger

init(autoreset=True)

class NetworkDevice:
    """
    网络设备自动化驱动类 v3.0
    核心升级：支持手动指定 TextFSM 模板路径，彻底解决 NTC 索引失效问题。
    """

    def __init__(self, host, username, password, port=22, timeout=10, device_type='huawei_vrp'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.device_type = device_type

        # 初始化日志
        self.logger = setup_logger(f"Device-{host}")

        # 内部变量
        self.client = None
        self.chan = None
        self.base_prompt = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """建立 SSH 连接"""
        print(Fore.YELLOW + f"--- [连接] 正在连接到 {self.host} ... ---")
        self.logger.info(f"Connecting to {self.host}:{self.port}")

        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host, port=self.port,
                username=self.username, password=self.password,
                timeout=self.timeout, look_for_keys=False, allow_agent=False
            )

            self.chan = self.client.invoke_shell()
            self.chan.settimeout(self.timeout)

            # 自动探测并保存基础提示符
            initial_output = self._read_until([b'>', b']', b'#'])
            self.base_prompt = self._extract_prompt(initial_output)
            self.logger.info("SSH Connection Established")
            print(Fore.GREEN + f"--- [成功] 已连接到 {self.host} (提示符: {self.base_prompt}) ---")

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            print(Fore.RED + f"!!! 连接失败: {e}")
            raise e

    def _extract_prompt(self, output):
        """从输出中提取提示符"""
        # 查找最后一个换行符后的文本，这通常是提示符
        lines = output.split('\n')
        last_line = lines[-1] if lines else ''

        # 尝试匹配常见的提示符模式
        prompt_patterns = [
            r'[<\[].*?[>\]]\s*$',  # 匹配 <AR1> 或 [AR1]
            r'.*?#\s*$',  # 匹配 # 提示符
            r'.*?>\s*$',  # 匹配 > 提示符
            r'.*?]\s*$',  # 匹配 ] 提示符
        ]

        for pattern in prompt_patterns:
            match = re.search(pattern, last_line)
            if match:
                return match.group(0).encode('utf-8')

        # 如果没找到匹配的，返回最后一行
        return last_line.encode('utf-8') if last_line else b'>'

    def _read_until(self, expected_list, timeout=None):
        """
        读取数据直到遇到任意一个预期的字符串
        :param expected_list: 期望字符串的列表，可以是单个字符串或列表
        :return: 接收到的数据
        """
        if isinstance(expected_list, (bytes, str)):
            expected_list = [expected_list]

        if timeout is None:
            timeout = self.timeout

        buffer = b''
        start = time.time()
        while time.time() - start < timeout:
            if self.chan.recv_ready():
                data = self.chan.recv(65535)
                buffer += data

                # 检查是否包含任意一个期望的字符串
                for expected in expected_list:
                    if expected in buffer:
                        return buffer.decode('utf-8', errors='ignore')
            time.sleep(0.1)

        return buffer.decode('utf-8', errors='ignore')

    def _clean_data(self, raw_data, command):
        """数据清洗管道"""
        # 1. 去除 ANSI 颜色代码
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        data = ansi_escape.sub('', raw_data)

        # 2. 去除分页标记和退格符
        data = data.replace('---- More ----', '').replace('\x08', '')
        data = re.sub(r'  \x1b\[16D\s+\x1b\[16D', '', data)

        # 3. 去除命令回显 (头部)
        cmd_stripped = command.strip()
        if cmd_stripped in data:
             _, _, data = data.partition(cmd_stripped)
             data = data.lstrip()

        # 4. 去除尾部提示符 (例如 [AR1000v] 或 <AR1>)
        data = re.sub(r'\n[<\[].+?[>\]]\s*$', '', data)

        return data.strip()

    def execute_command(self, command, expect_prompt=None):
        """执行单条命令并返回清洗后的文本"""
        if not expect_prompt:
            expect_prompt = self.base_prompt or b']'

        print(Fore.CYAN + f">>> 发送命令: {command}")
        self.logger.info(f"Execute: {command}")

        self.chan.send(command.encode('utf-8') + b'\n')

        full_output = b''
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self.chan.recv_ready():
                chunk = self.chan.recv(65535)
                full_output += chunk

                if b'---- More ----' in chunk:
                    self.chan.send(b' ')
                    time.sleep(0.1)
                elif expect_prompt in chunk:
                    break
            else:
                time.sleep(0.1)

        decoded = full_output.decode('utf-8', errors='ignore')
        return self._clean_data(decoded, command)

    def execute_commands(self, commands):
        """执行多个命令"""
        results = []
        for cmd in commands:
            result = self.execute_command(cmd)
            results.append({
                'command': cmd,
                'output': result
            })
        return results

    def enter_system_view(self):
        """进入系统视图"""
        result = self.execute_command("system-view", expect_prompt=b']')
        return result

    def exit_system_view(self):
        """退出系统视图"""
        result = self.execute_command("quit", expect_prompt=b'>')
        return result

    def get_output_with_template(self, command, template_path):
        """
        🔥 [核心新功能] 执行命令并使用指定的 TextFSM 模板解析
        :param command: 要执行的命令 (如 'display ip int brief')
        :param template_path: 模板文件的绝对路径
        :return: 字典列表 (List[Dict])
        """
        # 1. 获取原始数据
        raw_output = self.execute_command(command)

        # 2. 检查模板是否存在
        if not os.path.exists(template_path):
            self.logger.error(f"Template not found: {template_path}")
            return {"error": f"Template not found: {template_path}"}

        try:
            # 3. TextFSM 解析
            with open(template_path, 'r', encoding='utf-8') as f:
                re_table = textfsm.TextFSM(f)
                result = re_table.ParseText(raw_output)
                headers = re_table.header

                # 4. 强制转小写 (方便前端调用)
                headers_lower = [h.lower() for h in headers]

                # 5. 组合成字典
                parsed_data = [dict(zip(headers_lower, row)) for row in result]

            print(Fore.GREEN + f"--- [解析] 成功解析 {len(parsed_data)} 条数据 (Template: {os.path.basename(template_path)}) ---")
            return parsed_data

        except Exception as e:
            self.logger.error(f"TextFSM Parse Error: {e}")
            print(Fore.RED + f"!!! 解析失败: {e}")
            return raw_output

    def get_parsed_output(self, command, template_path=None):
        """
        执行命令并解析输出，自动选择模板
        :param command: 要执行的命令
        :param template_path: 模板路径，如果为None则尝试自动选择
        :return: 解析后的数据
        """
        if template_path is None:
            # 根据命令自动选择模板
            template_path = self._auto_select_template(command)

        return self.get_output_with_template(command, template_path)

    def _auto_select_template(self, command):
        """根据命令自动选择模板"""
        template_dir = "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates"

        # 命令关键词到模板的映射
        command_templates = {
            'display ip interface brief': 'huawei_vrp_display_ip_interface_brief.textfsm',
            'display version': 'huawei_vrp_display_version.textfsm',
            'display current-configuration': 'huawei_vrp_display_current-configuration.textfsm',
            'display interface': 'huawei_vrp_display_interface.textfsm',
            'display vlan': 'huawei_vrp_display_vlan.textfsm',
            'show ip interface brief': 'cisco_ios_show_ip_interface_brief.textfsm',
            'show version': 'cisco_ios_show_version.textfsm',
        }

        # 尝试匹配命令
        for cmd_pattern, template_name in command_templates.items():
            if cmd_pattern in command.lower():
                return os.path.join(template_dir, template_name)

        # 默认返回IP接口模板
        return "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_ip_interface_brief.textfsm"

    def configure(self, config_commands):
        """
        执行配置命令
        :param config_commands: 配置命令列表
        """
        print(Fore.CYAN + f">>> 进入系统视图并执行配置...")

        # 进入系统视图
        self.enter_system_view()

        results = []
        for cmd in config_commands:
            result = self.execute_command(cmd, expect_prompt=b']')
            results.append({
                'command': cmd,
                'output': result
            })

        print(Fore.GREEN + f">>> 配置完成，共执行 {len(config_commands)} 条命令")
        return results

    def save_config(self):
        """保存配置"""
        result = self.execute_command("save", expect_prompt=b']')
        # 确认保存
        result += self.execute_command("y", expect_prompt=self.base_prompt)
        return result

    def close(self):
        if self.client:
            self.client.close()
            print(Fore.YELLOW + f"--- [断开] 连接已关闭 ---")