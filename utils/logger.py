"""
日志工具模块
"""
import os
import logging
from datetime import datetime
from typing import Optional

class Logger:
    """日志管理类"""
    
    _instance = None
    _loggers = {}  # 存储不同模块的logger
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self):
        """初始化日志管理器"""
        if not hasattr(self, 'initialized'):
            self._setup_base_config()
            self.initialized = True
            
    def _setup_base_config(self):
        """配置基本日志系统"""
        # 创建logs目录
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 生成日志文件名
        self.log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # 配置日志格式
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建文件处理器
        self.file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        self.file_handler.setFormatter(self.formatter)
        self.file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(self.formatter)
        self.console_handler.setLevel(logging.INFO)
            
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的logger
        
        Args:
            name: 模块名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(self.file_handler)
            logger.addHandler(self.console_handler)
            # 防止日志重复
            logger.propagate = False
            self._loggers[name] = logger
            
        return self._loggers[name]

# 创建全局日志管理器
_logger_manager = Logger()

def get_logger(name: str = None) -> logging.Logger:
    """获取logger的便捷函数
    
    Args:
        name: 模块名称，如果为None则使用调用者的模块名
        
    Returns:
        logging.Logger: 日志记录器
    """
    if name is None:
        import inspect
        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back
        if frame is not None:
            name = frame.f_globals.get('__name__', 'unknown')
    
    return _logger_manager.get_logger(name) 