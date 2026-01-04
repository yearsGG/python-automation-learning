import paramiko
import sys
import time
import logging
import os
import re
from colorama import init, Fore, Style

# 尝试导入 ntc_templates
# 如果通过 pip 安装了，这里直接能用
# 如果是 clone 的代码，下面会尝试动态添加路径
try:
    from ntc_templates.parse import parse_output
except ImportError:
    parse_output = None

init(autoreset=True)

class VisualSSH:
    def __init__(self, host, username, password, port=22, timeout=10, logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.addHandler(logging.NullHandler())

        # --- 自动配置 ntc-templates 环境 ---
        self._setup_ntc_templates()

        print(Fore.YELLOW + f"--- 准备 SSH 连接到 {host}:{port} ---")
        self.logger.info(f"--- 准备 SSH 连接到 {host}:{port} ---")
        
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=host, 
                port=port, 
                username=username, 
                password=password, 
                timeout=timeout,
                look_for_keys=False, 
                allow_agent=False
            )

            self.chan = self.client.invoke_shell()
            self.chan.settimeout(timeout)

            self.current_prompt = None
            print(Fore.GREEN + Style.BRIGHT + "--- SSH 连接成功！ ---\n")
            self.logger.info("--- SSH 连接成功！ ---")

        except Exception as e:
            print(Fore.RED + f"!!! SSH 连接失败: {e}")
            self.logger.error(f"!!! SSH 连接失败: {e}", exc_info=True)
            raise e

    def _setup_ntc_templates(self):
        """配置 ntc-templates 的搜索路径"""
        global parse_output
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # 1. 寻找 ntc_templates 库代码的位置 (为了导入 parse_output)
        if parse_output is None:
            lib_path = os.path.join(project_root, 'ntc-templates')
            if os.path.exists(os.path.join(lib_path, 'ntc_templates')):
                sys.path.append(lib_path)
                try:
                    from ntc_templates.parse import parse_output
                    self.logger.info("成功从本地目录导入 ntc_templates")
                except ImportError:
                    self.logger.error("无法导入 ntc_templates，解析功能将不可用")

        # 2. 寻找 templates 目录 (为了设置 NTC_TEMPLATES_DIR)
        # 优先寻找包含 'index' 文件的目录
        potential_paths = [
            os.path.join(project_root, 'ntc-templates', 'templates', 'templates'), # 双层结构
            os.path.join(project_root, 'ntc-templates', 'templates'),              # 标准结构
        ]
        
        for path in potential_paths:
            index_file = os.path.join(path, 'index')
            if os.path.exists(index_file):
                os.environ["NTC_TEMPLATES_DIR"] = path
                self.logger.info(f"设置 NTC_TEMPLATES_DIR = {path}")
                break

    def _log_received(self, data):
        decoded_data = data.decode('utf-8', errors='ignore')
        print(Fore.GREEN + "[接收] <<<")
        print(Style.DIM + decoded_data, end='')
        self.logger.info("[接收] <<<\n" + decoded_data)

    def write(self, command_bytes):
        if not command_bytes.endswith(b'\n'):
            command_bytes += b'\n'
        print(Fore.BLUE + f"[发送] >>> {command_bytes!r}")
        self.logger.info(f"[发送] >>> {command_bytes!r}")
        self.chan.send(command_bytes)

    def read_until(self, expected_bytes, timeout=10):
        print(Fore.CYAN + f"\n--- [等待并记忆] ...正在等到标志: {expected_bytes!r}... ---")
        self.logger.info(f"--- [等待并记忆] ...正在等到标志: {expected_bytes!r}... ---")

        output = b''
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.chan.recv_ready():
                chunk = self.chan.recv(65535)
                output += chunk
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
            raise ValueError("无法执行命令: 提示符未知。")

        print(Fore.MAGENTA + f"--- [使用记忆] 将等待最终提示符: {prompt_to_use!r} ---")
        self.logger.info(f"--- [使用记忆] 将等待最终提示符: {prompt_to_use!r} ---")

        self.write(command_bytes)

        full_output = b''
        space_to_send = (b' ' * space_count)

        while True:
            try:
                if self.chan.recv_ready():
                    chunk = self.chan.recv(65535)
                    if not chunk:
                        break

                    full_output += chunk

                    if page_break_bytes in chunk:
                        print(Fore.CYAN + "--- [自动翻页] 检测到 'More'，发送空格... ---")
                        self.logger.info("--- [自动翻页] 检测到 'More'，发送空格... ---")
                        self.write(space_to_send)
                        time.sleep(0.2)
                    elif prompt_to_use in chunk:
                        print(Fore.GREEN + "--- [执行完毕] 检测到最终提示符，输出完成。 ---")
                        self.logger.info("--- [执行完毕] 检测到最终提示符，输出完成。 ---")
                        break
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(Fore.RED + f"!!! 在执行命令时发生超时或错误: {e}")
                self.logger.error(f"!!! 在执行命令时发生超时或错误: {e}", exc_info=True)
                break

        self._log_received(full_output)
        return full_output.decode('utf-8', errors='ignore')

    def _clean_data(self, raw_data):
        """清洗数据：去除颜色代码、More、退格符"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        data = ansi_escape.sub('', raw_data)
        data = data.replace('---- More ----', '')
        data = data.replace('\x08', '') 
        data = data.replace('  \x1b[16D                                          \x1b[16D', '')
        return data

    def execute_and_parse(self, command, platform='huawei_vrp'):
        """
        执行命令并调用 ntc_templates.parse_output 进行解析
        :param command: 命令字符串
        :param platform: 设备平台 (默认为 huawei_vrp, 对应 ntc-templates 的索引)
        """
        # 1. 导入检查
        global parse_output
        if parse_output is None:
            # 尝试再次导入（为了保险）
            try:
                from ntc_templates.parse import parse_output
            except ImportError:
                print(Fore.RED + "错误: 无法导入 ntc_templates。请确保库已下载或安装。")
                return None

        # 2. 获取原始文本
        raw_output = self.execute(command.encode('utf-8'))
        
        # 3. 清洗数据 (必须做！否则 TextFSM 仍然会报 State Error)
        clean_output = self._clean_data(raw_output)

        # 4. 去除命令回显 (解决 State Error 的关键)
        command_str = command.strip()
        if command_str in clean_output:
             _, _, rest = clean_output.partition(command_str)
             clean_output = rest.lstrip()

        # 5. 调用官方解析函数
        self.logger.info(f"调用 ntc_templates 解析: platform={platform}, command={command}")
        try:
            # 官方接口调用方式：platform, command, data
            parsed_data = parse_output(platform=platform, command=command, data=clean_output)
            
            # 官方返回的是 [{}, {}] 格式的字典列表
            self.logger.info(f"解析成功，获得 {len(parsed_data)} 条数据")
            return parsed_data

        except Exception as e:
            print(Fore.RED + f"!!! ntc_templates 解析异常: {e}")
            self.logger.error(f"解析过程出错: {e}")
            # 如果解析失败，返回原始文本方便调试
            return raw_output 

    def close(self):
        print(Fore.YELLOW + "\n--- 关闭 SSH 连接 ---")
        self.logger.info("--- 关闭 SSH 连接 ---")
        self.client.close()