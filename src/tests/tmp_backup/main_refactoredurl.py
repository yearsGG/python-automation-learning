import configparser
import logging # <-- 1. 导入logging模块
import os      # <-- 2. 导入os模块，用于创建文件夹
import datetime # <-- 3. 导入datetime模块，用于生成带时间戳的文件名
from my_visual_ssh import VisualSSH
from colorama import Fore, Style

def setup_logger():
    """配置并返回一个日志记录器。"""
    # 确保log文件夹存在
    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)
    
    # 生成带时间戳的日志文件名，例如 '2025-09-28_15-30-05.log'
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(log_dir, f"{timestamp}.log")
    
    # 创建一个logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 创建一个文件处理器 (FileHandler)，写入日志文件
    # 使用 'w' 模式确保每次运行都是一个全新的日志文件
    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    
    # 定义日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 将处理器添加到logger
    logger.addHandler(file_handler)
    
    print(Fore.YELLOW + f"--- 日志系统已启动，日志将记录到: {log_filename} ---")
    return logger

def load_config(filename='config.ini'):
    """读取配置文件并返回一个包含所有信息的字典。"""
    # ... 此函数内容不变 ...
    print(Fore.YELLOW + "--- 正在加载配置文件... ---")
    parser = configparser.ConfigParser()
    parser.read(filename)
    
    config = {
        'host': parser.get('device_info', 'host'),
        'port': parser.getint('device_info', 'port'), 
        'username': parser.get('device_info', 'username'),
        'password': parser.get('device_info', 'password'),
        'user_prompt': parser.get('device_prompts', 'user_prompt').encode('utf-8'),
        'system_prompt': parser.get('device_prompts', 'system_prompt').encode('utf-8'),
        'commands': parser.get('commands_to_run', 'commands').strip().split('\n')
    }
    print(Fore.GREEN + "--- 配置文件加载成功！ ---\n")
    return config

def execute_device_session(config, logger): # <-- 4. 接收logger作为参数
    """
    主执行函数：连接设备、进入系统模式并执行一系列命令。
    """
    ssh_session = None
    try:
        # 5. 将logger传递给VisualSSH
        ssh_session = VisualSSH(
            host=config['host'],
            port=config['port'], 
            username=config['username'],
            password=config['password'],
            logger=logger 
        )
        
        # ... 后续逻辑不变 ...
        ssh_session.read_until(config['user_prompt'])
        ssh_session.write(b"system-view")
        ssh_session.read_until(config['system_prompt'])

        for cmd in config['commands']:
            cmd_clean = cmd.strip()
            if not cmd_clean: continue
            
            cmd_bytes = cmd_clean.encode('utf-8')
            
            print("\n" + Fore.WHITE + Style.BRIGHT + f"======== 命令输出: {cmd_clean} ========")
            logger.info(f"======== 开始执行命令: {cmd_clean} ========")
            output = ssh_session.execute(cmd_bytes)
            print(output)
            logger.info(f"======== 命令执行完毕: {cmd_clean} ========")

    except Exception as e:
        print(Fore.RED + f"!!! 在执行会话时发生严重错误: {e}")
        logger.critical(f"!!! 在执行会话时发生严重错误: {e}", exc_info=True)
    finally:
        if ssh_session:
            ssh_session.close()

# Python程序的标准主入口
if __name__ == "__main__":
    # 6. 先初始化logger
    main_logger = setup_logger()
    
    # 7. 然后加载配置
    device_config = load_config()
    
    # 8. 最后执行任务，并传入logger
    execute_device_session(device_config, main_logger)