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
    网络设备自动化驱动类 v2.0
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
            
            # 自动探测提示符
            self._read_until(b'>') # 或者是 b']'
            self.logger.info("SSH Connection Established")
            print(Fore.GREEN + f"--- [成功] 已连接到 {self.host} ---")
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            print(Fore.RED + f"!!! 连接失败: {e}")
            raise e

    def _read_until(self, expected, timeout=None):
        if timeout is None:
            timeout = self.timeout
        
        buffer = b''
        start = time.time()
        while time.time() - start < timeout:
            if self.chan.recv_ready():
                data = self.chan.recv(65535)
                buffer += data
                if expected in buffer:
                    break
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
            expect_prompt = b']' 

        print(Fore.CYAN + f">>> 发送命令: {command}")
        self.logger.info(f"Execute: {command}")
        
        self.chan.send(command.encode('utf-8') + b'\n')
        
        full_output = b''
        while True:
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

    def close(self):
        if self.client:
            self.client.close()
            print(Fore.YELLOW + f"--- [断开] 连接已关闭 ---")