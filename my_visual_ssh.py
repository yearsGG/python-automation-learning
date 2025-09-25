# 首先需要安装: pip install paramiko
import paramiko
import sys
import time
from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)

class VisualSSH:
    """
    一个为调试而生的、可视化的SSH交互工具 v1.2 (记忆版)。
    这个类是 my_visual_telnet.py 的直接升级版，旨在提供
    完全相同的交互体验，但使用更安全的SSH协议。
    """
    def __init__(self, host, username, password, port=22, timeout=10):
        """
        使用 Paramiko 初始化SSH连接。
        """
        print(Fore.YELLOW + f"--- 准备SSH连接到 {host} ---")
        try:
            # 1. 创建SSH客户端实例
            self.client = paramiko.SSHClient()
            # 2. 自动接受不在know_hosts文件中的主机密钥 (仅限实验环境!)
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # 3. 连接
            self.client.connect(hostname=host,
                                port=port,
                                username=username,
                                password=password,
                                timeout=timeout)
            
            # 4. 获取一个交互式的shell通道，这是与telnetlib最相似的部分
            self.chan = self.client.invoke_shell()
            self.chan.settimeout(timeout)

            # 5. 完美保留“记忆”属性
            self.current_prompt = None
            print(Fore.GREEN + Style.BRIGHT + "--- SSH 连接成功！ ---\n")

        except Exception as e:
            print(Fore.RED + f"!!! SSH 连接失败: {e}")
            sys.exit(1)

    def _log_received(self, data):
        """(完全复用) 记录接收到的数据并用绿色打印。"""
        decoded_data = data.decode('utf-8', errors='ignore')
        print(Fore.GREEN + "[接收] <<<")
        print(Style.DIM + decoded_data, end='')

    def read_until(self, expected_bytes, timeout=10):
        """
        (逻辑重构) 使用paramiko的recv()循环读取，直到出现期望的字节串。
        """
        print(Fore.CYAN + f"\n--- [等待并记忆] ...正在等到标志: {expected_bytes!r}... ---")
        
        output = b''
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查通道是否准备好接收数据
            if self.chan.recv_ready():
                # 从缓冲区读取最多65535字节
                output += self.chan.recv(65535)
                # 如果找到了期望的标志，就跳出循环
                if expected_bytes in output:
                    break
            time.sleep(0.1) # 避免CPU空转

        self._log_received(output)
        
        # (完全复用) 更新记忆
        self.current_prompt = expected_bytes
        print(Fore.YELLOW + f"--- [记忆更新] 当前提示符已设为: {self.current_prompt!r} ---")
        return output

    def write(self, command_bytes):
        """(逻辑替换) 使用paramiko的send()发送命令。"""
        if not command_bytes.endswith(b'\n'):
            command_bytes += b'\n'
            
        print(Fore.BLUE + f"[发送] >>> {command_bytes!r}")
        # 将telnet的write替换为channel的send
        self.chan.send(command_bytes)
    
    def execute(self, command_bytes, final_prompt_bytes=None, page_break_bytes=b'---- More ----', space_count=1):
        """
        (核心逻辑复用) 智能执行命令，并自动处理翻页。
        """
        print(Fore.MAGENTA + f"\n--- [智能执行] 正在执行命令: {command_bytes!r} ---")
        
        # (完全复用) 检查是否需要使用记忆
        prompt_to_use = final_prompt_bytes or self.current_prompt
        if not prompt_to_use:
            raise ValueError("无法执行命令: 提示符未知。请先调用 read_until()。")
            
        print(Fore.MAGENTA + f"--- [使用记忆] 将等待最终提示符: {prompt_to_use!r} ---")

        self.write(command_bytes)
        
        full_output = b''
        space_to_send = (b' ' * space_count)

        while True:
            # 持续从缓冲区读取数据
            chunk = self.chan.recv(65535)
            if not chunk:
                break
                
            self._log_received(chunk)
            full_output += chunk

            # 自动翻页逻辑
            if page_break_bytes in chunk:
                print(Fore.CYAN + "--- [自动翻页] 检测到 'More'，发送空格... ---")
                self.write(space_to_send)
            # 结束判断逻辑
            elif prompt_to_use in chunk:
                print(Fore.GREEN + "--- [执行完毕] 检测到最终提示符，输出完成。 ---")
                break
        
        return full_output.decode('utf-8', errors='ignore')

    def close(self):
        """(逻辑替换) 关闭SSH连接。"""
        print(Fore.YELLOW + "\n--- 关闭SSH连接 ---")
        # 先关闭客户端，通道会自动关闭
        self.client.close()