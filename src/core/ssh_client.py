import paramiko
import time
import os
import sys
import re
from colorama import init, Fore, Style

# 引入我们刚才写的日志模块
# 注意：这里假设 src 是根目录，如果报错，可能需要在 main.py 里处理路径
from utils.logger import setup_logger

# 尝试导入 ntc_templates
try:
    from ntc_templates.parse import parse_output
except ImportError:
    parse_output = None

init(autoreset=True)

class NetworkDevice:
    """
    网络设备自动化驱动类
    封装了 SSH 连接、命令交互、数据清洗及 TextFSM 解析功能。
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
        self.current_prompt = None

        # 初始化环境
        self._setup_ntc_templates()

    def __enter__(self):
        """支持 with 语句：进入时自动连接"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句：退出时自动关闭"""
        self.close()

    def _setup_ntc_templates(self):
        """自动配置 NTC Templates 环境变量"""
        global parse_output
        current_file_path = os.path.abspath(__file__) # src/core/ssh_client.py
        src_root = os.path.dirname(os.path.dirname(current_file_path)) # src/
        project_root = os.path.dirname(src_root) # 项目根目录
        
        # 设置 NTC_TEMPLATES_DIR
        potential_paths = [
            os.path.join(project_root, 'ntc-templates', 'templates', 'templates'),
            os.path.join(project_root, 'ntc-templates', 'templates'),
        ]
        
        for path in potential_paths:
            index_file = os.path.join(path, 'index')
            if os.path.exists(index_file):
                os.environ["NTC_TEMPLATES_DIR"] = path
                self.logger.info(f"NTC Templates 目录已设置为: {path}")
                break
        
        if parse_output is None:
            sys.path.append(os.path.join(project_root, 'ntc-templates'))
            try:
                from ntc_templates.parse import parse_output as po
                parse_output = po
            except ImportError:
                self.logger.warning("无法加载 ntc_templates 库，解析功能将受限。")

    def connect(self):
        """建立 SSH 连接"""
        print(Fore.YELLOW + f"--- [连接] 正在连接到 {self.host} ... ---")
        self.logger.info(f"正在连接到 {self.host}:{self.port}")
        
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
            
            # 自动探测提示符 (简单处理)
            self._read_until(b'>') # 或者是 b']'
            self.logger.info("SSH 连接建立成功")
            print(Fore.GREEN + f"--- [成功] 已连接到 {self.host} ---")
            
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            print(Fore.RED + f"!!! 连接失败: {e}")
            raise e

    def _read_until(self, expected, timeout=None):
        """读取流直到遇到特定字符"""
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
        
        decoded = buffer.decode('utf-8', errors='ignore')
        return decoded

    def _clean_data(self, raw_data):
        """数据清洗管道"""
        # 1. 去除 ANSI 颜色
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        data = ansi_escape.sub('', raw_data)
        
        # 2. 去除分页和退格
        data = data.replace('---- More ----', '').replace('\x08', '')
        data = data.replace('  \x1b[16D                                          \x1b[16D', '')
        
        # 3. [关键修复] 去除尾部的提示符 (例如 [AR1000v] 或 <AR1>)
        # 这个正则会匹配行尾的 <...> 或 [...] 并将其删除
        data = re.sub(r'\n[<\[].+?[>\]]\s*$', '', data)
        
        return data

    def execute_command(self, command, expect_prompt=None):
        """执行单条命令并返回清洗后的文本"""
        if not expect_prompt:
            # 简单猜测提示符：如果在系统视图就是 ']'，用户视图就是 '>'
            expect_prompt = b']' 

        print(Fore.CYAN + f">>> 发送命令: {command}")
        self.logger.info(f"Execute: {command}")
        
        self.chan.send(command.encode('utf-8') + b'\n')
        
        # 智能读取（处理分页）
        full_output = b''
        while True:
            if self.chan.recv_ready():
                chunk = self.chan.recv(65535)
                full_output += chunk
                
                if b'---- More ----' in chunk:
                    self.chan.send(b' ') # 翻页
                    time.sleep(0.1)
                elif expect_prompt in chunk:
                    break
            else:
                time.sleep(0.1)
        
        decoded = full_output.decode('utf-8', errors='ignore')
        cleaned = self._clean_data(decoded)
        
        # 4. 去除命令回显 (头部)
        # 防止命令本身干扰 TextFSM 的第一行匹配
        cmd_stripped = command.strip()
        if cmd_stripped in cleaned:
             _, _, cleaned = cleaned.partition(cmd_stripped)
             cleaned = cleaned.lstrip()
             
        return cleaned

    def get_parsed_output(self, command):
        """执行命令并返回结构化数据 (JSON/List)"""
        raw_output = self.execute_command(command)
        
        if not parse_output:
            return {"error": "NTC library not loaded", "raw": raw_output}
            
        try:
            # 调用 NTC 解析
            parsed = parse_output(platform=self.device_type, command=command, data=raw_output)
            print(Fore.GREEN + f"--- [解析] 成功解析 {len(parsed)} 条数据 ---")
            return parsed
        except Exception as e:
            self.logger.error(f"解析失败: {e}")
            print(Fore.RED + f"!!! 解析失败: {e}")
            # 调试用：如果解析失败，可以取消下面注释查看原始数据
            # print(f"DEBUG Raw Data: {repr(raw_output)}")
            return raw_output

    def configure(self, configs):
        """批量下发配置"""
        print(Fore.MAGENTA + f"--- [配置] 开始下发 {len(configs)} 条配置 ---")
        
        # 1. 进入系统视图
        self.chan.send(b'system-view\n')
        time.sleep(1)
        self.chan.recv(65535) # 清空缓冲区
        
        log_output = []
        for cmd in configs:
            print(f"  -> {cmd}")
            self.chan.send(cmd.encode('utf-8') + b'\n')
            time.sleep(0.5) # 给一点时间
        
        # 2. 尝试读取一下结果
        if self.chan.recv_ready():
            out = self.chan.recv(65535).decode('utf-8', errors='ignore')
            log_output.append(out)
            
        print(Fore.MAGENTA + f"--- [配置] 下发完成 ---")
        return "\n".join(log_output)

    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()
            print(Fore.YELLOW + f"--- [断开] 连接已关闭 ---")