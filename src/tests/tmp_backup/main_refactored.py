import configparser
from my_visual_ssh import VisualSSH
from colorama import Fore, Style

def load_config(filename='config.ini'):
    """读取配置文件并返回一个包含所有信息的字典。"""
    print(Fore.YELLOW + "--- 正在加载配置文件... ---")
    parser = configparser.ConfigParser()
    parser.read(filename)
    
    config = {
        'host': parser.get('device_info', 'host'),
        # 读取port，并转换为整数
        'port': parser.getint('device_info', 'port'), 
        'username': parser.get('device_info', 'username'),
        'password': parser.get('device_info', 'password'),
        'user_prompt': parser.get('device_prompts', 'user_prompt').encode('utf-8'),
        'system_prompt': parser.get('device_prompts', 'system_prompt').encode('utf-8'),
        'commands': parser.get('commands_to_run', 'commands').strip().split('\n')
    }
    print(Fore.GREEN + "--- 配置文件加载成功！ ---\n")
    return config

def execute_device_session(config):
    """
    主执行函数：连接设备、进入系统模式并执行一系列命令。
    """
    ssh_session = None
    try:
        # 1. 初始化连接，传入host和port
        ssh_session = VisualSSH(
            host=config['host'],
            port=config['port'], 
            username=config['username'],
            password=config['password']
        )
        
        # 2. 等待用户提示符
        ssh_session.read_until(config['user_prompt'])
        
        # 3. 进入系统视图
        ssh_session.write(b"system-view")
        
        # 4. 等待系统提示符
        ssh_session.read_until(config['system_prompt'])

        # 5. 循环执行命令
        for cmd in config['commands']:
            if not cmd.strip():
                continue
            
            cmd_bytes = cmd.strip().encode('utf-8')
            
            print("\n" + Fore.WHITE + Style.BRIGHT + f"======== 命令输出: {cmd.strip()} ========")
            output = ssh_session.execute(cmd_bytes)
            print(output)
            print(Fore.WHITE + Style.BRIGHT + "================================================")

    except Exception as e:
        print(Fore.RED + f"!!! 在执行会话时发生严重错误: {e}")
    finally:
        if ssh_session:
            ssh_session.close()

# Python程序的标准主入口
if __name__ == "__main__":
    device_config = load_config()
    execute_device_session(device_config)