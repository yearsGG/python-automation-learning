# 文件名: my_visual_telnet.py (V1.2 - 拥有记忆的版本)

import telnetlib
import sys
from colorama import init, Fore, Style

init(autoreset=True)

class VisualTelnet:
    """
    一个为调试而生的、可视化的Telnet交互工具 v1.2 (记忆版)。
    
    V1.2 更新: 增加了上下文记忆功能。工具能自动记住上一个 read_until()
    的提示符，使得 execute() 调用变得极其简洁。
    """
    def __init__(self, host, port=23, timeout=10):
        """初始化。同时初始化一个'记忆'属性。"""
        print(Fore.YELLOW + f"--- 准备连接到 {host} ---")
        try:
            self.tn = telnetlib.Telnet(host, port, timeout)
            self.tn.set_debuglevel(0)
            # <--- 核心改动 1: 赋予工具一个'记忆'属性 ---
            self.current_prompt = None
            print(Fore.GREEN + Style.BRIGHT + "--- 连接成功！ ---\n")
        except Exception as e:
            print(Fore.RED + f"!!! 连接失败: {e}")
            sys.exit(1)

    # ... _log_received 方法不变 ...
    def _log_received(self, data):
        decoded_data = data.decode('utf-8', errors='ignore')
        print(Fore.GREEN + "[接收] <<<")
        print(Style.DIM + decoded_data, end='')

    def read_until(self, expected_bytes, timeout=10):
        """
        读取直到出现期望的字节串，并将其“存入记忆”。
        """
        print(Fore.CYAN + f"\n--- [等待并记忆] ...正在等到标志: {expected_bytes!r}... ---")
        output = self.tn.read_until(expected_bytes, timeout)
        self._log_received(output)
        # <--- 核心改动 2: 将成功等到的提示符，存入记忆 ---
        self.current_prompt = expected_bytes
        print(Fore.YELLOW + f"--- [记忆更新] 当前提示符已设为: {self.current_prompt!r} ---")
        return output

    # ... write 和 read_very_eager 方法不变 ...
    def write(self, command_bytes):
        if not command_bytes.endswith(b'\n'):
            command_bytes += b'\n'
        print(Fore.BLUE + f"[发送] >>> {command_bytes!r}")
        self.tn.write(command_bytes)

    def read_very_eager(self):
        output = self.tn.read_very_eager()
        if output:
            self._log_received(output)
        else:
            print(Fore.GREEN + "[接收] <<< (缓冲区无新内容)")
        return output
    
    def execute(self, command_bytes, final_prompt_bytes=None, space_count=1):
        """
        执行命令。如果未指定结束提示符，将自动使用'记忆'中的那一个。
        """
        print(Fore.MAGENTA + f"\n--- [智能执行] 正在执行命令: {command_bytes!r} ---")
        
        # <--- 核心改动 3: 检查是否需要使用记忆 ---
        prompt_to_use = final_prompt_bytes or self.current_prompt
        if not prompt_to_use:
            # 这是一个保护机制，防止用户在一次 read_until 都没调用的情况下就用 execute
            raise ValueError("无法执行命令: 提示符未知。请先调用 read_until() 或在 execute() 中明确提供 'final_prompt_bytes'。")
        
        print(Fore.MAGENTA + f"--- [使用记忆] 将等待最终提示符: {prompt_to_use!r} ---")

        self.write(command_bytes)

        all_output_chunks = []
        space_to_send = (b' ' * space_count)

        while True:
            try:
                # 使用我们决定好的提示符
                index, match, data = self.tn.expect([b'---- More ----', prompt_to_use], timeout=15)
                all_output_chunks.append(data)
                
                if index == 0:
                    print(Fore.CYAN + "--- [自动翻页] 检测到 'More'，发送空格... ---")
                    self.write(space_to_send)
                elif index == 1:
                    print(Fore.GREEN + "--- [执行完毕] 检测到最终提示符，输出完成。 ---")
                    break
            except Exception as e:
                print(Fore.RED + f"!!! 在执行命令时发生错误: {e}")
                break
        
        full_output = b"".join(all_output_chunks).decode('utf-8', errors='ignore')
        return full_output

    def close(self):
        """关闭Telnet连接。"""
        print(Fore.YELLOW + "\n--- 关闭连接 ---")
        self.tn.close()