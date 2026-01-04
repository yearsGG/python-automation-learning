import logging
import os
import sys

def setup_logger(name=__name__, log_file='automation.log', level=logging.INFO):
    """
    配置并返回一个标准的 logger 对象
    :param name: logger 名称，通常传 __name__
    :param log_file: 日志文件名
    :param level: 日志级别
    """
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler (防止日志重复打印)
    if not logger.handlers:
        # 1. 格式器
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
        )

        # 2. 文件处理器 (写入文件)
        # 确保日志文件存在于项目根目录或 logs 目录下
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # 3. 控制台处理器 (输出到屏幕 - 可选，因为你的 SSH 类自己有 print，这里可以只记录 error)
        # 如果你想让系统日志也显示在屏幕上，取消下面注释
        # console_handler = logging.StreamHandler(sys.stdout)
        # console_handler.setFormatter(formatter)
        # logger.addHandler(console_handler)

    return logger