import paramiko
import sys
import time
import logging # <-- 1. 导入logging模块
from colorama import init, Fore, Style

init(autoreset=True)

class VisualSSH:
    def __init__(self, host, username, password, port=22, timeout=10, logger=None): # <-- 2. 在构造函数中接收logger
        """
        初始化时接收一个logger对象。
        """
        # 3. 如果没有提供logger，创建一个不会产生任何输出的'哑'logger，以防报错
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.addHandler(logging.NullHandler())

        print(Fore.YELLOW + f"--- 准备SSH连接到 {host}:{port} ---")
        self.logger.info(f"--- 准备SSH连接到 {host}:{port} ---") # <-- 4. 开始记录日志
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(hostname=host, port=port, username=username, password=password, timeout=timeout)
            
            self.chan = self.client.invoke_shell()
            self.chan.settimeout(timeout)

            self.current_prompt = None
            print(Fore.GREEN + Style.BRIGHT + "--- SSH 连接成功！ ---\n")
            self.logger.info("--- SSH 连接成功！ ---") # <-- 记录

        except Exception as e:
            print(Fore.RED + f"!!! SSH 连接失败: {e}")
            self.logger.error(f"!!! SSH 连接失败: {e}", exc_info=True) # <-- 记录错误
            sys.exit(1)

    def _log_received(self, data):
        """现在这个方法同时负责打印到屏幕和记录到日志。"""
        decoded_data = data.decode('utf-8', errors='ignore')
        # 打印到屏幕（带颜色）
        print(Fore.GREEN + "[接收] <<<")
        print(Style.DIM + decoded_data, end='')
        # 记录到文件（纯文本）
        self.logger.info("[接收] <<<\n" + decoded_data)

    def write(self, command_bytes):
        """发送命令时，同时打印和记录。"""
        if not command_bytes.endswith(b'\n'):
            command_bytes += b'\n'
            
        print(Fore.BLUE + f"[发送] >>> {command_bytes!r}")
        self.logger.info(f"[发送] >>> {command_bytes!r}")
        
        self.chan.send(command_bytes)

    # read_until 和 execute 方法的核心逻辑不需要大改，因为它们
    # 依赖的 _log_received 和 write 方法已经被我们修改好了。
    # 我们只需要将这些方法中的 print 调用也替换/补充为 logger 调用。
    
    def read_until(self, expected_bytes, timeout=10):
        print(Fore.CYAN + f"\n--- [等待并记忆] ...正在等到标志: {expected_bytes!r}... ---")
        self.logger.info(f"--- [等待并记忆] ...正在等到标志: {expected_bytes!r}... ---")
        
        output = b''
        start_time = time.time()
        # ... (循环逻辑不变) ...
        while time.time() - start_time < timeout:
            if self.chan.recv_ready():
                output += self.chan.recv(65535)
                if expected_bytes in output:
                    break
            time.sleep(0.1)

        self._log_received(output)
        
        self.current_prompt = expected_bytes
        print(Fore.YELLOW + f"--- [记忆更新] 当前提示符已设为: {self.current_prompt!r} ---")
        self.logger.info(f"--- [记忆更新] 当前提示符已设为: {self.current_prompt!r} ---")
        return output

    def execute(self, command_bytes, final_prompt_bytes=None, page_break_bytes=b'---- More ----', space_count=1):
        print(Fore.MAGENTA + f"\n--- [智能执行] 正在执行命令: {command_bytes!r} ---")
        self.logger.info(f"--- [智能执行] 正在执行命令: {command_bytes!r} ---")
        
        prompt_to_use = final_prompt_bytes or self.current_prompt
        if not prompt_to_use:
            # ... (异常处理逻辑不变) ...
            raise ValueError("无法执行命令: 提示符未知。")
            
        print(Fore.MAGENTA + f"--- [使用记忆] 将等待最终提示符: {prompt_to_use!r} ---")
        self.logger.info(f"--- [使用记忆] 将等待最终提示符: {prompt_to_use!r} ---")

        self.write(command_bytes)
        
        full_output = b''
        space_to_send = (b' ' * space_count)
        # ... (循环处理逻辑不变) ...
        while True:
            try:
                chunk = self.chan.recv(65535)
                if not chunk: break
                
                # _log_received 会同时处理打印和日志
                self._log_received(chunk)
                full_output += chunk

                if page_break_bytes in chunk:
                    print(Fore.CYAN + "--- [自动翻页] 检测到 'More'，发送空格... ---")
                    self.logger.info("--- [自动翻页] 检测到 'More'，发送空格... ---")
                    self.write(space_to_send)
                elif prompt_to_use in chunk:
                    print(Fore.GREEN + "--- [执行完毕] 检测到最终提示符，输出完成。 ---")
                    self.logger.info("--- [执行完毕] 检测到最终提示符，输出完成。 ---")
                    break
            except Exception as e:
                print(Fore.RED + f"!!! 在执行命令时发生超时或错误: {e}")
                self.logger.error(f"!!! 在执行命令时发生超时或错误: {e}", exc_info=True)
                break
        
        return full_output.decode('utf-8', errors='ignore')

    def close(self):
        print(Fore.YELLOW + "\n--- 关闭SSH连接 ---")
        self.logger.info("--- 关闭SSH连接 ---")
        self.client.close()